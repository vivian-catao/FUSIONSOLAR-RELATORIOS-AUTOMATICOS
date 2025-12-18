# 🚀 Guia Rápido de Uso

## Para testar o sistema imediatamente com dados do exemplo Diomar:

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Executar exemplo com dados simulados
```bash
python exemplo_diomar.py
```

### 3. Ver resultado
O relatório será gerado em:
- **PDF**: `output/relatorios/exemplo_diomar_novembro_2025.pdf`
- **JSON**: `output/dados/exemplo_diomar_novembro_2025.json`

---

## 📊 O que o exemplo demonstra:

✅ Cliente: **DIOMAR DE OLIVEIRA**  
✅ Sistema: **8,4 kWp**  
✅ Período: **Novembro/2025**  
✅ Geração: **1.286,98 kWh**  
✅ Economia: **R$ 1.141,55**  
✅ CO₂ evitado: **~105 kg**  
✅ Árvores equivalentes: **~0,6**  
✅ Performance Ratio: **~78%**  

---

## 🎯 Características do PDF Gerado:

- ✨ Design profissional com gradientes
- 📊 Resumo executivo com KPIs
- 📈 Gráfico de barras (geração diária)
- 💎 Cards de métricas principais
- ⚡ Análise de performance
- 🌍 Impacto ambiental detalhado
- 🔧 Status do sistema
- 💰 Formatação brasileira (R$, dd/mm/yyyy)
- 🕐 Timezone: America/Sao_Paulo

---

## Para usar com API real:

1. Copie os arquivos de exemplo:
```bash
cp config/config.yaml.example config/config.yaml
cp config/clientes.yaml.example config/clientes.yaml
```

2. Edite com suas credenciais:
```bash
nano config/config.yaml  # Adicione username/password FusionSolar
nano config/clientes.yaml  # Adicione seus clientes
```

3. Execute:
```bash
python main.py --mes 11 --ano 2025
```

---

## � Sistema de Cache (Evita Rate Limit!)

O sistema agora possui **cache automático** que armazena respostas da API por 24h:

### ✅ Vantagens:
- **Evita rate limit** durante testes
- **Respostas instantâneas** (dados em cache)
- **Economia de chamadas** à API
- **Desenvolvimento mais rápido**

### 📊 Gerenciar Cache:

**Ver estatísticas:**
```bash
python gerenciar_cache.py stats
```

**Limpar todo cache:**
```bash
python gerenciar_cache.py clear
```

**Limpar cache antigo (>48h):**
```bash
python gerenciar_cache.py clear-old --hours 48
```

### ⚙️ Configurar:

**Desabilitar cache** (forçar API sempre):
```bash
export CACHE_ENABLED=false
python main.py
```

**Cache está em:** `.cache/fusionsolar/` (excluído do git)

---

## �📝 Nota Importante:

O arquivo `exemplo_diomar.py` usa dados **simulados realistas** e não requer API ou configuração. É perfeito para:
- ✅ Testar o sistema
- ✅ Ver o design do relatório
- ✅ Demonstrar para clientes
- ✅ Desenvolvimento/testes

---

**Pronto! Sistema 100% funcional! 🎉**
