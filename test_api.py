#!/usr/bin/env python3
"""
Script de teste para verificar conexão com API FusionSolar
"""

import requests
import hashlib
import json

# Suas credenciais de API
USERNAME = "teste-relatorio"
PASSWORD = "qcd3se9D*"
BASE_URL = "https://la5.fusionsolar.huawei.com"

print("=" * 70)
print("TESTE DE CONEXÃO API FUSIONSOLAR")
print("=" * 70)
print(f"Servidor: {BASE_URL}")
print(f"Usuário: {USERNAME}")
print()

# Gera hash SHA256 da senha
password_hash = hashlib.sha256(PASSWORD.encode()).hexdigest()
print(f"Hash da senha (SHA256): {password_hash[:20]}...")
print()

# Prepara dados do login
data = {
    "userName": USERNAME,
    "systemCode": password_hash
}

# Endpoint de login
endpoint = f"{BASE_URL}/thirdData/login"
print(f"Tentando login em: {endpoint}")
print()

# Faz requisição
try:
    headers = {
        'Content-Type': 'application/json',
        'Connection': 'keep-alive'
    }
    
    response = requests.post(endpoint, json=data, headers=headers, timeout=30)
    
    print(f"Status HTTP: {response.status_code}")
    print()
    print("Resposta da API:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print()
    
    if response.json().get('success'):
        print("✅ Login realizado com sucesso!")
        print(f"Token: {response.json().get('data', '')[:50]}...")
    else:
        print("❌ Falha no login")
        print(f"Mensagem: {response.json().get('message', 'Sem mensagem')}")
        print()
        print("POSSÍVEIS CAUSAS:")
        print("1. Credenciais de API diferentes das credenciais do site web")
        print("2. Servidor incorreto (verifique se é realmente 'la5')")
        print("3. Conta sem acesso à API habilitado")
        print("4. Necessário solicitar credenciais de API ao suporte Huawei")
        
except Exception as e:
    print(f"❌ Erro na requisição: {e}")
    print()
    print("Verifique se:")
    print("- Você tem acesso à internet")
    print("- O servidor la5.fusionsolar.huawei.com está acessível")
    print("- Não há bloqueio de firewall")

print()
print("=" * 70)
