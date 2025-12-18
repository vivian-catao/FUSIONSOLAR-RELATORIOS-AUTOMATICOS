#!/usr/bin/env python3
"""
Script principal para geração de relatórios FusionSolar
Suporta processamento de múltiplos clientes e períodos
"""

import argparse
import sys
import os
from datetime import datetime

# Adiciona diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.fusionsolar_api import FusionSolarAPI
from src.extrator_dados import ExtratorDados
from src.gerador_relatorio import GeradorRelatorio
from src.utils import (
    configurar_logging,
    carregar_config,
    carregar_clientes,
    criar_diretorios,
    validar_mes_ano,
    gerar_nome_arquivo,
    salvar_json
)


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Gera relatórios mensais de energia solar da API FusionSolar',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  # Gerar relatório do mês atual para todos os clientes
  python main.py
  
  # Gerar relatório de um mês específico
  python main.py --mes 11 --ano 2023
  
  # Gerar para um cliente específico
  python main.py --cliente CLIENTE001 --mes 12 --ano 2023
  
  # Salvar dados intermediários em JSON
  python main.py --salvar-json
        """
    )
    
    parser.add_argument(
        '--mes',
        type=int,
        help='Mês (1-12). Padrão: mês anterior ao atual'
    )
    
    parser.add_argument(
        '--ano',
        type=int,
        help='Ano (ex: 2023). Padrão: ano atual'
    )
    
    parser.add_argument(
        '--cliente',
        type=str,
        help='Código do cliente específico (se omitido, processa todos)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Caminho para arquivo de configuração (padrão: config/config.yaml)'
    )
    
    parser.add_argument(
        '--clientes',
        type=str,
        default='config/clientes.yaml',
        help='Caminho para arquivo de clientes (padrão: config/clientes.yaml)'
    )
    
    parser.add_argument(
        '--salvar-json',
        action='store_true',
        help='Salvar dados intermediários em JSON'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Ativar modo debug (logs detalhados)'
    )
    
    parser.add_argument(
        '--sem-diarios',
        action='store_true',
        help='Desativar busca de dados diários (gera relatório apenas com totais mensais)'
    )
    
    args = parser.parse_args()
    
    # Define mês/ano padrão (mês anterior)
    hoje = datetime.now()
    if args.mes is None:
        mes = hoje.month - 1 if hoje.month > 1 else 12
        ano = args.ano or (hoje.year if hoje.month > 1 else hoje.year - 1)
    else:
        mes = args.mes
        ano = args.ano or hoje.year
    
    # Valida mês/ano
    if not validar_mes_ano(mes, ano):
        print(f"❌ Erro: Mês/ano inválido ou futuro: {mes}/{ano}")
        sys.exit(1)
    
    # Configura logging
    nivel_log = 'DEBUG' if args.debug else 'INFO'
    arquivo_log = f'logs/relatorios_{ano}{mes:02d}.log'
    configurar_logging(nivel_log, arquivo_log)
    
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 70)
    logger.info("SISTEMA DE GERAÇÃO DE RELATÓRIOS FUSIONSOLAR")
    logger.info("=" * 70)
    logger.info(f"Período: {mes:02d}/{ano}")
    
    try:
        # Carrega configurações
        logger.info("Carregando configurações...")
        config = carregar_config(args.config)
        
        # Cria diretórios necessários
        criar_diretorios(['output/relatorios', 'output/dados', 'logs'])
        
        # Inicializa API
        logger.info("Conectando à API FusionSolar...")
        api = FusionSolarAPI(
            username=config['fusionsolar']['username'],
            password=config['fusionsolar']['password'],
            base_url=config['fusionsolar']['base_url']
        )
        
        # Faz login
        if not api.login():
            logger.error("Falha na autenticação!")
            sys.exit(1)
        
        # Inicializa extrator e gerador
        extrator = ExtratorDados(api)
        gerador = GeradorRelatorio(config)
        
        # Carrega lista de clientes
        logger.info("Carregando lista de clientes...")
        dados_clientes = carregar_clientes(args.clientes)
        
        # Filtra cliente específico se informado
        if args.cliente:
            clientes_processar = [
                c for c in dados_clientes['clientes'] 
                if c.get('station_code') == args.cliente
            ]
            if not clientes_processar:
                logger.error(f"Cliente {args.cliente} não encontrado!")
                sys.exit(1)
        else:
            clientes_processar = dados_clientes['clientes']
        
        logger.info(f"Total de clientes a processar: {len(clientes_processar)}")
        
        # Processa cada cliente
        sucesso = 0
        falhas = 0
        
        for i, cliente in enumerate(clientes_processar, 1):
            station_code = cliente['station_code']
            nome_cliente = cliente['nome']
            
            logger.info("")
            logger.info("-" * 70)
            logger.info(f"[{i}/{len(clientes_processar)}] Processando: {nome_cliente}")
            logger.info("-" * 70)
            
            try:
                # Extrai dados
                # Por padrão busca dados diários (é eficiente: 1 chamada só)
                buscar_diarios = not args.sem_diarios
                
                if buscar_diarios:
                    logger.info("📊 Busca de dados diários ATIVADA (1 chamada à API)")
                else:
                    logger.info("⚠️  Busca de dados diários DESATIVADA")
                
                logger.info("Extraindo dados da API...")
                dados = extrator.comparar_com_mes_anterior(
                    station_code=station_code,
                    mes=mes,
                    ano=ano,
                    potencia_kwp=cliente.get('potencia_kwp'),
                    buscar_diarios=buscar_diarios
                )
                
                # Adiciona informações do cliente
                dados['cliente'] = {
                    'nome': nome_cliente,
                    'email': cliente.get('email'),
                    'telefone': cliente.get('telefone'),
                    'contato': cliente.get('contato')
                }
                
                # Salva JSON se solicitado
                if args.salvar_json:
                    json_path = os.path.join(
                        'output/dados',
                        gerar_nome_arquivo(nome_cliente, mes, ano, 'json')
                    )
                    logger.info(f"Salvando dados em JSON: {json_path}")
                    salvar_json(dados, json_path)
                
                # Gera PDF
                pdf_path = os.path.join(
                    'output/relatorios',
                    gerar_nome_arquivo(nome_cliente, mes, ano, 'pdf')
                )
                logger.info(f"Gerando relatório PDF: {pdf_path}")
                gerador.gerar_relatorio(dados, pdf_path)
                
                logger.info(f"✅ Relatório gerado com sucesso!")
                logger.info(f"   📄 {pdf_path}")
                logger.info(f"   ⚡ Geração: {dados['geracao']['total_kwh']:.2f} kWh")
                logger.info(f"   💰 Economia: R$ {dados['economia']['economia_mensal']:.2f}")
                
                sucesso += 1
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar {nome_cliente}: {e}", exc_info=args.debug)
                falhas += 1
        
        # Logout
        api.logout()
        
        # Resumo final
        logger.info("")
        logger.info("=" * 70)
        logger.info("RESUMO DA EXECUÇÃO")
        logger.info("=" * 70)
        logger.info(f"✅ Sucessos: {sucesso}")
        logger.info(f"❌ Falhas: {falhas}")
        logger.info(f"📁 Relatórios salvos em: output/relatorios/")
        if args.salvar_json:
            logger.info(f"📊 Dados JSON salvos em: output/dados/")
        logger.info("=" * 70)
        
        # Exit code
        sys.exit(0 if falhas == 0 else 1)
        
    except FileNotFoundError as e:
        logger.error(f"❌ Arquivo não encontrado: {e}")
        logger.error("   Certifique-se de criar os arquivos de configuração:")
        logger.error("   - config/config.yaml (baseado em config.yaml.example)")
        logger.error("   - config/clientes.yaml (baseado em clientes.yaml.example)")
        sys.exit(1)
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Processo interrompido pelo usuário")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}", exc_info=args.debug)
        sys.exit(1)


if __name__ == '__main__':
    main()
