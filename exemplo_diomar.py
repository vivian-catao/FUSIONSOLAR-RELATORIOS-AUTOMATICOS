#!/usr/bin/env python3
"""
Exemplo de geração de relatório para o cliente DIOMAR DE OLIVEIRA
Baseado nos dados: 8.4 kWp, novembro/2025, 1.286,98 kWh, R$ 1.141,55 economia
Demonstra todas as funcionalidades do sistema com dados reais
"""

import sys
import os
from datetime import datetime

# Adiciona diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gerador_relatorio import GeradorRelatorio
from src.calculos import calcular_metricas_completas
from src.utils import (
    configurar_logging,
    formatar_moeda,
    formatar_numero,
    formatar_mes_ano,
    obter_data_hora_atual_brasil,
    obter_timezone_brasil
)
import pytz


def criar_dados_exemplo_diomar():
    """
    Cria dados de exemplo baseados no cliente DIOMAR DE OLIVEIRA
    Novembro/2025: 1.286,98 kWh gerados, R$ 1.141,55 de economia
    Sistema: 8.4 kWp, Tarifa: R$ 0.887/kWh
    """
    
    # Configuração do cliente
    potencia_kwp = 8.4
    tarifa_kwh = 0.887
    mes = 11
    ano = 2025
    total_kwh = 1286.98
    
    # Dados de geração diária simulados (novembro tem 30 dias)
    # Distribuição realista com alguns dias de chuva/baixa geração
    geracao_diaria = [
        {'dia': 1, 'kwh': 48.5},
        {'dia': 2, 'kwh': 52.3},
        {'dia': 3, 'kwh': 45.1},
        {'dia': 4, 'kwh': 51.2},
        {'dia': 5, 'kwh': 38.7},  # Dia nublado
        {'dia': 6, 'kwh': 49.8},
        {'dia': 7, 'kwh': 53.4},
        {'dia': 8, 'kwh': 47.2},
        {'dia': 9, 'kwh': 50.9},
        {'dia': 10, 'kwh': 44.3},
        {'dia': 11, 'kwh': 35.2},  # Chuva
        {'dia': 12, 'kwh': 41.6},
        {'dia': 13, 'kwh': 48.7},
        {'dia': 14, 'kwh': 52.1},
        {'dia': 15, 'kwh': 46.9},
        {'dia': 16, 'kwh': 49.3},
        {'dia': 17, 'kwh': 51.8},
        {'dia': 18, 'kwh': 43.5},
        {'dia': 19, 'kwh': 47.8},
        {'dia': 20, 'kwh': 50.2},
        {'dia': 21, 'kwh': 45.6},
        {'dia': 22, 'kwh': 48.9},
        {'dia': 23, 'kwh': 52.7},
        {'dia': 24, 'kwh': 44.8},
        {'dia': 25, 'kwh': 39.4},  # Nublado
        {'dia': 26, 'kwh': 46.5},
        {'dia': 27, 'kwh': 49.1},
        {'dia': 28, 'kwh': 51.3},
        {'dia': 29, 'kwh': 47.6},
        {'dia': 30, 'kwh': 50.4},
    ]
    
    # Calcula métricas
    metricas = calcular_metricas_completas({
        'kwh_gerado': total_kwh,
        'potencia_kwp': potencia_kwp,
        'tarifa_kwh': tarifa_kwh,
        'energia_teorica': total_kwh / 0.78,  # PR esperado de 78%
        'mes_anterior': 1150.50  # Outubro teve menos geração
    })
    
    # Timezone Brasil
    tz_brasil = obter_timezone_brasil()
    data_geracao = obter_data_hora_atual_brasil()
    
    # Estrutura completa de dados
    dados = {
        'estacao': {
            'nome': 'DIOMAR DE OLIVEIRA',
            'codigo': 'DIOMAR001',
            'potencia_kwp': potencia_kwp,
            'endereco': 'Rua Exemplo, 123 - Centro - Cidade/UF',
            'latitude': -23.5505,
            'longitude': -46.6333
        },
        
        'periodo': {
            'mes': mes,
            'ano': ano,
            'mes_ano_texto': formatar_mes_ano(mes, ano),
            'dias_no_mes': 30,
            'data_geracao': data_geracao.strftime('%d/%m/%Y %H:%M'),
            'timezone': 'America/Sao_Paulo'
        },
        
        'geracao': {
            'total_kwh': total_kwh,
            'media_diaria': total_kwh / 30,
            'max_diario': max([d['kwh'] for d in geracao_diaria]),
            'min_diario': min([d['kwh'] for d in geracao_diaria]),
            'dias_com_geracao': len([d for d in geracao_diaria if d['kwh'] > 0]),
            'geracao_diaria': geracao_diaria
        },
        
        'economia': {
            'economia_mensal': metricas['economia']['economia_mensal'],
            'economia_anual': metricas['economia']['economia_anual'],
            'tarifa_utilizada': tarifa_kwh,
            'kwh_gerado': total_kwh
        },
        
        'impacto_ambiental': {
            'co2_evitado_kg': metricas['co2']['co2_kg'],
            'co2_evitado_ton': metricas['co2']['co2_toneladas'],
            'arvores_equivalentes': metricas['arvores']['arvores_equivalentes'],
            'fator_emissao': metricas['co2']['fator_emissao']
        },
        
        'performance': {
            'pr': metricas['pr'],
            'hsp_medio': metricas['hsp'],
            'energia_teorica': total_kwh / 0.78,
            'disponibilidade': 98.5,  # 98.5% de disponibilidade
            'eficiencia_sistema': 18.2
        },
        
        'comparativo': {
            'mes_anterior': 'Outubro de 2025',
            'kwh_mes_anterior': metricas['comparativo']['mes_anterior'],
            'variacao_kwh': metricas['comparativo']['variacao_kwh'],
            'variacao_percentual': metricas['comparativo']['variacao_percentual']
        },
        
        'sistema': {
            'num_inversores': 1,
            'tipo_inversor': 'Huawei SUN2000-8KTL-M1',
            'num_paineis': 21,
            'potencia_painel': 400,  # W
            'marca_painel': 'Canadian Solar',
            'alarmes': {
                'total': 0,
                'criticos': 0,
                'avisos': 0,
                'lista': []
            }
        },
        
        'cliente': {
            'nome': 'DIOMAR DE OLIVEIRA',
            'email': 'diomar@exemplo.com',
            'telefone': '(11) 98765-4321',
            'contato': 'Diomar'
        }
    }
    
    return dados


def main():
    """Função principal do exemplo"""
    
    # Configura logging
    configurar_logging('INFO')
    
    import logging
    logger = logging.getLogger(__name__)
    
    print("=" * 80)
    print("EXEMPLO DE RELATÓRIO - CLIENTE DIOMAR DE OLIVEIRA")
    print("=" * 80)
    print()
    print("📊 Dados do Sistema:")
    print(f"   • Cliente: DIOMAR DE OLIVEIRA")
    print(f"   • Potência Instalada: 8,4 kWp")
    print(f"   • Período: Novembro/2025")
    print(f"   • Geração: 1.286,98 kWh")
    print(f"   • Economia: R$ 1.141,55")
    print(f"   • Tarifa: R$ 0,887/kWh")
    print()
    
    # Configuração do gerador
    config = {
        'fusionsolar': {
            'username': 'usuario@exemplo.com',
            'password': 'senha123',
            'base_url': 'https://intl.fusionsolar.huawei.com'
        },
        'relatorio': {
            'nome_empresa': 'Solar Energy Solutions',
            'telefone': '(11) 3456-7890',
            'email': 'contato@solarenergy.com.br',
            'website': 'www.solarenergy.com.br',
            'cor_primaria': '#FF6B00',
            'cor_secundaria': '#2C3E50'
        }
    }
    
    # Cria diretórios
    os.makedirs('output/relatorios', exist_ok=True)
    os.makedirs('output/dados', exist_ok=True)
    
    try:
        # Cria dados do exemplo
        logger.info("Gerando dados de exemplo...")
        dados = criar_dados_exemplo_diomar()
        
        # Salva JSON para análise
        from src.utils import salvar_json
        json_path = 'output/dados/exemplo_diomar_novembro_2025.json'
        salvar_json(dados, json_path)
        print(f"📄 Dados salvos em: {json_path}")
        
        # Gera relatório
        logger.info("Gerando relatório PDF...")
        gerador = GeradorRelatorio(config)
        pdf_path = 'output/relatorios/exemplo_diomar_novembro_2025.pdf'
        gerador.gerar_relatorio(dados, pdf_path)
        
        print()
        print("=" * 80)
        print("✅ RELATÓRIO GERADO COM SUCESSO!")
        print("=" * 80)
        print()
        print(f"📍 Localização do PDF: {pdf_path}")
        print(f"📍 Dados JSON: {json_path}")
        print()
        print("📊 Resumo do Relatório:")
        print(f"   • Energia Total: {formatar_numero(dados['geracao']['total_kwh'], 2)} kWh")
        print(f"   • Economia Mensal: {formatar_moeda(dados['economia']['economia_mensal'])}")
        print(f"   • CO₂ Evitado: {formatar_numero(dados['impacto_ambiental']['co2_evitado_kg'], 0)} kg")
        print(f"   • Árvores Equivalentes: {formatar_numero(dados['impacto_ambiental']['arvores_equivalentes'], 0)}")
        print(f"   • Performance Ratio: {dados['performance']['pr']:.1f}%")
        print(f"   • Disponibilidade: {dados['performance']['disponibilidade']:.1f}%")
        print()
        print("🌟 Características do Relatório:")
        print("   ✓ Design profissional com gradientes")
        print("   ✓ Resumo executivo com KPIs destacados")
        print("   ✓ Gráfico de barras (geração diária)")
        print("   ✓ Cards de métricas principais")
        print("   ✓ Análise de performance")
        print("   ✓ Impacto ambiental (CO₂, árvores)")
        print("   ✓ Status do sistema e alarmes")
        print("   ✓ Formatação brasileira (R$, dd/mm/yyyy)")
        print("   ✓ Timezone: America/Sao_Paulo")
        print()
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar relatório: {e}", exc_info=True)
        print()
        print(f"❌ Erro: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
