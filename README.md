# 🌞 FusionSolar Relatórios Automáticos

Sistema completo em Python para automatizar a extração de dados da API FusionSolar (Huawei) e gerar relatórios profissionais em PDF para clientes de energia solar fotovoltaica.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## 📋 Índice

- [Características](#-características)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Exemplos](#-exemplos)
- [API FusionSolar](#-api-fusionsolar)
- [Personalização](#-personalização)
- [Troubleshooting](#-troubleshooting)
- [Contribuindo](#-contribuindo)

## ✨ Características

### 🎨 Design Profissional
- ✅ Layout moderno com gradientes e cores personalizáveis
- ✅ Cards de métricas com KPIs destacados
- ✅ Gráficos de alta qualidade (barras, velocímetro, comparativos)
- ✅ Formatação brasileira (R$, dd/mm/yyyy)
- ✅ Timezone America/Sao_Paulo

### 🔌 Integração com API FusionSolar
- ✅ Autenticação automática com gerenciamento de token
- ✅ Retry logic para requisições
- ✅ Suporte a múltiplas estações/plantas
- ✅ Extração de dados mensais, diários e em tempo real

### 📊 Análise de Dados Completa
- ✅ Geração total mensal e diária
- ✅ Performance Ratio (PR)
- ✅ Horas de Sol Pico (HSP)
- ✅ Disponibilidade do sistema
- ✅ Comparativo com mês anterior
- ✅ Análise de alarmes e eventos

### 💰 Cálculos Automáticos
- ✅ Economia financeira (R$)
- ✅ CO₂ evitado (kg/ton)
- ✅ Árvores equivalentes plantadas
- ✅ Payback simples
- ✅ Eficiência do sistema

### 📄 Relatórios Profissionais em PDF
- ✅ PDF de alta qualidade com WeasyPrint
- ✅ Gráficos interativos com Matplotlib
- ✅ Template HTML personalizável com Jinja2
- ✅ Design responsivo e profissional
- ✅ Identidade visual customizável
- ✅ Resumo executivo detalhado
- ✅ Análise de impacto ambiental
- ✅ Recomendações personalizadas

### 🚀 Código Profissional
- ✅ Type hints em funções críticas
- ✅ Docstrings completas em português
- ✅ Tratamento robusto de erros
- ✅ Logging de todas operações
- ✅ Código modular e extensível
- ✅ Pronto para produção

## 🔧 Pré-requisitos

- **Python 3.8+**
- **Conta FusionSolar** (Huawei) com acesso à API
- **Bibliotecas**: WeasyPrint, Matplotlib, Requests, PyYAML

### Instalação de dependências do sistema (WeasyPrint)

**macOS:**
```bash
brew install python3 cairo pango gdk-pixbuf libffi
```

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-dev python3-pip python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

**Windows:**
- Baixe GTK+ Runtime: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases

## 📥 Instalação

### 1. Clone ou baixe o projeto

```bash
git clone https://github.com/seu-usuario/fusionsolar-relatorios-automaticos.git
cd fusionsolar-relatorios-automaticos
```

### 2. Crie um ambiente virtual (recomendado)

```bash
python3 -m venv venv

# Ativar no Linux/macOS
source venv/bin/activate

# Ativar no Windows
venv\Scripts\activate
```

### 3. Instale as dependências Python

```bash
pip install -r requirements.txt
```

## ⚙️ Configuração

### 1. Configure a API FusionSolar

Copie o exemplo e edite com suas credenciais:

```bash
cp config/config.yaml.example config/config.yaml
```

Edite `config/config.yaml`:

```yaml
fusionsolar:
  base_url: "https://intl.fusionsolar.huawei.com"
  username: "seu_usuario@email.com"
  password: "sua_senha"

relatorio:
  nome_empresa: "Sua Empresa Solar Ltda"
  telefone: "(00) 0000-0000"
  email: "contato@empresa.com"
  tarifa_energia_kwh: 0.887
  fator_emissao_co2: 0.0817
  cor_primaria: "#FF6B00"
  cor_secundaria: "#2C3E50"
```

### 2. Configure a lista de clientes

```bash
cp config/clientes.yaml.example config/clientes.yaml
```

Edite `config/clientes.yaml`:

```yaml
clientes:
  - station_code: "NE=12345678"
    nome: "João Silva"
    email: "joao@email.com"
    telefone: "(11) 98765-4321"
    potencia_kwp: 5.4
    
  - station_code: "NE=87654321"
    nome: "Empresa ABC"
    email: "contato@abc.com"
    potencia_kwp: 15.6
```

### 3. (Opcional) Use variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env` com suas credenciais sensíveis.

## 🚀 Uso

### Uso Básico

Gerar relatórios do mês anterior para todos os clientes:

```bash
python main.py
```

### Argumentos CLI

```bash
# Mês e ano específicos
python main.py --mes 11 --ano 2023

# Cliente específico
python main.py --cliente NE=12345678 --mes 12 --ano 2023

# Salvar dados JSON intermediários
python main.py --salvar-json

# Modo debug (logs detalhados)
python main.py --debug

# Arquivo de configuração customizado
python main.py --config meu_config.yaml --clientes meus_clientes.yaml
```

### Exemplos de Saída

```
==========================================
SISTEMA DE GERAÇÃO DE RELATÓRIOS FUSIONSOLAR
==========================================
Período: 11/2023

[1/3] Processando: João Silva
   ✅ Relatório gerado com sucesso!
   📄 output/relatorios/relatorio_joao_silva_202311.pdf
   ⚡ Geração: 852.45 kWh
   💰 Economia: R$ 756,02

==========================================
RESUMO DA EXECUÇÃO
==========================================
✅ Sucessos: 3
❌ Falhas: 0
📁 Relatórios salvos em: output/relatorios/
==========================================
```

## 📁 Estrutura do Projeto

```
fusionsolar-relatorios-automaticos/
├── README.md                    # Este arquivo
├── requirements.txt             # Dependências Python
├── .env.example                 # Exemplo de variáveis de ambiente
├── .gitignore                   # Arquivos ignorados pelo Git
│
├── config/
│   ├── config.yaml.example      # Exemplo de configuração da API
│   └── clientes.yaml.example    # Exemplo de lista de clientes
│
├── src/
│   ├── __init__.py
│   ├── fusionsolar_api.py       # Cliente da API FusionSolar
│   ├── extrator_dados.py        # Extração e processamento de dados
│   ├── gerador_relatorio.py     # Geração de relatórios PDF
│   ├── calculos.py              # Cálculos (economia, CO2, PR, etc)
│   └── utils.py                 # Funções auxiliares
│
├── templates/
│   └── relatorio_template.html  # Template HTML para PDF
│
├── output/
│   ├── relatorios/              # PDFs gerados
│   └── dados/                   # Dados JSON intermediários
│
├── logs/                        # Logs do sistema
│
├── exemplos/
│   ├── exemplo_uso_basico.py
│   └── exemplo_multiplos_clientes.py
│
└── main.py                      # Script principal
```

## 📚 Exemplos

### Exemplo 1: Uso Básico

```python
from src.fusionsolar_api import FusionSolarAPI
from src.extrator_dados import ExtratorDados
from src.gerador_relatorio import GeradorRelatorio

# Inicializa API
api = FusionSolarAPI(username="user@email.com", password="senha")
api.login()

# Extrai dados
extrator = ExtratorDados(api)
dados = extrator.extrair_dados_mensais("NE=12345678", mes=11, ano=2023)

# Gera relatório
gerador = GeradorRelatorio(config)
gerador.gerar_relatorio(dados, "relatorio_nov2023.pdf")

api.logout()
```

Veja o exemplo completo em: [`exemplos/exemplo_uso_basico.py`](exemplos/exemplo_uso_basico.py)

### Exemplo 2: Múltiplos Clientes

```python
# Processa lista de clientes
clientes = [
    {'station_code': 'NE=111', 'nome': 'Cliente 1', 'potencia_kwp': 5.4},
    {'station_code': 'NE=222', 'nome': 'Cliente 2', 'potencia_kwp': 10.2}
]

for cliente in clientes:
    dados = extrator.extrair_dados_mensais(
        cliente['station_code'], mes=11, ano=2023
    )
    gerador.gerar_relatorio(dados, f"relatorio_{cliente['nome']}.pdf")
```

Veja o exemplo completo em: [`exemplos/exemplo_multiplos_clientes.py`](exemplos/exemplo_multiplos_clientes.py)

## 🔌 API FusionSolar

### Endpoints Implementados

| Endpoint | Descrição |
|----------|-----------|
| `login()` | Autenticação e obtenção de token |
| `get_station_list()` | Lista de todas as estações |
| `get_station_realtime_data()` | Dados em tempo real |
| `get_station_day_kpi()` | KPIs diários |
| `get_station_month_kpi()` | KPIs mensais |
| `get_station_hour_kpi()` | KPIs por hora |
| `get_device_list()` | Lista de dispositivos |
| `get_alarm_list()` | Alarmes do sistema |

### Exemplo de Uso da API

```python
from src.fusionsolar_api import FusionSolarAPI

api = FusionSolarAPI(username="user", password="pass")
api.login()

# Lista estações
estacoes = api.get_station_list()
for estacao in estacoes:
    print(f"{estacao['stationName']}: {estacao['capacity']} kWp")

# Dados mensais
kpi = api.get_station_month_kpi("NE=12345678", "202311")
print(f"Geração: {kpi['dataItemMap']['production_power']} kWh")

api.logout()
```

## 🎨 Personalização

### Cores do Relatório

Edite em `config/config.yaml`:

```yaml
relatorio:
  cor_primaria: "#FF6B00"    # Cor principal (laranja)
  cor_secundaria: "#2C3E50"  # Cor secundária (azul escuro)
```

### Template HTML

Edite `templates/relatorio_template.html` para customizar:
- Layout das páginas
- Seções do relatório
- Estilos CSS
- Conteúdo textual

### Parâmetros de Cálculo

```yaml
relatorio:
  tarifa_energia_kwh: 0.887      # R$/kWh (ajuste conforme sua região)
  fator_emissao_co2: 0.0817      # tCO2/MWh (média Brasil)
  absorcao_arvore_ano: 163.0     # kg CO2/ano por árvore
```

## 🐛 Troubleshooting

### Erro: "Token expirado"

O sistema renova automaticamente. Se persistir:
- Verifique credenciais em `config/config.yaml`
- Teste login manual na plataforma FusionSolar

### Erro: "WeasyPrint não encontrado"

Instale dependências do sistema:
```bash
# macOS
brew install cairo pango gdk-pixbuf libffi

# Ubuntu
sudo apt-get install libcairo2 libpango-1.0-0
```

### Erro: "Estação não encontrada"

Verifique o `station_code`:
```python
api = FusionSolarAPI(username="...", password="...")
api.login()
estacoes = api.get_station_list()
for e in estacoes:
    print(e['stationCode'], e['stationName'])
```

### Logs Detalhados

Execute com `--debug`:
```bash
python main.py --debug
```

Verifique logs em: `logs/relatorios_AAAAMM.log`

## 🧪 Testes

```bash
# Instalar dependências de teste
pip install pytest pytest-cov

# Executar testes
pytest

# Com cobertura
pytest --cov=src
```

## 📝 TODO / Melhorias Futuras

- [ ] Envio automático de emails com relatórios
- [ ] Dashboard web com Flask/Django
- [ ] Suporte a múltiplos idiomas
- [ ] Comparativos anuais
- [ ] Previsão de geração com ML
- [ ] Integração com Google Drive/Dropbox
- [ ] API REST própria
- [ ] App mobile

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor

**Sua Empresa Solar**
- Website: https://suaempresa.com.br
- Email: contato@suaempresa.com.br
- Telefone: (00) 0000-0000

## 🙏 Agradecimentos

- Huawei FusionSolar pela API
- Comunidade Python
- Bibliotecas open-source utilizadas

## 📞 Suporte

Para dúvidas ou problemas:
- Abra uma [issue](https://github.com/seu-usuario/fusionsolar-relatorios/issues)
- Entre em contato: contato@suaempresa.com.br

---

**⚡ Feito com ❤️ para um futuro mais sustentável 🌱**
