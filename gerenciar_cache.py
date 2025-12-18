#!/usr/bin/env python3
"""
Utilitário para gerenciar cache da API FusionSolar
"""

import sys
import argparse
from pathlib import Path
from src.cache_manager import CacheManager


def main():
    parser = argparse.ArgumentParser(description='Gerenciador de cache da API FusionSolar')
    parser.add_argument('action', choices=['stats', 'clear', 'clear-old'],
                       help='Ação a executar')
    parser.add_argument('--hours', type=int, default=24,
                       help='Para clear-old: remove cache mais antigo que X horas (padrão: 24)')
    
    args = parser.parse_args()
    
    cache = CacheManager(cache_dir=".cache/fusionsolar", ttl_hours=24)
    
    if args.action == 'stats':
        stats = cache.stats()
        print("\n" + "="*60)
        print("📊 ESTATÍSTICAS DO CACHE")
        print("="*60)
        print(f"Status: {'✅ Habilitado' if stats['enabled'] else '❌ Desabilitado'}")
        if stats['enabled']:
            print(f"Diretório: {stats.get('cache_dir', 'N/A')}")
            print(f"Arquivos: {stats['total_files']}")
            print(f"Tamanho: {stats['total_size_mb']} MB")
            print(f"TTL: {stats['ttl_hours']} horas")
        print("="*60)
        
    elif args.action == 'clear':
        if not cache.enabled:
            print("❌ Cache desabilitado (CACHE_ENABLED=false)")
            return 1
        
        confirm = input("⚠️  Deseja limpar TODO o cache? (s/N): ")
        if confirm.lower() == 's':
            removed = cache.clear()
            print(f"✅ {removed} arquivo(s) removido(s)")
        else:
            print("❌ Cancelado")
    
    elif args.action == 'clear-old':
        if not cache.enabled:
            print("❌ Cache desabilitado (CACHE_ENABLED=false)")
            return 1
        
        removed = cache.clear(older_than_hours=args.hours)
        print(f"✅ {removed} arquivo(s) mais antigos que {args.hours}h removido(s)")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
