#!/usr/bin/env python3
"""
Script de diagnóstico completo para API FusionSolar
Testa múltiplos endpoints e métodos de autenticação
"""

import requests
import hashlib
import json
import base64

# Credenciais
API_USER = "teste-relatorio"
API_PASS = "qcd3se9D*"
WEB_USER = "COMSOL.ENERGIAS"
WEB_PASS = "comsol2023"
BASE_URL = "https://la5.fusionsolar.huawei.com"

print("=" * 70)
print("DIAGNÓSTICO COMPLETO - API FUSIONSOLAR")
print("=" * 70)

session = requests.Session()
session.headers.update({
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

# =====================================================
# TESTE 1: Verificar se o servidor responde
# =====================================================
print("\n[TESTE 1] Verificando conectividade com o servidor...")
try:
    resp = requests.get(BASE_URL, timeout=10)
    print(f"✅ Servidor acessível - Status: {resp.status_code}")
except Exception as e:
    print(f"❌ Servidor não acessível: {e}")

# =====================================================
# TESTE 2: Endpoint /thirdData/login com hash SHA256
# =====================================================
print("\n[TESTE 2] Endpoint /thirdData/login (método padrão - SHA256)...")
password_hash = hashlib.sha256(API_PASS.encode()).hexdigest()
data = {"userName": API_USER, "systemCode": password_hash}
try:
    resp = session.post(f"{BASE_URL}/thirdData/login", json=data, timeout=30)
    result = resp.json()
    print(f"Status: {resp.status_code}")
    print(f"Resposta: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"Erro: {e}")

# =====================================================
# TESTE 3: Tentar sem hash (senha plain text)
# =====================================================
print("\n[TESTE 3] Endpoint /thirdData/login (senha sem hash)...")
data = {"userName": API_USER, "systemCode": API_PASS}
try:
    resp = session.post(f"{BASE_URL}/thirdData/login", json=data, timeout=30)
    result = resp.json()
    print(f"Status: {resp.status_code}")
    print(f"Resposta: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"Erro: {e}")

# =====================================================
# TESTE 4: Outros campos de autenticação
# =====================================================
print("\n[TESTE 4] Testando campos alternativos (password ao invés de systemCode)...")
data = {"userName": API_USER, "password": API_PASS}
try:
    resp = session.post(f"{BASE_URL}/thirdData/login", json=data, timeout=30)
    result = resp.json()
    print(f"Status: {resp.status_code}")
    print(f"Resposta: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"Erro: {e}")

# =====================================================
# TESTE 5: Endpoint diferente /login
# =====================================================
print("\n[TESTE 5] Endpoint alternativo /authn/v3/login...")
data = {"userName": WEB_USER, "password": WEB_PASS}
try:
    resp = session.post(f"{BASE_URL}/authn/v3/login", json=data, timeout=30)
    print(f"Status: {resp.status_code}")
    print(f"Headers: {dict(resp.headers)}")
    try:
        result = resp.json()
        print(f"Resposta: {json.dumps(result, indent=2)}")
    except:
        print(f"Resposta (texto): {resp.text[:500]}")
except Exception as e:
    print(f"Erro: {e}")

# =====================================================
# TESTE 6: Endpoint NorthBound API
# =====================================================
print("\n[TESTE 6] Endpoint NorthBound /nbi/v2/login...")
data = {"userName": API_USER, "password": API_PASS}
try:
    resp = session.post(f"{BASE_URL}/nbi/v2/login", json=data, timeout=30)
    print(f"Status: {resp.status_code}")
    try:
        result = resp.json()
        print(f"Resposta: {json.dumps(result, indent=2)}")
    except:
        print(f"Resposta (texto): {resp.text[:500]}")
except Exception as e:
    print(f"Erro: {e}")

# =====================================================
# TESTE 7: Listar endpoints disponíveis
# =====================================================
print("\n[TESTE 7] Verificando endpoints conhecidos...")
endpoints = [
    "/thirdData/login",
    "/thirdData/stations", 
    "/authn/v3/login",
    "/nbi/v2/login",
    "/rest/login",
    "/api/login",
    "/rest/neteco/login",
]
for endpoint in endpoints:
    try:
        resp = session.options(f"{BASE_URL}{endpoint}", timeout=5)
        print(f"  {endpoint}: {resp.status_code}")
    except Exception as e:
        print(f"  {endpoint}: Erro - {str(e)[:30]}")

# =====================================================
# SUMÁRIO
# =====================================================
print("\n" + "=" * 70)
print("SUMÁRIO DO DIAGNÓSTICO")
print("=" * 70)
print("""
POSSÍVEIS PROBLEMAS:

1. **Tipo de conta de API**: A FusionSolar tem diferentes tipos de API:
   - NorthBound Interface API (para integradores)
   - Third-party Management System API
   - OpenAPI (para desenvolvedores certificados)
   
   Cada uma requer credenciais diferentes criadas em locais diferentes.

2. **Servidor regional**: O servidor 'la5' é específico para América Latina.
   Verifique se suas credenciais de API foram criadas no mesmo servidor.

3. **Vinculação da conta**: A conta de API precisa estar vinculada à conta
   principal que tem acesso às plantas. Verifique no painel se o usuário
   de API tem permissões para acessar as estações.

4. **Formato do usuário**: Alguns sistemas exigem o nome de usuário completo
   incluindo domínio ou sufixo específico.

PRÓXIMOS PASSOS RECOMENDADOS:

1. Acesse: https://la5.fusionsolar.huawei.com
2. Faça login com COMSOL.ENERGIAS
3. Vá em: Sistema > API Management ou Gerenciamento de API
4. Verifique se:
   - O usuário 'teste-relatorio' existe e está ativo
   - Ele tem permissão para acessar as plantas
   - Copie o nome de usuário EXATO como aparece no sistema
   - Gere uma nova senha se necessário

5. Procure também por documentação específica do NorthBound API
""")
