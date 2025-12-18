#!/usr/bin/env python3
"""
Script para verificar todos os dados extraídos
"""

import os
import json
from dotenv import load_dotenv
from src.fusionsolar_api import FusionSolarAPI
from src.extrator_dados import ExtratorDados

load_dotenv()

def main():
    # Conecta API
    api = FusionSolarAPI(
        username=os.getenv('FUSIONSOLAR_USERNAME'),
        password=os.getenv('FUSIONSOLAR_PASSWORD'),
        base_url=os.getenv('FUSIONSOLAR_URL', 'https://la5.fusionsolar.huawei.com')
    )
    api.login()
    
    # Extrai dados
    extrator = ExtratorDados(api)
    station_code = "NE=43772224"  # ANDRÉ LUIZ - BROW
    
    dados = extrator.extrair_dados_mensais(station_code, mes=11, ano=2025)
    
    print("\n" + "="*80)
    print("DADOS EXTRAÍDOS PARA O RELATÓRIO")
    print("="*80)
    
    # Estação
    print("\n📍 ESTAÇÃO:")
    for k, v in dados['estacao'].items():
        print(f"   {k}: {v}")
    
    # Geração
    print("\n⚡ GERAÇÃO:")
    for k, v in dados['geracao'].items():
        if k != 'geracao_diaria':
            print(f"   {k}: {v}")
        else:
            print(f"   {k}: {len(v)} dias com dados")
    
    # Performance
    print("\n📊 PERFORMANCE:")
    for k, v in dados['performance'].items():
        print(f"   {k}: {v}")
    
    # Economia
    print("\n💰 ECONOMIA:")
    for k, v in dados['economia'].items():
        print(f"   {k}: {v}")
    
    # Impacto Ambiental
    print("\n🌱 IMPACTO AMBIENTAL:")
    for k, v in dados['impacto_ambiental'].items():
        print(f"   {k}: {v}")
    
    # Sistema
    print("\n🔧 SISTEMA:")
    print(f"   num_inversores: {dados['sistema']['num_inversores']}")
    
    # Inversores detalhados
    print("\n🔌 INVERSORES (detalhado):")
    for inv in dados['sistema']['inversores']:
        print(f"\n   --- {inv.get('nome', 'N/A')} ---")
        for k, v in inv.items():
            if k != '_raw':
                print(f"      {k}: {v}")
    
    # Resumo inversores
    print("\n📈 RESUMO INVERSORES:")
    if dados['sistema'].get('inversores_resumo'):
        for k, v in dados['sistema']['inversores_resumo'].items():
            print(f"   {k}: {v}")
    
    # Alarmes
    print("\n⚠️ ALARMES:")
    for k, v in dados['sistema']['alarmes'].items():
        if k != 'lista':
            print(f"   {k}: {v}")
    
    api.logout()
    print("\n" + "="*80)
    print("✅ Verificação concluída!")
    print("="*80)

if __name__ == "__main__":
    main()
