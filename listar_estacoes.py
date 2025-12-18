#!/usr/bin/env python3
"""
Script para listar todas as estações disponíveis na conta FusionSolar.
Use os códigos retornados para configurar o clientes.yaml
"""
import yaml
from src.fusionsolar_api import FusionSolarAPI

# Carrega configuração
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

fs_config = config['fusionsolar']
api = FusionSolarAPI(
    username=fs_config['username'],
    password=fs_config['password'],
    base_url=fs_config['base_url']
)

print("Conectando à API FusionSolar...")
api.login()

print("\n" + "="*80)
print("ESTAÇÕES DISPONÍVEIS")
print("="*80)

estacoes = api.get_station_list()

for i, est in enumerate(estacoes, 1):
    code = est.get('stationCode', 'N/A')
    name = est.get('stationName', 'N/A')
    capacity = est.get('capacity', 0)
    addr = est.get('stationAddr', 'N/A')
    
    print(f"\n{i}. {name}")
    print(f"   Código: {code}")
    print(f"   Capacidade: {capacity} kWp")
    print(f"   Endereço: {addr}")

print("\n" + "="*80)
print(f"Total: {len(estacoes)} estações")
print("="*80)
print("\nCopie os códigos acima para o arquivo config/clientes.yaml")

api.logout()
