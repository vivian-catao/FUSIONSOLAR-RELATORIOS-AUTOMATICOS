"""
Funções auxiliares para o sistema
Gerenciamento de logging, configurações, formatação de dados, etc.
"""

import os
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import json
import pytz


def configurar_logging(nivel: str = "INFO", arquivo_log: Optional[str] = None) -> None:
    """
    Configura o sistema de logging
    
    Args:
        nivel: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        arquivo_log: Caminho para arquivo de log (opcional)
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    handlers = [logging.StreamHandler()]
    
    if arquivo_log:
        # Cria diretório se não existir
        log_dir = os.path.dirname(arquivo_log)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        handlers.append(logging.FileHandler(arquivo_log, encoding='utf-8'))
    
    logging.basicConfig(
        level=getattr(logging, nivel.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=handlers
    )
    
    # Reduz verbosidade de bibliotecas externas
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)


def carregar_config(caminho: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Carrega arquivo de configuração YAML
    
    Args:
        caminho: Caminho para o arquivo config.yaml
    
    Returns:
        Dicionário com configurações
    """
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {caminho}")
    
    with open(caminho, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def carregar_clientes(caminho: str = "config/clientes.yaml") -> Dict[str, Any]:
    """
    Carrega arquivo de clientes YAML
    
    Args:
        caminho: Caminho para o arquivo clientes.yaml
    
    Returns:
        Dicionário com dados dos clientes
    """
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Arquivo de clientes não encontrado: {caminho}")
    
    with open(caminho, 'r', encoding='utf-8') as f:
        clientes = yaml.safe_load(f)
    
    return clientes


def criar_diretorios(diretorios: list) -> None:
    """
    Cria diretórios se não existirem
    
    Args:
        diretorios: Lista de caminhos de diretórios
    """
    for diretorio in diretorios:
        Path(diretorio).mkdir(parents=True, exist_ok=True)


def formatar_data_br(data: datetime) -> str:
    """
    Formata data no padrão brasileiro
    
    Args:
        data: Objeto datetime
    
    Returns:
        String formatada (ex: 01/12/2023)
    """
    return data.strftime('%d/%m/%Y')


def formatar_data_hora_br(data: datetime) -> str:
    """
    Formata data e hora no padrão brasileiro
    
    Args:
        data: Objeto datetime
    
    Returns:
        String formatada (ex: 01/12/2023 14:30:45)
    """
    return data.strftime('%d/%m/%Y %H:%M:%S')


def formatar_mes_ano(mes: int, ano: int) -> str:
    """
    Formata mês e ano por extenso
    
    Args:
        mes: Número do mês (1-12)
        ano: Ano (ex: 2023)
    
    Returns:
        String formatada (ex: Dezembro de 2023)
    """
    meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    
    if 1 <= mes <= 12:
        return f"{meses[mes - 1]} de {ano}"
    return f"{mes}/{ano}"


def formatar_moeda(valor: float) -> str:
    """
    Formata valor em moeda brasileira
    
    Args:
        valor: Valor numérico
    
    Returns:
        String formatada (ex: R$ 1.234,56)
    """
    return f"R$ {valor:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')


def formatar_numero(valor: float, casas_decimais: int = 2) -> str:
    """
    Formata número com separadores brasileiros
    
    Args:
        valor: Valor numérico
        casas_decimais: Número de casas decimais
    
    Returns:
        String formatada (ex: 1.234,56) ou "-" se valor for None
    """
    if valor is None:
        return "-"
    try:
        formato = f"{{:,.{casas_decimais}f}}"
        return formato.format(float(valor)).replace(',', '_').replace('.', ',').replace('_', '.')
    except (TypeError, ValueError):
        return "-"


def formatar_percentual(valor: float, casas_decimais: int = 1) -> str:
    """
    Formata percentual
    
    Args:
        valor: Valor numérico (ex: 85.5)
        casas_decimais: Número de casas decimais
    
    Returns:
        String formatada (ex: 85,5%) ou "-" se valor for None
    """
    if valor is None:
        return "-"
    try:
        return f"{formatar_numero(valor, casas_decimais)}%"
    except (TypeError, ValueError):
        return "-"


def salvar_json(dados: Dict, caminho: str, identar: bool = True) -> None:
    """
    Salva dados em arquivo JSON
    
    Args:
        dados: Dicionário para salvar
        caminho: Caminho do arquivo
        identar: Se deve identar o JSON
    """
    # Cria diretório se não existir
    dir_path = os.path.dirname(caminho)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2 if identar else None)


def carregar_json(caminho: str) -> Dict:
    """
    Carrega dados de arquivo JSON
    
    Args:
        caminho: Caminho do arquivo
    
    Returns:
        Dicionário com dados
    """
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Arquivo JSON não encontrado: {caminho}")
    
    with open(caminho, 'r', encoding='utf-8') as f:
        return json.load(f)


def gerar_nome_arquivo(cliente_nome: str, mes: int, ano: int, extensao: str = "pdf") -> str:
    """
    Gera nome de arquivo padronizado
    
    Args:
        cliente_nome: Nome do cliente
        mes: Mês (1-12)
        ano: Ano
        extensao: Extensão do arquivo (sem ponto)
    
    Returns:
        Nome do arquivo (ex: relatorio_cliente_202312.pdf)
    """
    # Remove caracteres especiais e espaços
    nome_limpo = cliente_nome.lower()
    nome_limpo = nome_limpo.replace(' ', '_')
    nome_limpo = ''.join(c for c in nome_limpo if c.isalnum() or c == '_')
    
    return f"relatorio_{nome_limpo}_{ano}{mes:02d}.{extensao}"


def validar_mes_ano(mes: int, ano: int) -> bool:
    """
    Valida se mês e ano são válidos
    
    Args:
        mes: Mês (1-12)
        ano: Ano
    
    Returns:
        True se válido
    """
    if not (1 <= mes <= 12):
        return False
    
    # Verifica se não é futuro
    hoje = datetime.now()
    if ano > hoje.year or (ano == hoje.year and mes > hoje.month):
        return False
    
    return True


def converter_timestamp_ms(timestamp_ms: int) -> datetime:
    """
    Converte timestamp em milissegundos para datetime
    
    Args:
        timestamp_ms: Timestamp em milissegundos
    
    Returns:
        Objeto datetime
    """
    return datetime.fromtimestamp(timestamp_ms / 1000)


def obter_timestamp_ms(data: datetime) -> int:
    """
    Converte datetime para timestamp em milissegundos
    
    Args:
        data: Objeto datetime
    
    Returns:
        Timestamp em milissegundos
    """
    return int(data.timestamp() * 1000)


def calcular_primeiro_ultimo_dia_mes(mes: int, ano: int) -> tuple:
    """
    Calcula primeiro e último dia do mês
    
    Args:
        mes: Mês (1-12)
        ano: Ano
    
    Returns:
        Tupla (primeiro_dia, ultimo_dia) como datetime
    """
    from calendar import monthrange
    
    primeiro_dia = datetime(ano, mes, 1, 0, 0, 0)
    ultimo_dia_numero = monthrange(ano, mes)[1]
    ultimo_dia = datetime(ano, mes, ultimo_dia_numero, 23, 59, 59)
    
    return primeiro_dia, ultimo_dia


def obter_mes_anterior(mes: int, ano: int) -> tuple:
    """
    Obtém mês e ano anteriores
    
    Args:
        mes: Mês atual (1-12)
        ano: Ano atual
    
    Returns:
        Tupla (mes_anterior, ano_anterior)
    """
    if mes == 1:
        return 12, ano - 1
    return mes - 1, ano


def obter_timezone_brasil() -> pytz.timezone:
    """
    Retorna timezone de São Paulo (Brasil)
    
    Returns:
        Timezone pytz para America/Sao_Paulo
    """
    return pytz.timezone('America/Sao_Paulo')


def converter_para_timezone_brasil(data: datetime) -> datetime:
    """
    Converte datetime para timezone do Brasil
    
    Args:
        data: Objeto datetime (pode ser naive ou aware)
    
    Returns:
        Datetime com timezone America/Sao_Paulo
    """
    tz_brasil = obter_timezone_brasil()
    
    # Se já tem timezone, converte
    if data.tzinfo is not None:
        return data.astimezone(tz_brasil)
    
    # Se não tem timezone (naive), assume UTC e converte
    data_utc = pytz.utc.localize(data)
    return data_utc.astimezone(tz_brasil)


def obter_data_hora_atual_brasil() -> datetime:
    """
    Retorna data e hora atual no timezone do Brasil
    
    Returns:
        Datetime atual em America/Sao_Paulo
    """
    return datetime.now(obter_timezone_brasil())


def formatar_data_extenso(data: datetime) -> str:
    """
    Formata data por extenso em português
    
    Args:
        data: Objeto datetime
    
    Returns:
        String formatada (ex: 01 de Dezembro de 2023)
    """
    meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    
    return f"{data.day:02d} de {meses[data.month - 1]} de {data.year}"

