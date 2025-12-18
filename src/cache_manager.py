"""
Gerenciador de cache para respostas da API FusionSolar
Reduz chamadas à API e evita rate limiting durante desenvolvimento/testes
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheManager:
    """Gerencia cache de respostas da API em arquivos JSON"""
    
    def __init__(self, cache_dir: str = ".cache", ttl_hours: int = 24):
        """
        Inicializa o gerenciador de cache
        
        Args:
            cache_dir: Diretório onde os arquivos de cache serão salvos
            ttl_hours: Tempo de vida do cache em horas (padrão: 24h)
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_hours * 3600
        self.enabled = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
        
        if self.enabled:
            self.cache_dir.mkdir(exist_ok=True)
            logger.info(f"Cache habilitado: {self.cache_dir.absolute()} (TTL: {ttl_hours}h)")
        else:
            logger.info("Cache desabilitado")
    
    def _generate_key(self, endpoint: str, params: Dict) -> str:
        """
        Gera chave única para o cache baseada no endpoint e parâmetros
        
        Args:
            endpoint: Nome do endpoint da API
            params: Parâmetros da requisição
            
        Returns:
            Hash MD5 como chave do cache
        """
        # Serializa params de forma determinística
        params_str = json.dumps(params, sort_keys=True)
        key_str = f"{endpoint}:{params_str}"
        
        # Gera hash MD5
        hash_obj = hashlib.md5(key_str.encode())
        return hash_obj.hexdigest()
    
    def _get_cache_path(self, key: str) -> Path:
        """Retorna o caminho do arquivo de cache para uma chave"""
        return self.cache_dir / f"{key}.json"
    
    def _is_expired(self, cache_data: Dict) -> bool:
        """Verifica se o cache expirou"""
        if 'timestamp' not in cache_data:
            return True
        
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        elapsed = (datetime.now() - cache_time).total_seconds()
        
        return elapsed > self.ttl_seconds
    
    def get(self, endpoint: str, params: Dict) -> Optional[Any]:
        """
        Obtém dados do cache se disponível e válido
        
        Args:
            endpoint: Nome do endpoint da API
            params: Parâmetros da requisição
            
        Returns:
            Dados em cache ou None se não houver/expirado
        """
        if not self.enabled:
            return None
        
        key = self._generate_key(endpoint, params)
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            logger.debug(f"Cache miss: {endpoint}")
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            if self._is_expired(cache_data):
                logger.debug(f"Cache expirado: {endpoint}")
                cache_path.unlink()  # Remove cache expirado
                return None
            
            logger.debug(f"Cache hit: {endpoint}")
            return cache_data.get('data')
            
        except Exception as e:
            logger.warning(f"Erro ao ler cache: {e}")
            return None
    
    def set(self, endpoint: str, params: Dict, data: Any) -> None:
        """
        Armazena dados no cache
        
        Args:
            endpoint: Nome do endpoint da API
            params: Parâmetros da requisição
            data: Dados a serem armazenados
        """
        if not self.enabled:
            return
        
        key = self._generate_key(endpoint, params)
        cache_path = self._get_cache_path(key)
        
        cache_data = {
            'endpoint': endpoint,
            'params': params,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Cache salvo: {endpoint}")
            
        except Exception as e:
            logger.warning(f"Erro ao salvar cache: {e}")
    
    def clear(self, older_than_hours: Optional[int] = None) -> int:
        """
        Limpa arquivos de cache
        
        Args:
            older_than_hours: Se especificado, remove apenas caches mais antigos que X horas
            
        Returns:
            Número de arquivos removidos
        """
        if not self.enabled or not self.cache_dir.exists():
            return 0
        
        removed = 0
        cutoff_time = None
        
        if older_than_hours is not None:
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                if cutoff_time:
                    # Verifica timestamp do arquivo
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    cache_time = datetime.fromisoformat(cache_data.get('timestamp', '2000-01-01'))
                    
                    if cache_time >= cutoff_time:
                        continue  # Não remove este
                
                cache_file.unlink()
                removed += 1
                
            except Exception as e:
                logger.warning(f"Erro ao processar {cache_file}: {e}")
        
        logger.info(f"Cache limpo: {removed} arquivo(s) removido(s)")
        return removed
    
    def stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        if not self.enabled or not self.cache_dir.exists():
            return {
                'enabled': self.enabled,
                'total_files': 0,
                'total_size_mb': 0
            }
        
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'enabled': self.enabled,
            'cache_dir': str(self.cache_dir.absolute()),
            'total_files': len(cache_files),
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'ttl_hours': self.ttl_seconds / 3600
        }
