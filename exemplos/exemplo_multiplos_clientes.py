"""
Exemplo de processamento de múltiplos clientes
Gera relatórios para vários clientes de uma vez
"""

import sys
import os

# Adiciona diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.fusionsolar_api import FusionSolarAPI
from src.extrator_dados import ExtratorDados
from src.gerador_relatorio import GeradorRelatorio
from src.utils import (
    configurar_logging,
    criar_diretorios,
    gerar_nome_arquivo,
    salvar_json
)

# Configuração
configurar_logging('INFO', 'logs/multiplos_clientes.log')
criar_diretorios(['output/relatorios', 'output/dados', 'logs'])

CONFIG = {
    'fusionsolar': {
        'username': 'seu_usuario@email.com',
        'password': 'sua_senha',
        'base_url': 'https://intl.fusionsolar.huawei.com'
    },
    'relatorio': {
        'nome_empresa': 'Minha Empresa Solar',
        'telefone': '(00) 0000-0000',
        'email': 'contato@empresa.com',
        'tarifa_energia_kwh': 0.887,
        'fator_emissao_co2': 0.0817,
        'cor_primaria': '#FF6B00',
        'cor_secundaria': '#2C3E50'
    }
}

# Lista de clientes
CLIENTES = [
    {
        'station_code': 'NE=12345678',
        'nome': 'João Silva',
        'potencia_kwp': 5.4,
        'email': 'joao@email.com'
    },
    {
        'station_code': 'NE=87654321',
        'nome': 'Empresa ABC',
        'potencia_kwp': 15.6,
        'email': 'contato@abc.com'
    },
    {
        'station_code': 'NE=11223344',
        'nome': 'Indústria XYZ',
        'potencia_kwp': 75.0,
        'email': 'energia@xyz.com'
    }
]

MES = 11
ANO = 2023

def processar_cliente(api, extrator, gerador, cliente, mes, ano):
    """Processa um cliente individual"""
    nome = cliente['nome']
    station_code = cliente['station_code']
    
    print(f"\n{'=' * 70}")
    print(f"Processando: {nome}")
    print('=' * 70)
    
    try:
        # Extrai dados
        print("  → Extraindo dados da API...")
        dados = extrator.comparar_com_mes_anterior(
            station_code=station_code,
            mes=mes,
            ano=ano,
            potencia_kwp=cliente.get('potencia_kwp')
        )
        
        # Adiciona info do cliente
        dados['cliente'] = {
            'nome': nome,
            'email': cliente.get('email'),
            'telefone': cliente.get('telefone')
        }
        
        # Salva JSON intermediário
        json_path = os.path.join(
            'output/dados',
            gerar_nome_arquivo(nome, mes, ano, 'json')
        )
        print(f"  → Salvando dados: {json_path}")
        salvar_json(dados, json_path)
        
        # Gera PDF
        pdf_path = os.path.join(
            'output/relatorios',
            gerar_nome_arquivo(nome, mes, ano, 'pdf')
        )
        print(f"  → Gerando PDF: {pdf_path}")
        gerador.gerar_relatorio(dados, pdf_path)
        
        print(f"\n  ✅ Sucesso!")
        print(f"     📄 PDF: {pdf_path}")
        print(f"     ⚡ Geração: {dados['geracao']['total_kwh']:.2f} kWh")
        print(f"     💰 Economia: R$ {dados['economia']['economia_mensal']:.2f}")
        
        return {
            'status': 'sucesso',
            'nome': nome,
            'geracao_kwh': dados['geracao']['total_kwh'],
            'economia_rs': dados['economia']['economia_mensal']
        }
        
    except Exception as e:
        print(f"\n  ❌ Erro ao processar {nome}: {e}")
        return {
            'status': 'erro',
            'nome': nome,
            'erro': str(e)
        }

def main():
    """Processa múltiplos clientes"""
    print("\n" + "=" * 70)
    print("PROCESSAMENTO DE MÚLTIPLOS CLIENTES")
    print("=" * 70)
    print(f"Período: {MES:02d}/{ANO}")
    print(f"Total de clientes: {len(CLIENTES)}")
    
    # Inicializa API
    print("\n[1/3] Conectando à API...")
    api = FusionSolarAPI(
        username=CONFIG['fusionsolar']['username'],
        password=CONFIG['fusionsolar']['password'],
        base_url=CONFIG['fusionsolar']['base_url']
    )
    
    if not api.login():
        print("❌ Falha no login!")
        return
    
    print("✅ Conectado!")
    
    # Inicializa componentes
    extrator = ExtratorDados(api)
    gerador = GeradorRelatorio(CONFIG)
    
    # Processa cada cliente
    print(f"\n[2/3] Processando {len(CLIENTES)} clientes...")
    resultados = []
    
    for i, cliente in enumerate(CLIENTES, 1):
        print(f"\n[Cliente {i}/{len(CLIENTES)}]")
        resultado = processar_cliente(api, extrator, gerador, cliente, MES, ANO)
        resultados.append(resultado)
    
    # Logout
    print("\n[3/3] Encerrando sessão...")
    api.logout()
    
    # Resumo final
    print("\n" + "=" * 70)
    print("RESUMO FINAL")
    print("=" * 70)
    
    sucessos = [r for r in resultados if r['status'] == 'sucesso']
    erros = [r for r in resultados if r['status'] == 'erro']
    
    print(f"\n✅ Sucessos: {len(sucessos)}")
    print(f"❌ Erros: {len(erros)}")
    
    if sucessos:
        print("\n📊 Estatísticas dos sucessos:")
        total_geracao = sum(r['geracao_kwh'] for r in sucessos)
        total_economia = sum(r['economia_rs'] for r in sucessos)
        
        print(f"   Total gerado: {total_geracao:,.2f} kWh")
        print(f"   Total economizado: R$ {total_economia:,.2f}")
        print(f"\n   Detalhamento:")
        for r in sucessos:
            print(f"   • {r['nome']}: {r['geracao_kwh']:,.2f} kWh | R$ {r['economia_rs']:,.2f}")
    
    if erros:
        print("\n❌ Clientes com erro:")
        for r in erros:
            print(f"   • {r['nome']}: {r['erro']}")
    
    print("\n" + "=" * 70)
    print(f"📁 Relatórios salvos em: output/relatorios/")
    print(f"📊 Dados JSON salvos em: output/dados/")
    print("=" * 70)

if __name__ == '__main__':
    main()
