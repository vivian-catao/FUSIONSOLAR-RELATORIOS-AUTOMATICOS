"""
Extrator de dados da API FusionSolar
Processa e estrutura dados para geração de relatórios
"""

import logging
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
    
    def extrair_dados_mensais(self, station_code: str, mes: int, ano: int,
                             potencia_kwp: Optional[float] = None) -> Dict[str, Any]:
        """
        Extrai dados completos de um mês para uma estação
        
        Args:
            station_code: Código da estação
            mes: Mês (1-12)
            ano: Ano
            potencia_kwp: Potência instalada em kWp (se não informada, tenta obter da API)
        
        Returns:
            Dicionário completo com todos os dados do mês
        """
        logger.info(f"Extraindo dados mensais de {station_code} para {mes}/{ano}")
        
        # Formata período
        collect_time = f"{ano}{mes:02d}"
        
        # Dados da estação
        estacao = self._obter_dados_estacao(station_code)
        
        # KPIs mensais
        kpi_mensal = self.api.get_station_month_kpi(station_code, collect_time)
        
        # Dados diários do mês
        dados_diarios = self._obter_dados_diarios_mes(station_code, mes, ano)
        
        # Alarmes do mês
        alarmes = self._obter_alarmes_mes(station_code, mes, ano)
        
        # Dispositivos
        dispositivos = self.api.get_device_list(station_code)
        
        # Usa potência informada ou tenta obter da estação
        if potencia_kwp is None:
            potencia_kwp = estacao.get('capacity', 0)
        
        # Processa dados
        dados_processados = self._processar_dados_mensais(
            estacao=estacao,
            kpi_mensal=kpi_mensal,
            dados_diarios=dados_diarios,
            alarmes=alarmes,
            dispositivos=dispositivos,
            potencia_kwp=potencia_kwp,
            mes=mes,
            ano=ano
        )
        
        logger.info(f"Dados extraídos com sucesso: {dados_processados['geracao']['total_kwh']:.2f} kWh")
        
        return dados_processados
    
    def _obter_dados_estacao(self, station_code: str) -> Dict:
        """Obtém dados básicos da estação"""
        estacoes = self.api.get_station_list()
        
        for estacao in estacoes:
            if estacao.get('stationCode') == station_code:
                return estacao
        
        logger.warning(f"Estação {station_code} não encontrada na lista")
        return {'stationCode': station_code}
    
    def _obter_dados_diarios_mes(self, station_code: str, mes: int, ano: int) -> List[Dict]:
        """Obtém dados diários de todos os dias do mês"""
        dias_no_mes = monthrange(ano, mes)[1]
        dados_diarios = []
        
        for dia in range(1, dias_no_mes + 1):
            collect_time = f"{ano}{mes:02d}{dia:02d}"
            
            try:
                kpi_dia = self.api.get_station_day_kpi(station_code, collect_time)
                if kpi_dia:
                    kpi_dia['dia'] = dia
                    dados_diarios.append(kpi_dia)
            except Exception as e:
                logger.warning(f"Erro ao obter dados do dia {dia}/{mes}/{ano}: {e}")
        
        return dados_diarios
    
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
    
    def _processar_dados_mensais(self, estacao: Dict, kpi_mensal: Dict, 
                                dados_diarios: List[Dict], alarmes: List[Dict],
                                dispositivos: List[Dict], potencia_kwp: float,
                                mes: int, ano: int) -> Dict[str, Any]:
        """Processa e estrutura todos os dados coletados"""
        
        # Extrai KPIs mensais
        total_kwh = kpi_mensal.get('dataItemMap', {}).get('production_power', 0)
        if isinstance(total_kwh, str):
            total_kwh = float(total_kwh)
        
        # Processa dados diários
        geracao_diaria = []
        for dia_data in dados_diarios:
            dia = dia_data.get('dia', 0)
            kwh = dia_data.get('dataItemMap', {}).get('production_power', 0)
            if isinstance(kwh, str):
                kwh = float(kwh)
            
            geracao_diaria.append({
                'dia': dia,
                'kwh': kwh,
                'data': datetime(ano, mes, dia)
            })
        
        # Calcula estatísticas
        geracoes = [d['kwh'] for d in geracao_diaria if d['kwh'] > 0]
        media_diaria = sum(geracoes) / len(geracoes) if geracoes else 0
        max_diario = max(geracoes) if geracoes else 0
        min_diario = min(geracoes) if geracoes else 0
        
        # Conta dias com geração
        dias_com_geracao = len([g for g in geracoes if g > 0])
        dias_sem_geracao = len(geracao_diaria) - dias_com_geracao
        
        # Performance Ratio (estimativa)
        # HSP médio para cálculo (ajustar conforme região)
        hsp_medio = 4.5
        energia_teorica = potencia_kwp * hsp_medio * len(geracao_diaria)
        pr = (total_kwh / energia_teorica * 100) if energia_teorica > 0 else 0
        
        # Calcula métricas
        metricas = calcular_metricas_completas({
            'kwh_gerado': total_kwh,
            'potencia_kwp': potencia_kwp,
            'energia_teorica': energia_teorica
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
                'dias_no_mes': len(geracao_diaria)
            },
            'geracao': {
                'total_kwh': round(total_kwh, 2),
                'media_diaria': round(media_diaria, 2),
                'max_diario': round(max_diario, 2),
                'min_diario': round(min_diario, 2),
                'dias_com_geracao': dias_com_geracao,
                'dias_sem_geracao': dias_sem_geracao,
                'geracao_diaria': geracao_diaria
            },
            'performance': {
                'pr': round(pr, 2),
                'energia_teorica': round(energia_teorica, 2),
                'hsp_medio': round(total_kwh / potencia_kwp, 2) if potencia_kwp > 0 else 0,
                'disponibilidade': round((dias_com_geracao / len(geracao_diaria) * 100), 2)
            },
            'economia': metricas['economia'],
            'impacto_ambiental': {
                'co2_evitado_kg': metricas['co2']['co2_kg'],
                'co2_evitado_ton': metricas['co2']['co2_toneladas'],
                'arvores_equivalentes': metricas['arvores']['arvores_equivalentes']
            },
            'sistema': {
                'num_inversores': len(inversores),
                'inversores': [
                    {
                        'nome': inv.get('devName'),
                        'modelo': inv.get('devTypeId'),
                        'sn': inv.get('esnCode')
                    }
                    for inv in inversores[:5]  # Limita a 5 para não poluir
                ],
                'alarmes': alarmes_processados
            },
            'dados_brutos': {
                'kpi_mensal': kpi_mensal,
                'estacao_completa': estacao
            }
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
                                 potencia_kwp: Optional[float] = None) -> Dict[str, Any]:
        """
        Extrai dados do mês atual e compara com mês anterior
        
        Args:
            station_code: Código da estação
            mes: Mês atual
            ano: Ano atual
            potencia_kwp: Potência instalada
        
        Returns:
            Dict com dados do mês atual e comparativo
        """
        # Dados do mês atual
        dados_atual = self.extrair_dados_mensais(station_code, mes, ano, potencia_kwp)
        
        # Dados do mês anterior
        mes_ant, ano_ant = obter_mes_anterior(mes, ano)
        
        try:
            dados_anterior = self.extrair_dados_mensais(station_code, mes_ant, ano_ant, potencia_kwp)
            
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
            
        except Exception as e:
            logger.warning(f"Não foi possível comparar com mês anterior: {e}")
            dados_atual['comparativo'] = None
        
        return dados_atual
