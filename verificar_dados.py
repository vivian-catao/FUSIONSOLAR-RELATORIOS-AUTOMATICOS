#!/usr/bin/env python3
"""
Script para verificar dados retornados pela API
"""
import yaml
import json
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

# Busca estações
print("\n" + "="*60)
print("TESTANDO DIFERENTES ENDPOINTS")
print("="*60)

estacoes = api.get_station_list()
print(f"✅ getStationList: {len(estacoes)} estações encontradas")

# Testa com a primeira estação
station_code = estacoes[0].get('stationCode')
station_name = estacoes[0].get('stationName')
print(f"\nTestando endpoints para: {station_name} ({station_code})")

# 1. Dados em tempo real
print("\n1. getStationRealKpi (tempo real):")
url = f"{api.base_url}/thirdData/getStationRealKpi"
data = {"stationCodes": station_code}
response = api.session.post(url, json=data, timeout=30)
result = response.json()
print(f"   success: {result.get('success')}")
print(f"   data: {result.get('data', 'N/A')[:200] if result.get('data') else 'vazio'}")

# 2. KPI Mensal
print("\n2. getKpiStationMonth (mensal):")
url = f"{api.base_url}/thirdData/getKpiStationMonth"
data = {"stationCodes": station_code, "collectTime": 202511}
response = api.session.post(url, json=data, timeout=30)
result = response.json()
print(f"   success: {result.get('success')}")
print(f"   data: {result.get('data')}")

# 3. KPI Diário
print("\n3. getKpiStationDay (diário):")
url = f"{api.base_url}/thirdData/getKpiStationDay"
data = {"stationCodes": station_code, "collectTime": 20251110}
response = api.session.post(url, json=data, timeout=30)
result = response.json()
print(f"   success: {result.get('success')}")
print(f"   data: {result.get('data')}")

# 4. Lista de dispositivos
print("\n4. getDevList (dispositivos):")
url = f"{api.base_url}/thirdData/getDevList"
data = {"stationCodes": station_code}
response = api.session.post(url, json=data, timeout=30)
result = response.json()
print(f"   success: {result.get('success')}")
print(f"   data count: {len(result.get('data', []))}")
if result.get('data'):
    print(f"   primeiro dispositivo: {json.dumps(result['data'][0], indent=4)}")

api.logout()
