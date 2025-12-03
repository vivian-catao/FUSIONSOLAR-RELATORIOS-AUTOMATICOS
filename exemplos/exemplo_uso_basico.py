"""
Exemplo de uso básico do sistema
Gera relatório para um único cliente em um mês específico
"""

import sys
import os

# Adiciona diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.fusionsolar_api import FusionSolarAPI
from src.extrator_dados import ExtratorDados
from src.gerador_relatorio import GeradorRelatorio
from src.utils import configurar_logging, criar_diretorios

# Configuração básica
configurar_logging('INFO')
criar_diretorios(['output/relatorios', 'output/dados'])

# Dados de configuração
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

# Dados do cliente
STATION_CODE = 'NE=12345678'  # Código da estação FusionSolar
POTENCIA_KWP = 5.4             # Potência instalada em kWp
MES = 11                       # Mês (1-12)
ANO = 2023                     # Ano

def main():
    """Exemplo de uso básico"""
    print("=" * 70)
    print("EXEMPLO DE USO BÁSICO - GERAÇÃO DE RELATÓRIO ÚNICO")
    print("=" * 70)
    
    # 1. Inicializa API e faz login
    print("\n[1/4] Conectando à API FusionSolar...")
    api = FusionSolarAPI(
        username=CONFIG['fusionsolar']['username'],
        password=CONFIG['fusionsolar']['password'],
        base_url=CONFIG['fusionsolar']['base_url']
    )
    
    if not api.login():
        print("❌ Falha no login!")
        return
    
    print("✅ Login realizado com sucesso!")
    
    try:
        # 2. Extrai dados
        print(f"\n[2/4] Extraindo dados de {MES}/{ANO}...")
        extrator = ExtratorDados(api)
        
        dados = extrator.comparar_com_mes_anterior(
            station_code=STATION_CODE,
            mes=MES,
            ano=ANO,
            potencia_kwp=POTENCIA_KWP
        )
        
        print(f"✅ Dados extraídos!")
        print(f"   - Geração total: {dados['geracao']['total_kwh']:.2f} kWh")
        print(f"   - Economia: R$ {dados['economia']['economia_mensal']:.2f}")
        print(f"   - CO2 evitado: {dados['impacto_ambiental']['co2_evitado_kg']:.2f} kg")
        
        # 3. Gera relatório PDF
        print("\n[3/4] Gerando relatório PDF...")
        gerador = GeradorRelatorio(CONFIG)
        
        pdf_path = f'output/relatorios/relatorio_{ANO}{MES:02d}.pdf'
        gerador.gerar_relatorio(dados, pdf_path)
        
        print(f"✅ Relatório gerado: {pdf_path}")
        
        # 4. Logout
        print("\n[4/4] Encerrando sessão...")
        api.logout()
        
        print("\n" + "=" * 70)
        print("✅ PROCESSO CONCLUÍDO COM SUCESSO!")
        print("=" * 70)
        print(f"\n📄 Relatório salvo em: {pdf_path}")
        print(f"⚡ Geração: {dados['geracao']['total_kwh']:.2f} kWh")
        print(f"💰 Economia: R$ {dados['economia']['economia_mensal']:.2f}")
        print(f"🌱 CO2 evitado: {dados['impacto_ambiental']['co2_evitado_kg']:.2f} kg")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        api.logout()
        raise

if __name__ == '__main__':
    main()
