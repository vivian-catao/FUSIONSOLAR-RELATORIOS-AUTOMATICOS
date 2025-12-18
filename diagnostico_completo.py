#!/usr/bin/env python3
"""
Script para verificar TODOS os dados disponíveis na API FusionSolar
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

station_code = "NE=43772224"  # ANDRÉ LUIZ

print(f"\n{'='*70}")
print(f"DADOS COMPLETOS PARA: {station_code}")
print("="*70)

# 1. Dados em tempo real (funciona!)
print("\n1. DADOS EM TEMPO REAL (getStationRealKpi):")
url = f"{api.base_url}/thirdData/getStationRealKpi"
data = {"stationCodes": station_code}
response = api.session.post(url, json=data, timeout=30)
result = response.json()
if result.get('data'):
    print(json.dumps(result['data'][0], indent=2, default=str))
else:
    print("   Sem dados")

# 2. Dados da estação
print("\n2. DADOS DA ESTAÇÃO:")
estacoes = api.get_station_list()
for est in estacoes:
    if est.get('stationCode') == station_code:
        print(json.dumps(est, indent=2, default=str))
        break

# 3. Lista de dispositivos
print("\n3. DISPOSITIVOS (getDevList):")
url = f"{api.base_url}/thirdData/getDevList"
data = {"stationCodes": station_code}
response = api.session.post(url, json=data, timeout=30)
result = response.json()
if result.get('data'):
    for dev in result['data']:
        print(f"   - {dev.get('devName')} (Tipo: {dev.get('devTypeId')}, Modelo: {dev.get('model')})")
        print(f"     SN: {dev.get('esnCode')}")

# 4. Dados em tempo real dos dispositivos (inversores)
print("\n4. DADOS DOS INVERSORES EM TEMPO REAL (getDevRealKpi):")
for dev in result.get('data', []):
    dev_id = dev.get('id')
    dev_type = dev.get('devTypeId')
    dev_name = dev.get('devName')
    
    url = f"{api.base_url}/thirdData/getDevRealKpi"
    data = {"devIds": str(dev_id), "devTypeId": dev_type}
    response = api.session.post(url, json=data, timeout=30)
    dev_result = response.json()
    
    print(f"\n   {dev_name} (tipo {dev_type}):")
    if dev_result.get('data'):
        print(f"   {json.dumps(dev_result['data'][0] if dev_result['data'] else {}, indent=4, default=str)}")
    else:
        print(f"   Sem dados (failCode: {dev_result.get('failCode')})")

# 5. Histórico de KPIs do dispositivo
print("\n5. KPIs HISTÓRICOS DOS DISPOSITIVOS (getDevKpiDay):")
for dev in result.get('data', [])[:2]:  # Apenas primeiros 2
    dev_id = dev.get('id')
    dev_type = dev.get('devTypeId')
    dev_name = dev.get('devName')
    
    url = f"{api.base_url}/thirdData/getDevKpiDay"
    data = {"devIds": str(dev_id), "devTypeId": dev_type, "collectTime": 20251210}
    response = api.session.post(url, json=data, timeout=30)
    dev_result = response.json()
    
    print(f"\n   {dev_name}:")
    print(f"   success: {dev_result.get('success')}, failCode: {dev_result.get('failCode')}")
    if dev_result.get('data'):
        print(f"   {json.dumps(dev_result['data'][0] if dev_result['data'] else {}, indent=4, default=str)[:500]}")

api.logout()
print("\n✅ Diagnóstico concluído!")
