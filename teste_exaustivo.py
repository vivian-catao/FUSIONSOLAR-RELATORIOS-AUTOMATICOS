#!/usr/bin/env python3
"""
Teste exaustivo de todas as combinações possíveis de autenticação
"""

import requests
import hashlib
import json
import time

API_USER = "teste-relatorio"
API_PASS = "qcd3se9D*"
BASE_URL = "https://la5.fusionsolar.huawei.com"

DELAY_ENTRE_TESTES = 30  # segundos entre cada teste

print("=" * 70)
print("TESTE EXAUSTIVO DE AUTENTICAÇÃO")
print(f"(Delay de {DELAY_ENTRE_TESTES}s entre testes para evitar rate limit)")
print("=" * 70)
print(f"Usuário: {API_USER}")
print(f"Senha: {API_PASS}")
print(f"Base URL: {BASE_URL}")
print()

session = requests.Session()
session.headers.update({
    'Content-Type': 'application/json',
    'Accept': 'application/json',
})

# Diferentes hashes da senha
senha_plain = API_PASS
senha_sha256 = hashlib.sha256(API_PASS.encode()).hexdigest()
senha_sha256_upper = senha_sha256.upper()
senha_md5 = hashlib.md5(API_PASS.encode()).hexdigest()

print("Hashes gerados:")
print(f"  Plain: {senha_plain}")
print(f"  SHA256: {senha_sha256[:30]}...")
print(f"  SHA256 UPPER: {senha_sha256_upper[:30]}...")
print(f"  MD5: {senha_md5}")
print()

# Combinações para testar
combinacoes = [
    # (campo_usuario, campo_senha, valor_senha, descricao)
    ("userName", "systemCode", senha_plain, "userName + systemCode (plain)"),
    ("userName", "systemCode", senha_sha256, "userName + systemCode (SHA256)"),
    ("userName", "systemCode", senha_sha256_upper, "userName + systemCode (SHA256 UPPER)"),
    ("userName", "systemCode", senha_md5, "userName + systemCode (MD5)"),
    ("userName", "password", senha_plain, "userName + password (plain)"),
    ("userName", "password", senha_sha256, "userName + password (SHA256)"),
    ("username", "systemCode", senha_plain, "username + systemCode (plain)"),
    ("username", "systemCode", senha_sha256, "username + systemCode (SHA256)"),
    ("username", "password", senha_plain, "username + password (plain)"),
    ("user", "systemCode", senha_sha256, "user + systemCode (SHA256)"),
]

# Endpoints para testar
endpoints = [
    "/thirdData/login",
    "/thirdData/v1/login", 
    "/rest/dp/web/v1/auth/login",
]

print("Testando combinações...")
print("-" * 70)

teste_num = 0
for endpoint in endpoints:
    print(f"\n📍 Endpoint: {endpoint}")
    print("-" * 50)
    
    for campo_user, campo_pass, valor_senha, desc in combinacoes:
        teste_num += 1
        data = {
            campo_user: API_USER,
            campo_pass: valor_senha
        }
        
        print(f"  [{teste_num}] Testando: {desc}...", end=" ", flush=True)
        
        try:
            resp = session.post(f"{BASE_URL}{endpoint}", json=data, timeout=10)
            result = resp.json()
            
            success = result.get('success', False)
            message = result.get('message', result.get('failCode', 'N/A'))
            
            if success:
                print(f"✅ SUCESSO!")
                print(f"\n     Token: {result.get('data', '')[:30]}...")
                print()
                print("=" * 70)
                print("CREDENCIAIS CORRETAS ENCONTRADAS!")
                print(f"Endpoint: {endpoint}")
                print(f"Campo usuário: {campo_user}")
                print(f"Campo senha: {campo_pass}")
                print(f"Tipo de senha: {desc.split('(')[1].replace(')', '')}")
                print("=" * 70)
                exit(0)
            else:
                print(f"❌ {message}")
                
        except requests.exceptions.JSONDecodeError:
            print("⚠️ Resposta inválida (HTML)")
        except Exception as e:
            print(f"⚠️ Erro: {str(e)[:30]}")
        
        # Aguarda entre testes para evitar rate limit
        if teste_num < len(combinacoes) * len(endpoints):
            print(f"     ⏳ Aguardando {DELAY_ENTRE_TESTES}s antes do próximo teste...")
            time.sleep(DELAY_ENTRE_TESTES)

print()
print("-" * 70)
print("❌ Nenhuma combinação funcionou")
print()
print("POSSÍVEIS CAUSAS:")
print("1. A senha está incorreta - tente resetar no painel")
print("2. O usuário não está vinculado a nenhuma planta")
print("3. O usuário precisa de permissões adicionais")
print()
print("PRÓXIMOS PASSOS:")
print("1. No painel FusionSolar, clique no lápis (editar) do usuário 'teste-relatorio'")
print("2. Verifique se há opção de vincular plantas/estações")
print("3. Tente resetar a senha e criar uma nova")
print("4. Consulte o 'Guia do desenvolvedor' que aparece na tela de API")
