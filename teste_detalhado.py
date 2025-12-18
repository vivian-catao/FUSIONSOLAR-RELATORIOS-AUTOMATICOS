#!/usr/bin/env python3
"""
Teste detalhado com logs completos de resposta
"""

import requests
import hashlib
import json

API_USER = "teste-relatorio"
API_PASS = "qcd3se9D*"
BASE_URL = "https://la5.fusionsolar.huawei.com"

print("=" * 70)
print("TESTE DETALHADO COM RESPOSTA COMPLETA")
print("=" * 70)

session = requests.Session()
session.headers.update({
    'Content-Type': 'application/json',
    'Accept': 'application/json',
})

senha_sha256 = hashlib.sha256(API_PASS.encode()).hexdigest()

data = {
    "userName": API_USER,
    "systemCode": senha_sha256
}

print(f"\nRequisição:")
print(f"  URL: {BASE_URL}/thirdData/login")
print(f"  Payload: {json.dumps(data, indent=4)}")
print()

resp = session.post(f"{BASE_URL}/thirdData/login", json=data, timeout=30)

print(f"Resposta:")
print(f"  Status Code: {resp.status_code}")
print(f"  Headers: {dict(resp.headers)}")
print()
print(f"  Body:")
print(json.dumps(resp.json(), indent=4, ensure_ascii=False))
print()

# Verificar o failCode
result = resp.json()
fail_code = result.get('failCode')

print("=" * 70)
print("ANÁLISE DO ERRO")
print("=" * 70)

if fail_code == 20400:
    print("""
Código de erro: 20400 - user.login.user_or_value_invalid

Este erro específico indica que:
- O usuário NÃO foi encontrado, OU
- A senha/systemCode está incorreta

Como o usuário 'teste-relatorio' aparece no painel de Gestão de API,
o problema é provavelmente a SENHA.

SOLUÇÃO RECOMENDADA:
1. No painel de Gestão de API, clique no ícone de LÁPIS (editar) 
   ao lado de 'teste-relatorio'
2. Resete/altere a senha
3. IMPORTANTE: Ao criar a senha, copie EXATAMENTE como ela aparece
   (alguns sistemas adicionam caracteres ou codificam de forma diferente)
4. Tente novamente com a nova senha
""")

elif fail_code == 407:
    print("""
Código de erro: 407 - Proxy Authentication Required ou Rate Limit

Isso pode indicar:
- Muitas tentativas de login (bloqueio temporário)
- Necessidade de autenticação adicional
- IP bloqueado temporariamente

Aguarde alguns minutos e tente novamente.
""")
