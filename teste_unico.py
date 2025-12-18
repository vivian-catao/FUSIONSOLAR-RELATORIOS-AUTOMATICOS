#!/usr/bin/env python3
"""
Teste único - uma combinação por execução para evitar rate limit
Execute várias vezes com diferentes argumentos
"""

import requests
import hashlib
import json
import sys

API_USER = "teste-relatorio"
API_PASS = "qcd3se9D*"
BASE_URL = "https://la5.fusionsolar.huawei.com"

# Opções disponíveis
opcoes = {
    "1": ("userName", "systemCode", API_PASS, "plain"),
    "2": ("userName", "systemCode", hashlib.sha256(API_PASS.encode()).hexdigest(), "SHA256"),
    "3": ("userName", "systemCode", hashlib.sha256(API_PASS.encode()).hexdigest().upper(), "SHA256 UPPER"),
    "4": ("userName", "password", API_PASS, "plain"),
    "5": ("userName", "password", hashlib.sha256(API_PASS.encode()).hexdigest(), "SHA256"),
}

print("=" * 60)
print("TESTE ÚNICO DE AUTENTICAÇÃO")
print("=" * 60)
print()

if len(sys.argv) < 2:
    print("Uso: python teste_unico.py <numero>")
    print()
    print("Opções disponíveis:")
    for k, v in opcoes.items():
        print(f"  {k} - {v[0]} + {v[1]} ({v[3]})")
    print()
    print("Exemplo: python teste_unico.py 2")
    sys.exit(0)

escolha = sys.argv[1]
if escolha not in opcoes:
    print(f"Opção inválida: {escolha}")
    sys.exit(1)

campo_user, campo_senha, valor_senha, tipo = opcoes[escolha]

print(f"Testando: {campo_user} + {campo_senha} ({tipo})")
print(f"Usuário: {API_USER}")
print(f"Valor senha: {valor_senha[:40]}...")
print()

session = requests.Session()
session.headers.update({
    'Content-Type': 'application/json',
    'Accept': 'application/json',
})

data = {
    campo_user: API_USER,
    campo_senha: valor_senha
}

print(f"Enviando para: {BASE_URL}/thirdData/login")
print(f"Payload: {json.dumps(data, indent=2)[:200]}...")
print()

try:
    resp = session.post(f"{BASE_URL}/thirdData/login", json=data, timeout=30)
    result = resp.json()
    
    print(f"Status HTTP: {resp.status_code}")
    print(f"Resposta: {json.dumps(result, indent=2)}")
    print()
    
    if result.get('success'):
        print("🎉 SUCESSO! Login funcionou!")
        print(f"Token: {result.get('data')}")
    elif result.get('failCode') == 407:
        print("⏳ RATE LIMIT - Aguarde alguns minutos e tente novamente")
    else:
        print(f"❌ Falha: {result.get('message')}")
        
except Exception as e:
    print(f"Erro: {e}")
