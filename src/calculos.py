"""
Módulo de cálculos para relatórios de energia solar
Inclui: economia financeira, CO2, árvores, Performance Ratio, HSP
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def calcular_economia_financeira(kwh: float, tarifa_kwh: float = 0.887) -> Dict[str, float]:
    """
    Calcula economia financeira baseada na energia gerada
    
    Args:
        kwh: Energia gerada em kWh
        tarifa_kwh: Tarifa de energia em R$/kWh (padrão: R$ 0,887)
    
    Returns:
        Dict com economia mensal, anual e economia acumulada
    """
    economia_mensal = kwh * tarifa_kwh
    economia_anual = economia_mensal * 12
    
    return {
        'economia_mensal': round(economia_mensal, 2),
        'economia_anual': round(economia_anual, 2),
        'tarifa_utilizada': tarifa_kwh,
        'kwh_gerado': round(kwh, 2)
    }


def calcular_co2_evitado(kwh: float, fator_emissao: float = 0.0817) -> Dict[str, float]:
    """
    Calcula CO2 evitado baseado na energia limpa gerada
    
    Args:
        kwh: Energia gerada em kWh
        fator_emissao: Fator de emissão em tCO2/MWh (padrão: 0,0817 - média Brasil)
    
    Returns:
        Dict com CO2 evitado em kg, toneladas e equivalências
    """
    # Converte kWh para MWh e multiplica pelo fator
    co2_toneladas = (kwh / 1000) * fator_emissao
    co2_kg = co2_toneladas * 1000
    
    return {
        'co2_kg': round(co2_kg, 2),
        'co2_toneladas': round(co2_toneladas, 4),
        'fator_emissao': fator_emissao,
        'kwh_gerado': round(kwh, 2)
    }


def calcular_arvores_equivalentes(co2_kg: float, absorcao_arvore_ano: float = 163.0) -> Dict[str, float]:
    """
    Calcula equivalência em árvores plantadas
    
    Args:
        co2_kg: CO2 evitado em kg
        absorcao_arvore_ano: Absorção média de uma árvore por ano em kg CO2 (padrão: 163 kg)
    
    Returns:
        Dict com número de árvores equivalentes
    """
    # Uma árvore absorve cerca de 163 kg de CO2 por ano
    arvores = co2_kg / absorcao_arvore_ano
    
    return {
        'arvores_equivalentes': round(arvores, 1),
        'co2_kg': round(co2_kg, 2),
        'absorcao_por_arvore': absorcao_arvore_ano
    }


def calcular_performance_ratio(energia_real: float, energia_teorica: float) -> float:
    """
    Calcula o Performance Ratio (PR) do sistema fotovoltaico
    
    Args:
        energia_real: Energia realmente gerada em kWh
        energia_teorica: Energia teórica esperada em kWh
    
    Returns:
        Performance Ratio em percentual (0-100)
    """
    if energia_teorica <= 0:
        logger.warning("Energia teórica deve ser maior que zero")
        return 0.0
    
    pr = (energia_real / energia_teorica) * 100
    return round(pr, 2)


def calcular_horas_sol_pico(kwh_gerado: float, potencia_kwp: float) -> float:
    """
    Calcula as Horas de Sol Pico (HSP) médias do período
    
    Args:
        kwh_gerado: Energia total gerada no período em kWh
        potencia_kwp: Potência instalada do sistema em kWp
    
    Returns:
        Horas de Sol Pico médias
    """
    if potencia_kwp <= 0:
        logger.warning("Potência instalada deve ser maior que zero")
        return 0.0
    
    hsp = kwh_gerado / potencia_kwp
    return round(hsp, 2)


def calcular_disponibilidade(horas_operacao: float, horas_totais: float) -> float:
    """
    Calcula a disponibilidade do sistema
    
    Args:
        horas_operacao: Horas em que o sistema esteve operacional
        horas_totais: Total de horas do período
    
    Returns:
        Disponibilidade em percentual (0-100)
    """
    if horas_totais <= 0:
        logger.warning("Horas totais deve ser maior que zero")
        return 0.0
    
    disponibilidade = (horas_operacao / horas_totais) * 100
    return round(disponibilidade, 2)


def calcular_eficiencia_sistema(energia_real: float, irradiacao_total: float, 
                                area_modulos: float, eficiencia_modulo: float = 0.20) -> float:
    """
    Calcula a eficiência global do sistema
    
    Args:
        energia_real: Energia gerada em kWh
        irradiacao_total: Irradiação total recebida em kWh/m²
        area_modulos: Área total dos módulos em m²
        eficiencia_modulo: Eficiência nominal do módulo (padrão: 20%)
    
    Returns:
        Eficiência do sistema em percentual (0-100)
    """
    if irradiacao_total <= 0 or area_modulos <= 0:
        logger.warning("Irradiação e área devem ser maiores que zero")
        return 0.0
    
    energia_teorica = irradiacao_total * area_modulos * eficiencia_modulo
    if energia_teorica <= 0:
        return 0.0
    
    eficiencia = (energia_real / energia_teorica) * 100
    return round(eficiencia, 2)


def calcular_comparativo_mensal(mes_atual: float, mes_anterior: float) -> Dict[str, float]:
    """
    Calcula comparativo entre mês atual e anterior
    
    Args:
        mes_atual: Geração do mês atual em kWh
        mes_anterior: Geração do mês anterior em kWh
    
    Returns:
        Dict com variação absoluta e percentual
    """
    if mes_anterior <= 0:
        return {
            'variacao_kwh': round(mes_atual, 2),
            'variacao_percentual': 100.0 if mes_atual > 0 else 0.0,
            'mes_atual': round(mes_atual, 2),
            'mes_anterior': round(mes_anterior, 2)
        }
    
    variacao_kwh = mes_atual - mes_anterior
    variacao_percentual = (variacao_kwh / mes_anterior) * 100
    
    return {
        'variacao_kwh': round(variacao_kwh, 2),
        'variacao_percentual': round(variacao_percentual, 2),
        'mes_atual': round(mes_atual, 2),
        'mes_anterior': round(mes_anterior, 2)
    }


def calcular_payback_simples(custo_sistema: float, economia_mensal: float) -> Dict[str, float]:
    """
    Calcula o payback simples do investimento
    
    Args:
        custo_sistema: Custo total do sistema em R$
        economia_mensal: Economia média mensal em R$
    
    Returns:
        Dict com payback em meses e anos
    """
    if economia_mensal <= 0:
        logger.warning("Economia mensal deve ser maior que zero")
        return {
            'payback_meses': 0.0,
            'payback_anos': 0.0,
            'custo_sistema': round(custo_sistema, 2),
            'economia_mensal': round(economia_mensal, 2)
        }
    
    payback_meses = custo_sistema / economia_mensal
    payback_anos = payback_meses / 12
    
    return {
        'payback_meses': round(payback_meses, 1),
        'payback_anos': round(payback_anos, 2),
        'custo_sistema': round(custo_sistema, 2),
        'economia_mensal': round(economia_mensal, 2)
    }


def calcular_metricas_completas(dados: Dict) -> Dict:
    """
    Calcula todas as métricas de uma vez
    
    Args:
        dados: Dict contendo:
            - kwh_gerado: Energia gerada
            - potencia_kwp: Potência instalada
            - tarifa_kwh: Tarifa de energia (opcional)
            - energia_teorica: Energia teórica (opcional)
            - mes_anterior: Geração mês anterior (opcional)
    
    Returns:
        Dict com todas as métricas calculadas
    """
    kwh = dados.get('kwh_gerado', 0)
    kwp = dados.get('potencia_kwp', 0)
    tarifa = dados.get('tarifa_kwh', 0.887)
    
    metricas = {
        'economia': calcular_economia_financeira(kwh, tarifa),
        'co2': calcular_co2_evitado(kwh),
        'hsp': calcular_horas_sol_pico(kwh, kwp) if kwp > 0 else 0.0
    }
    
    # Adiciona árvores equivalentes
    co2_kg = metricas['co2']['co2_kg']
    metricas['arvores'] = calcular_arvores_equivalentes(co2_kg)
    
    # Performance Ratio se tiver energia teórica
    if dados.get('energia_teorica'):
        metricas['pr'] = calcular_performance_ratio(kwh, dados['energia_teorica'])
    
    # Comparativo se tiver mês anterior
    if dados.get('mes_anterior'):
        metricas['comparativo'] = calcular_comparativo_mensal(kwh, dados['mes_anterior'])
    
    return metricas
