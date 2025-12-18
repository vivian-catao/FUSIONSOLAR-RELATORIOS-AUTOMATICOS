"""
Extrator de dados da API FusionSolar
Processa e estrutura dados para geração de relatórios
"""

import logging
import time
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from calendar import monthrange

from .fusionsolar_api import FusionSolarAPI
from .calculos import calcular_metricas_completas
from .utils import (
    calcular_primeiro_ultimo_dia_mes,
    obter_timestamp_ms,
    obter_mes_anterior,
    formatar_mes_ano
)

# Rate limit da API FusionSolar: 5 chamadas a cada 10 minutos
RATE_LIMIT_CALLS = 5
RATE_LIMIT_WINDOW_SECONDS = 10 * 60  # 10 minutos

logger = logging.getLogger(__name__)


class ExtratorDados:
    """Extrai e processa dados da API FusionSolar"""
    
    def __init__(self, api: FusionSolarAPI):
        """
        Inicializa o extrator
        
        Args:
            api: Instância configurada do cliente FusionSolarAPI
        """
        self.api = api
        self._cache_estacoes = None  # Cache para evitar chamadas repetidas
    
    def extrair_dados_mensais(self, station_code: str, mes: int, ano: int,
                             potencia_kwp: Optional[float] = None,
                             buscar_diarios: bool = False) -> Dict[str, Any]:
        """
        Extrai dados completos de um mês para uma estação
        
        Args:
            station_code: Código da estação
            mes: Mês (1-12)
            ano: Ano
            potencia_kwp: Potência instalada em kWp (se não informada, tenta obter da API)
            buscar_diarios: Se True, busca KPI de cada dia (CUIDADO: rate limit!)
        
        Returns:
            Dicionário completo com todos os dados do mês
        """
        logger.info(f"Extraindo dados mensais de {station_code} para {mes}/{ano}")
        
        # Formata período
        collect_time = f"{ano}{mes:02d}"
        
        # Dados da estação (usa cache)
        estacao = self._obter_dados_estacao(station_code)
        
        # Tenta obter KPIs mensais históricos
        kpi_mensal = self.api.get_station_month_kpi(station_code, collect_time)
        
        # Se KPI mensal está vazio, usa dados em tempo real como fallback
        if not kpi_mensal or not kpi_mensal.get('dataItemMap'):
            logger.info("KPI mensal vazio, usando dados em tempo real como fallback...")
            dados_realtime = self.api.get_station_realtime_data(station_code)
            if dados_realtime and dados_realtime.get('dataItemMap'):
                # Adapta dados realtime para formato esperado pelo processador
                kpi_mensal = {
                    'stationCode': station_code,
                    'dataItemMap': {
                        'production_power': dados_realtime.get('dataItemMap', {}).get('month_power', 0),
                        'total_power': dados_realtime.get('dataItemMap', {}).get('total_power', 0),
                        'day_power': dados_realtime.get('dataItemMap', {}).get('day_power', 0),
                        'total_income': dados_realtime.get('dataItemMap', {}).get('total_income', 0),
                    },
                    '_source': 'realtime'  # Marca origem dos dados
                }
                logger.info(f"Dados realtime obtidos: {kpi_mensal['dataItemMap'].get('production_power', 0)} kWh no mês")
            else:
                # Se nem realtime funciona (rate limit), usa valores zerados
                logger.warning("Dados realtime também indisponíveis (rate limit?). Usando valores padrão.")
                kpi_mensal = {
                    'stationCode': station_code,
                    'dataItemMap': {
                        'production_power': 0,
                        'total_power': 0,
                        'day_power': 0,
                        'total_income': 0,
                    },
                    '_source': 'fallback_empty'
                }
        
        # Dados diários do mês (desativado por padrão devido ao rate limit)
        dados_diarios = self._obter_dados_diarios_mes(station_code, mes, ano, buscar_diarios)
        
        # Alarmes do mês (pode dar erro 20045 se estação não existe)
        alarmes = self._obter_alarmes_mes(station_code, mes, ano)
        
        # Dispositivos e seus KPIs em tempo real
        dispositivos = self.api.get_device_list(station_code)
        inversores_kpi = self._obter_kpis_inversores(dispositivos)
        
        # Usa potência informada ou tenta obter da estação
        if potencia_kwp is None:
            # A API retorna potência em MW, converter para kWp (x1000)
            capacidade_mw = estacao.get('capacity', 0)
            potencia_kwp = capacidade_mw * 1000 if capacidade_mw and capacidade_mw < 100 else capacidade_mw
        
        # Processa dados
        dados_processados = self._processar_dados_mensais(
            estacao=estacao,
            kpi_mensal=kpi_mensal,
            dados_diarios=dados_diarios,
            alarmes=alarmes,
            dispositivos=dispositivos,
            inversores_kpi=inversores_kpi,
            potencia_kwp=potencia_kwp,
            mes=mes,
            ano=ano
        )
        
        logger.info(f"Dados extraídos com sucesso: {dados_processados['geracao']['total_kwh']:.2f} kWh")
        
        return dados_processados
    
    def _obter_dados_estacao(self, station_code: str) -> Dict:
        """Obtém dados básicos da estação (com cache para evitar múltiplas chamadas)"""
        # Usa cache se disponível
        if self._cache_estacoes is None:
            self._cache_estacoes = self.api.get_station_list()
        
        for estacao in self._cache_estacoes:
            if estacao.get('stationCode') == station_code:
                return estacao
        
        logger.warning(f"Estação {station_code} não encontrada na lista")
        return {'stationCode': station_code}
    
    def limpar_cache(self):
        """Limpa o cache de estações (útil para forçar nova busca)"""
        self._cache_estacoes = None
    
    def _rate_limit_wait(self, call_count: int, start_time: float, total_calls: int):
        """
        Implementa rate limiting respeitando 5 chamadas a cada 10 minutos.
        Mostra progresso ao usuário.
        """
        # A cada 5 chamadas, espera 10 minutos
        if call_count > 0 and call_count % RATE_LIMIT_CALLS == 0:
            elapsed = time.time() - start_time
            wait_time = RATE_LIMIT_WINDOW_SECONDS - (elapsed % RATE_LIMIT_WINDOW_SECONDS)
            
            if wait_time > 0 and wait_time < RATE_LIMIT_WINDOW_SECONDS:
                print(f"\n⏳ Rate limit atingido ({call_count}/{total_calls} chamadas)")
                print(f"   Aguardando {wait_time/60:.1f} minutos para continuar...")
                
                # Mostra countdown
                remaining = int(wait_time)
                while remaining > 0:
                    mins, secs = divmod(remaining, 60)
                    sys.stdout.write(f"\r   Tempo restante: {mins:02d}:{secs:02d}  ")
                    sys.stdout.flush()
                    time.sleep(1)
                    remaining -= 1
                
                print("\n   ✅ Continuando busca de dados...")
    
    def _obter_dados_diarios_mes(self, station_code: str, mes: int, ano: int, 
                                   buscar_diarios: bool = False) -> List[Dict]:
        """
        Obtém dados diários de todos os dias do mês em UMA ÚNICA CHAMADA.
        
        Usa o endpoint getKpiStationDay com timestamp em milissegundos do 
        primeiro dia do mês, que retorna todos os dias de uma vez.
        
        Args:
            station_code: Código da estação
            mes: Mês (1-12)
            ano: Ano
            buscar_diarios: Se True, busca dados diários (1 chamada apenas!)
            
        Returns:
            Lista de dicionários com dados de cada dia
        """
        if not buscar_diarios:
            logger.info(f"Busca de dados diários desativada")
            return []
        
        print(f"\n📊 Buscando dados diários de {mes:02d}/{ano}")
        print(f"   Método: Uma única chamada à API (eficiente)")
        
        try:
            # Usa o novo método que retorna todos os dias do mês de uma vez
            dados_api = self.api.get_station_month_daily_kpi(station_code, ano, mes)
            
            if not dados_api:
                print("   ⚠️  Nenhum dado retornado")
                return []
            
            # Processa os dados retornados
            dados_diarios = []
            for item in dados_api:
                timestamp_ms = item.get('collectTime', 0)
                if timestamp_ms:
                    dt = datetime.fromtimestamp(timestamp_ms / 1000)
                    dia = dt.day
                else:
                    continue
                
                data_map = item.get('dataItemMap', {})
                
                # Extrai energia do dia (tenta vários campos possíveis)
                energia = (
                    data_map.get('inverter_power') or 
                    data_map.get('inverterYield') or 
                    data_map.get('PVYield') or 
                    0
                )
                
                dados_diarios.append({
                    'dia': dia,
                    'data': dt.strftime('%Y-%m-%d'),
                    'dataItemMap': {
                        'inverter_power': energia,
                        'production_power': energia,  # Alias
                        'perpower_ratio': data_map.get('perpower_ratio', 0),  # kWh/kWp
                        'power_profit': data_map.get('power_profit', 0),  # Economia
                        'reduction_total_co2': data_map.get('reduction_total_co2', 0),
                        'installed_capacity': data_map.get('installed_capacity', 0),
                    }
                })
            
            # Ordena por dia
            dados_diarios.sort(key=lambda x: x['dia'])
            
            print(f"   ✅ {len(dados_diarios)} dias de dados obtidos!")
            
            # Mostra resumo
            total = sum(d['dataItemMap']['inverter_power'] for d in dados_diarios)
            print(f"   📈 Geração total: {total:.2f} kWh")
            
            return dados_diarios
            
        except Exception as e:
            logger.error(f"Erro ao obter dados diários: {e}")
            print(f"   ❌ Erro: {e}")
            return []
    
    def _obter_alarmes_mes(self, station_code: str, mes: int, ano: int) -> List[Dict]:
        """Obtém alarmes do mês"""
        primeiro_dia, ultimo_dia = calcular_primeiro_ultimo_dia_mes(mes, ano)
        
        begin_time = obter_timestamp_ms(primeiro_dia)
        end_time = obter_timestamp_ms(ultimo_dia)
        
        try:
            alarmes = self.api.get_alarm_list(station_code, begin_time, end_time)
            return alarmes
        except Exception as e:
            logger.warning(f"Erro ao obter alarmes: {e}")
            return []
    
    def _obter_kpis_inversores(self, dispositivos: List[Dict]) -> List[Dict]:
        """
        Obtém KPIs em tempo real de todos os inversores
        
        Args:
            dispositivos: Lista de dispositivos da estação
            
        Returns:
            Lista de dicionários com dados detalhados de cada inversor
        """
        inversores_kpi = []

        def _to_float(v, default=0.0):
            try:
                if v is None:
                    return float(default)
                return float(v)
            except Exception:
                return float(default)
        
        # Filtra apenas inversores (devTypeId: 1=String, 38=Residencial)
        tipos_inversor = [1, 38]
        inversores = [d for d in dispositivos if d.get('devTypeId') in tipos_inversor]
        
        for inv in inversores:
            dev_id = str(inv.get('id', ''))
            dev_type = inv.get('devTypeId', 1)
            
            if not dev_id:
                continue
                
            try:
                kpi = self.api.get_device_realtime_kpi(dev_id, dev_type)
                data_items = kpi.get('dataItemMap', {}) if isinstance(kpi, dict) else {}

                energia_total = _to_float(data_items.get('total_cap', 0))
                energia_dia = _to_float(data_items.get('day_cap', 0))
                potencia_ativa = _to_float(data_items.get('active_power', 0))
                potencia_reativa = _to_float(data_items.get('reactive_power', 0))
                mppt_total = _to_float(data_items.get('mppt_total_cap', data_items.get('mppt_total_cap', 0)))
                mppt_1 = _to_float(data_items.get('mppt_1_cap', 0))
                mppt_2 = _to_float(data_items.get('mppt_2_cap', 0))
                mppt_3 = _to_float(data_items.get('mppt_3_cap', 0))
                mppt_4 = _to_float(data_items.get('mppt_4_cap', 0))
                temperatura = _to_float(data_items.get('temperature', 0))

                inversor_data = {
                    'id': dev_id,
                    'nome': inv.get('devName', 'N/A'),
                    'modelo': inv.get('softwareVersion', 'N/A'),
                    'sn': inv.get('esnCode', inv.get('invSn', 'N/A')),
                    'status': data_items.get('run_state', data_items.get('inverter_state')),
                    # Produção
                    'energia_total_kwh': energia_total,
                    'energia_dia_kwh': energia_dia,
                    # Potência atual
                    'potencia_ativa_kw': potencia_ativa,
                    'potencia_reativa_kvar': potencia_reativa,
                    # MPPT (Multiple Power Point Tracking)
                    'mppt_total_kwh': mppt_total,
                    'mppt_1_kwh': mppt_1,
                    'mppt_2_kwh': mppt_2,
                    'mppt_3_kwh': mppt_3,
                    'mppt_4_kwh': mppt_4,
                    # Tensão e corrente
                    'tensao_rede_v': _to_float(data_items.get('a_u', data_items.get('ab_u', 0))),
                    'corrente_a': _to_float(data_items.get('a_i', 0)),
                    'frequencia_hz': _to_float(data_items.get('elec_freq', 0)),
                    # Strings PV
                    'pv1_tensao': _to_float(data_items.get('pv1_u', 0)),
                    'pv1_corrente': _to_float(data_items.get('pv1_i', 0)),
                    'pv2_tensao': _to_float(data_items.get('pv2_u', 0)),
                    'pv2_corrente': _to_float(data_items.get('pv2_i', 0)),
                    'pv3_tensao': _to_float(data_items.get('pv3_u', 0)),
                    'pv3_corrente': _to_float(data_items.get('pv3_i', 0)),
                    'pv4_tensao': _to_float(data_items.get('pv4_u', 0)),
                    'pv4_corrente': _to_float(data_items.get('pv4_i', 0)),
                    # Temperatura
                    'temperatura_c': temperatura,
                    # Eficiência
                    'eficiencia': _to_float(data_items.get('efficiency', 0)),
                    # Raw data para debug
                    '_raw': data_items
                }

                inversores_kpi.append(inversor_data)
                logger.info("  Inversor %s: %.2f kWh total, %.1f°C", inversor_data['nome'], inversor_data['energia_total_kwh'], inversor_data['temperatura_c'])

            except Exception as e:
                logger.warning(f"Erro ao obter KPI do inversor {inv.get('devName')}: {e}")
        
        return inversores_kpi
    
    def _processar_dados_mensais(self, estacao: Dict, kpi_mensal: Dict, 
                                dados_diarios: List[Dict], alarmes: List[Dict],
                                dispositivos: List[Dict], inversores_kpi: List[Dict],
                                potencia_kwp: float, mes: int, ano: int) -> Dict[str, Any]:
        """Processa e estrutura todos os dados coletados"""
        
        # Extrai KPIs mensais (valor de fallback)
        total_kwh_mensal = kpi_mensal.get('dataItemMap', {}).get('production_power', 0)
        if isinstance(total_kwh_mensal, str):
            total_kwh_mensal = float(total_kwh_mensal)
        
        # Processa dados diários
        geracao_diaria = []
        for dia_data in dados_diarios:
            dia = dia_data.get('dia', 0)
            # A API pode retornar em diferentes campos dependendo da versão
            data_items = dia_data.get('dataItemMap', {})
            kwh = data_items.get('inverter_power', data_items.get('production_power', 0))
            if isinstance(kwh, str):
                kwh = float(kwh) if kwh else 0
            
            geracao_diaria.append({
                'dia': dia,
                'kwh': kwh,
                'data': datetime(ano, mes, dia) if dia > 0 else None
            })
        
        # Calcula estatísticas APENAS se temos dados diários reais
        if geracao_diaria:
            geracoes = [d['kwh'] for d in geracao_diaria if d['kwh'] > 0]
            
            # SE temos dados diários, usa soma dos diários (mais preciso!)
            total_kwh_diarios = sum(geracoes)
            if total_kwh_diarios > 0:
                total_kwh = total_kwh_diarios
                logger.info(f"Usando total calculado dos dados diários: {total_kwh:.2f} kWh")
            else:
                total_kwh = total_kwh_mensal
            
            media_diaria = sum(geracoes) / len(geracoes) if geracoes else 0
            max_diario = max(geracoes) if geracoes else 0
            min_diario = min(geracoes) if geracoes else 0
            dias_com_geracao = len([g for g in geracoes if g > 0])
            dias_total = len(geracao_diaria)
            dias_sem_geracao = dias_total - dias_com_geracao
        else:
            # SEM dados diários - usa KPI mensal
            total_kwh = total_kwh_mensal
            media_diaria = None
            max_diario = None
            min_diario = None
            dias_com_geracao = None
            dias_total = monthrange(ano, mes)[1]
            dias_sem_geracao = None

        # HSP real (baseado APENAS em dados reais do mês)
        hsp_real = (total_kwh / potencia_kwp) if (potencia_kwp > 0 and total_kwh > 0) else None
        
        # NÃO calcular Performance Ratio sem dados diários
        # PR precisa de irradiação real ou dados completos do mês
        pr = None
        energia_teorica = None

        # Calcula métricas econômicas e ambientais (baseado em geração real)
        metricas = calcular_metricas_completas({
            'kwh_gerado': total_kwh,
            'potencia_kwp': potencia_kwp,
            'energia_teorica': 0  # Não temos dados para calcular
        })
        
        # Processa alarmes
        alarmes_processados = self._processar_alarmes(alarmes)
        
        # Informações dos dispositivos
        inversores = [d for d in dispositivos if d.get('devTypeId') == 1]
        
        # Monta estrutura final
        return {
            'estacao': {
                'codigo': estacao.get('stationCode'),
                'nome': estacao.get('stationName', 'N/A'),
                'endereco': estacao.get('stationAddr', 'N/A'),
                'potencia_kwp': potencia_kwp,
                'latitude': estacao.get('latitude'),
                'longitude': estacao.get('longitude'),
            },
            'periodo': {
                'mes': mes,
                'ano': ano,
                'mes_ano_texto': formatar_mes_ano(mes, ano),
                'dias_no_mes': dias_total
            },
            'geracao': {
                'total_kwh': round(total_kwh, 2) if total_kwh else 0,
                'media_diaria': round(media_diaria, 2) if media_diaria is not None else None,
                'max_diario': round(max_diario, 2) if max_diario is not None else None,
                'min_diario': round(min_diario, 2) if min_diario is not None else None,
                'dias_com_geracao': dias_com_geracao,
                'dias_sem_geracao': dias_sem_geracao,
                'geracao_diaria': geracao_diaria,
                'tem_dados_diarios': len(geracao_diaria) > 0  # Flag para template
            },
            'performance': {
                'pr': round(pr, 2) if pr is not None else None,
                'energia_teorica': round(energia_teorica, 2) if energia_teorica is not None else None,
                'hsp_medio': round(hsp_real, 2) if hsp_real is not None else None,
                'disponibilidade': round((dias_com_geracao / dias_total * 100), 2) if (dias_com_geracao is not None and dias_total > 0) else None
            },
            'economia': metricas['economia'],
            'impacto_ambiental': {
                'co2_evitado_kg': metricas['co2']['co2_kg'],
                'co2_evitado_ton': metricas['co2']['co2_toneladas'],
                'arvores_equivalentes': metricas['arvores']['arvores_equivalentes']
            },
            'sistema': {
                'num_inversores': len(inversores),
                'inversores': inversores_kpi if inversores_kpi else [
                    {
                        'nome': inv.get('devName'),
                        'modelo': inv.get('devTypeId'),
                        'sn': inv.get('esnCode')
                    }
                    for inv in inversores[:5]  # Fallback: Limita a 5 para não poluir
                ],
                'inversores_resumo': self._resumo_inversores(inversores_kpi),
                'alarmes': alarmes_processados
            },
            'dados_brutos': {
                'kpi_mensal': kpi_mensal,
                'estacao_completa': estacao,
                'inversores_kpi': inversores_kpi
            }
        }
    
    def _calcular_analises(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula análises e métricas extras para o relatório completo
        
        Args:
            dados: Dicionário com dados já processados
            
        Returns:
            Dicionário com análises calculadas
        """
        geracao = dados.get('geracao', {})
        estacao = dados.get('estacao', {})
        periodo = dados.get('periodo', {})
        sistema = dados.get('sistema', {})
        economia = dados.get('economia', {})
        
        total_kwh = geracao.get('total_kwh', 0)
        potencia_kwp = estacao.get('potencia_kwp', 1)
        mes = periodo.get('mes', 1)
        ano = periodo.get('ano', 2025)
        geracao_diaria = geracao.get('geracao_diaria', [])
        tarifa = economia.get('tarifa_utilizada', 0.68)
        
        analise = {
            'status_geral': 'SISTEMA OPERANDO COM EXCELENTE DESEMPENHO',
            'avaliacao_geracao': 'Excelente',
            'status_sistema': '100% OPERACIONAL'
        }
        
        # Energia específica (kWh/kWp)
        energia_especifica = (total_kwh / potencia_kwp) if potencia_kwp > 0 else 0
        analise['energia_especifica'] = round(energia_especifica, 2)
        
        # Avaliar energia específica
        if energia_especifica >= 150:
            analise['avaliacao_geracao'] = 'Excelente'
            analise['status_geral'] = 'SISTEMA OPERANDO COM EXCELENTE DESEMPENHO'
        elif energia_especifica >= 120:
            analise['avaliacao_geracao'] = 'Muito Bom'
            analise['status_geral'] = 'SISTEMA OPERANDO COM MUITO BOM DESEMPENHO'
        elif energia_especifica >= 100:
            analise['avaliacao_geracao'] = 'Bom'
            analise['status_geral'] = 'SISTEMA OPERANDO NORMALMENTE'
        elif energia_especifica >= 80:
            analise['avaliacao_geracao'] = 'Regular'
            analise['status_geral'] = 'SISTEMA OPERANDO COM DESEMPENHO REGULAR'
        else:
            analise['avaliacao_geracao'] = 'Abaixo do esperado'
            analise['status_geral'] = 'ATENÇÃO: DESEMPENHO ABAIXO DO ESPERADO'
        
        # Potência de pico (do inversor ou calculada)
        inversores_resumo = sistema.get('inversores_resumo', {})
        potencia_pico = inversores_resumo.get('potencia_ativa_total_kw', 0)
        
        # Se não temos potência atual, estimar baseado no máximo diário
        if potencia_pico == 0 and geracao.get('max_diario'):
            # Estimar potência pico: max_diario / horas_pico_estimadas (5h)
            potencia_pico = geracao['max_diario'] / 5
        
        analise['potencia_pico_kw'] = round(potencia_pico, 2) if potencia_pico > 0 else None
        analise['pico_percentual'] = round((potencia_pico / potencia_kwp) * 100, 1) if (potencia_kwp > 0 and potencia_pico > 0) else None
        
        # Rendimento acumulado (total da estação se disponível)
        total_power = dados.get('dados_brutos', {}).get('kpi_mensal', {}).get('dataItemMap', {}).get('total_power', 0)
        analise['rendimento_acumulado'] = round(float(total_power), 2) if total_power else None
        
        # Análise de dias (top 5, maior, menor)
        if geracao_diaria and len(geracao_diaria) > 0:
            # Ordenar por geração (maior primeiro)
            dias_ordenados = sorted(geracao_diaria, key=lambda x: x.get('kwh', 0), reverse=True)
            
            # Top 5 dias
            top5 = []
            for i, dia in enumerate(dias_ordenados[:5]):
                kwh = dia.get('kwh', 0)
                dia_num = dia.get('dia', i+1)
                top5.append({
                    'posicao': i + 1,
                    'data': f"{dia_num:02d}/{mes:02d}/{ano}",
                    'kwh': round(kwh, 2),
                    'receita': round(kwh * tarifa, 2)
                })
            analise['top5_dias'] = top5
            
            # Dia de maior e menor geração
            if dias_ordenados:
                maior = dias_ordenados[0]
                menor = dias_ordenados[-1]
                analise['dia_maior_geracao'] = {
                    'data': f"{maior.get('dia', 1):02d}/{mes:02d}",
                    'kwh': round(maior.get('kwh', 0), 2)
                }
                analise['dia_menor_geracao'] = {
                    'data': f"{menor.get('dia', 1):02d}/{mes:02d}",
                    'kwh': round(menor.get('kwh', 0), 2)
                }
        else:
            analise['top5_dias'] = []
            analise['dia_maior_geracao'] = None
            analise['dia_menor_geracao'] = None
        
        # Análise semanal
        analise['semanas'] = self._calcular_semanas(geracao_diaria, mes, ano, tarifa)
        
        # Identificar semana mais produtiva
        if analise['semanas']:
            melhor_semana = max(analise['semanas'], key=lambda x: x.get('geracao_kwh', 0))
            analise['semana_mais_produtiva'] = f"Semana {melhor_semana['numero']} ({melhor_semana['periodo']})"
            # Marcar a melhor semana
            for semana in analise['semanas']:
                semana['melhor'] = (semana['numero'] == melhor_semana['numero'])
        else:
            analise['semana_mais_produtiva'] = None
        
        return analise
    
    def _calcular_semanas(self, geracao_diaria: List[Dict], mes: int, ano: int, tarifa: float) -> List[Dict]:
        """Calcula análise semanal"""
        if not geracao_diaria or len(geracao_diaria) == 0:
            return []
        
        # Organizar dias em semanas
        from calendar import monthrange
        dias_no_mes = monthrange(ano, mes)[1]
        
        # Definir semanas (aproximadamente)
        semanas_def = [
            (1, 7),
            (8, 14),
            (15, 21),
            (22, 28),
            (29, dias_no_mes)  # Última semana pode ter menos dias
        ]
        
        semanas = []
        for i, (inicio, fim) in enumerate(semanas_def, 1):
            if inicio > dias_no_mes:
                break
            fim = min(fim, dias_no_mes)
            
            # Filtrar dias desta semana
            dias_semana = [d for d in geracao_diaria if inicio <= d.get('dia', 0) <= fim]
            
            if dias_semana:
                geracao_semana = sum(d.get('kwh', 0) for d in dias_semana)
                num_dias = len(dias_semana)
                media = geracao_semana / num_dias if num_dias > 0 else 0
                
                semanas.append({
                    'numero': i,
                    'periodo': f"{inicio:02d}-{fim:02d}/{mes:02d}",
                    'dias': num_dias,
                    'geracao_kwh': round(geracao_semana, 2),
                    'media_diaria': round(media, 2),
                    'receita': round(geracao_semana * tarifa, 2),
                    'destaque': self._avaliar_semana(media, geracao_semana),
                    'melhor': False  # Será atualizado depois
                })
        
        return semanas
    
    def _avaliar_semana(self, media_diaria: float, total: float) -> str:
        """Avalia desempenho da semana"""
        if media_diaria >= 45:
            return 'Excelente'
        elif media_diaria >= 40:
            return 'Muito bom'
        elif media_diaria >= 35:
            return 'Bom desempenho'
        elif media_diaria >= 30:
            return 'Regular'
        else:
            return 'Abaixo da média'

    def _resumo_inversores(self, inversores_kpi: List[Dict]) -> Dict[str, Any]:
        """Gera um resumo dos dados de todos os inversores"""
        if not inversores_kpi:
            return {}
        def _n(v):
            try:
                if v is None:
                    return 0.0
                return float(v)
            except Exception:
                return 0.0

        total_energia = sum(_n(inv.get('energia_total_kwh')) for inv in inversores_kpi)
        total_energia_dia = sum(_n(inv.get('energia_dia_kwh')) for inv in inversores_kpi)
        temps = [_n(inv.get('temperatura_c')) for inv in inversores_kpi if _n(inv.get('temperatura_c')) > 0]
        potencias = [_n(inv.get('potencia_ativa_kw')) for inv in inversores_kpi if _n(inv.get('potencia_ativa_kw')) > 0]
        
        return {
            'energia_total_kwh': round(total_energia, 2),
            'energia_dia_kwh': round(total_energia_dia, 2),
            'temperatura_media_c': round(sum(temps) / len(temps), 1) if temps else 0,
            'temperatura_max_c': max(temps) if temps else 0,
            'potencia_ativa_total_kw': round(sum(potencias), 2) if potencias else 0,
            'num_inversores_online': len([inv for inv in inversores_kpi if inv.get('status') == 1]),
            'num_inversores_total': len(inversores_kpi)
        }
    
    def _processar_alarmes(self, alarmes: List[Dict]) -> Dict[str, Any]:
        """Processa lista de alarmes"""
        if not alarmes:
            return {
                'total': 0,
                'criticos': 0,
                'avisos': 0,
                'lista': []
            }
        
        # Classifica alarmes por severidade
        criticos = []
        avisos = []
        
        for alarme in alarmes:
            severidade = alarme.get('alarmLevel', 0)
            
            alarme_processado = {
                'nome': alarme.get('alarmName', 'N/A'),
                'descricao': alarme.get('alarmCause', 'N/A'),
                'data': alarme.get('raiseTime'),
                'severidade': 'Crítico' if severidade >= 3 else 'Aviso'
            }
            
            if severidade >= 3:
                criticos.append(alarme_processado)
            else:
                avisos.append(alarme_processado)
        
        return {
            'total': len(alarmes),
            'criticos': len(criticos),
            'avisos': len(avisos),
            'lista': (criticos + avisos)[:10]  # Primeiros 10 alarmes
        }
    
    def extrair_dados_multiplos_clientes(self, clientes: List[Dict], 
                                        mes: int, ano: int) -> Dict[str, Dict]:
        """
        Extrai dados de múltiplos clientes
        
        Args:
            clientes: Lista de dicts com station_code, nome, potencia_kwp
            mes: Mês
            ano: Ano
        
        Returns:
            Dict com dados de cada cliente (chave = station_code)
        """
        logger.info(f"Extraindo dados de {len(clientes)} clientes para {mes}/{ano}")
        
        resultados = {}
        
        for i, cliente in enumerate(clientes, 1):
            station_code = cliente.get('station_code')
            nome = cliente.get('nome', station_code)
            potencia = cliente.get('potencia_kwp')
            
            logger.info(f"[{i}/{len(clientes)}] Processando {nome}...")
            
            try:
                dados = self.extrair_dados_mensais(station_code, mes, ano, potencia)
                dados['cliente'] = {
                    'nome': nome,
                    'email': cliente.get('email'),
                    'telefone': cliente.get('telefone')
                }
                resultados[station_code] = dados
                
            except Exception as e:
                logger.error(f"Erro ao processar {nome}: {e}")
                resultados[station_code] = {'erro': str(e)}
        
        logger.info(f"Extração concluída: {len(resultados)} clientes processados")
        
        return resultados
    
    def comparar_com_mes_anterior(self, station_code: str, mes: int, ano: int,
                                 potencia_kwp: Optional[float] = None,
                                 buscar_diarios: bool = False) -> Dict[str, Any]:
        """
        Extrai dados do mês atual e compara com mês anterior
        
        Args:
            station_code: Código da estação
            mes: Mês atual
            ano: Ano atual
            potencia_kwp: Potência instalada
            buscar_diarios: Se True, busca dados de cada dia
        
        Returns:
            Dict com dados do mês atual e comparativo
        """
        # Dados do mês atual
        dados_atual = self.extrair_dados_mensais(station_code, mes, ano, potencia_kwp, buscar_diarios)
        
        # Dados do mês anterior (também busca diários para ter o total correto)
        mes_ant, ano_ant = obter_mes_anterior(mes, ano)
        
        try:
            # Busca dados diários do mês anterior para obter total correto
            dados_anterior = self.extrair_dados_mensais(station_code, mes_ant, ano_ant, potencia_kwp, buscar_diarios=True)
            
            kwh_atual = dados_atual['geracao']['total_kwh']
            kwh_anterior = dados_anterior['geracao']['total_kwh']
            
            variacao_kwh = kwh_atual - kwh_anterior
            variacao_pct = (variacao_kwh / kwh_anterior * 100) if kwh_anterior > 0 else 0
            
            dados_atual['comparativo'] = {
                'mes_anterior': formatar_mes_ano(mes_ant, ano_ant),
                'kwh_mes_anterior': round(kwh_anterior, 2),
                'variacao_kwh': round(variacao_kwh, 2),
                'variacao_percentual': round(variacao_pct, 2)
            }
            
            logger.info(f"Comparativo: {mes_ant:02d}/{ano_ant} = {kwh_anterior:.2f} kWh")
            
        except Exception as e:
            logger.warning(f"Não foi possível comparar com mês anterior: {e}")
            dados_atual['comparativo'] = None
        
        # Calcular análises extras para o relatório completo
        dados_atual['analise'] = self._calcular_analises(dados_atual)
        
        return dados_atual
