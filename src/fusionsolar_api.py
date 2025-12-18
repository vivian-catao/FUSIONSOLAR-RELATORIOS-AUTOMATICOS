"""
Cliente da API FusionSolar (Huawei)
Gerencia autenticação, requisições e tokens automaticamente
"""

import requests
import hashlib
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .cache_manager import CacheManager


logger = logging.getLogger(__name__)


class FusionSolarAPI:
    """Cliente para interagir com a API FusionSolar da Huawei"""
    
    def __init__(self, username: str, password: str, base_url: str = "https://intl.fusionsolar.huawei.com"):
        """
        Inicializa o cliente da API
        
        Args:
            username: Nome de usuário da conta FusionSolar
            password: Senha da conta
            base_url: URL base da API (padrão internacional)
        """
        self.username = username
        self.password = password
        self.base_url = base_url.rstrip('/')
        self.token = None
        self.token_expiry = None
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Connection': 'keep-alive'
        })
        
        # Inicializa cache manager
        self.cache = CacheManager(cache_dir=".cache/fusionsolar", ttl_hours=24)
        
    def _is_token_valid(self) -> bool:
        """Verifica se o token ainda é válido"""
        if not self.token or not self.token_expiry:
            return False
        return datetime.now() < self.token_expiry
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     retry_count: int = 3, use_cache: bool = True) -> Dict[str, Any]:
        """
        Faz requisição à API com retry logic e cache
        
        Args:
            method: GET ou POST
            endpoint: Endpoint da API (ex: /thirdData/login)
            data: Payload JSON (para POST)
            retry_count: Número de tentativas em caso de falha
            use_cache: Se True, tenta usar cache antes de chamar API
            
        Returns:
            Resposta JSON da API
        """
        # Tenta buscar do cache primeiro (exceto login/logout)
        if use_cache and endpoint not in ['/thirdData/login', '/thirdData/logout']:
            cached = self.cache.get(endpoint, data or {})
            if cached is not None:
                return cached
        
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(retry_count):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, params=data, timeout=30)
                else:
                    response = self.session.post(url, json=data, timeout=30)
                
                response.raise_for_status()
                try:
                    result = response.json()
                except ValueError:
                    # Resposta não-JSON (HTML ou outro). Log completo para debugging.
                    text = response.text[:1000]
                    logger.error(f"Resposta não-JSON do endpoint {endpoint}: HTTP {response.status_code} - {text}")
                    raise Exception(f"Resposta inválida do servidor: HTTP {response.status_code}")

                # Verifica se a API retornou erro
                success = result.get('success', False)
                if not success:
                    # Normaliza mensagem e failCode
                    fail_code = result.get('failCode')
                    error_msg = result.get('message') if isinstance(result.get('message'), str) else str(result.get('message') or '')
                    logger.error(f"API retornou erro (failCode={fail_code}): {error_msg}")

                    # Se for erro de autenticação, tenta relogar
                    lower_msg = error_msg.lower() if error_msg else ''
                    if 'token' in lower_msg or 'auth' in lower_msg:
                        logger.info("Token expirado, refazendo login...")
                        self.login()
                        continue

                    # Propaga erro com código quando disponível
                    if fail_code is not None:
                        raise Exception(f"Erro na API (failCode={fail_code}): {error_msg}")
                    raise Exception(f"Erro na API: {error_msg or 'Erro desconhecido'}")

                # Salva no cache (exceto login/logout)
                if use_cache and endpoint not in ['/thirdData/login', '/thirdData/logout']:
                    self.cache.set(endpoint, data or {}, result)
                
                return result
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Tentativa {attempt + 1}/{retry_count} falhou: {e}")
                if attempt == retry_count - 1:
                    raise
                time.sleep(2 ** attempt)  # Backoff exponencial
        
        raise Exception(f"Falha após {retry_count} tentativas")
    
    def login(self) -> bool:
        """
        Realiza login e obtém token de autenticação
        
        Returns:
            True se login for bem-sucedido
        """
        logger.info(f"Fazendo login como {self.username}...")
        
        # API FusionSolar usa senha em plain text (conforme documentação NBI)
        data = {
            "userName": self.username,
            "systemCode": self.password
        }
        
        try:
            # Faz requisição diretamente para capturar o header XSRF-TOKEN
            url = f"{self.base_url}/thirdData/login"
            response = self.session.post(url, json=data, timeout=30)
            result = response.json()
            
            if result.get('success'):
                # Token vem no header da resposta, não no body
                self.token = response.headers.get('XSRF-TOKEN') or response.headers.get('xsrf-token')
                
                if not self.token:
                    # Fallback: alguns servidores retornam no body
                    self.token = result.get('data')
                
                # Token válido por 30 minutos (margem de segurança de 5 min)
                self.token_expiry = datetime.now() + timedelta(minutes=25)
                
                # Adiciona token ao header para próximas requisições
                self.session.headers.update({'XSRF-TOKEN': self.token})
                
                logger.info("Login realizado com sucesso!")
                return True
            else:
                error_msg = result.get('message', 'Erro desconhecido')
                fail_code = result.get('failCode')
                
                if fail_code == 407:
                    logger.error("Rate limit atingido. Aguarde 10 minutos.")
                elif fail_code == 20400:
                    logger.error("Usuário ou senha inválidos.")
                else:
                    logger.error(f"Falha no login: {error_msg}")
                    
                return False
                
        except Exception as e:
            logger.error(f"Erro ao fazer login: {e}")
            raise
    
    def _ensure_authenticated(self):
        """Garante que há um token válido antes de fazer requisições"""
        if not self._is_token_valid():
            self.login()
    
    def get_station_list(self) -> List[Dict]:
        """
        Obtém lista de todas as estações (usinas) da conta
        
        Returns:
            Lista de dicionários com dados das estações
        """
        self._ensure_authenticated()
        logger.info("Buscando lista de estações...")
        
        data = {
            "pageNo": 1,
            "pageSize": 100
        }
        
        result = self._make_request('POST', '/thirdData/getStationList', data)
        stations = result.get('data', {}).get('list', [])
        
        logger.info(f"Encontradas {len(stations)} estações")
        return stations
    
    def get_station_realtime_data(self, station_code: str) -> Dict:
        """
        Obtém dados em tempo real de uma estação
        
        Args:
            station_code: Código da estação
            
        Returns:
            Dicionário com dados em tempo real (vazio se rate limit ou erro)
        """
        self._ensure_authenticated()
        logger.info(f"Buscando dados em tempo real da estação {station_code}...")
        
        data = {"stationCodes": station_code}
        
        try:
            result = self._make_request('POST', '/thirdData/getStationRealKpi', data)
            return result.get('data', [{}])[0] if result.get('data') else {}
        except Exception as e:
            logger.warning(f"Erro ao obter dados realtime (rate limit?): {e}")
            return {}
    
    def get_station_day_kpi(self, station_code: str, collect_time: str) -> Dict:
        """
        Obtém KPIs diários de uma estação
        
        Args:
            station_code: Código da estação
            collect_time: Data no formato YYYYMMDD (ex: 20231201)
            
        Returns:
            Dicionário com KPIs do dia
        """
        self._ensure_authenticated()
        logger.info(f"Buscando KPIs diários de {station_code} para {collect_time}...")
        
        data = {
            "stationCodes": station_code,
            "collectTime": int(collect_time)
        }
        
        result = self._make_request('POST', '/thirdData/getKpiStationDay', data)
        return result.get('data', [{}])[0] if result.get('data') else {}
    
    def get_station_month_daily_kpi(self, station_code: str, ano: int, mes: int) -> List[Dict]:
        """
        Obtém KPIs diários de TODOS os dias de um mês em uma única chamada.
        
        Este é o método correto para obter dados diários históricos sem 
        estourar o rate limit. Usa timestamp em milissegundos do primeiro 
        dia do mês, e a API retorna todos os dias.
        
        Args:
            station_code: Código da estação
            ano: Ano (ex: 2025)
            mes: Mês (ex: 11)
            
        Returns:
            Lista de dicionários com KPIs de cada dia do mês
        """
        self._ensure_authenticated()
        logger.info(f"Buscando KPIs diários do mês {mes:02d}/{ano} da estação {station_code}...")
        
        # A API espera timestamp em milissegundos do primeiro dia do mês
        primeiro_dia = datetime(ano, mes, 1, 0, 0, 0)
        timestamp_ms = int(primeiro_dia.timestamp() * 1000)
        
        data = {
            "stationCodes": station_code,
            "collectTime": timestamp_ms
        }
        
        result = self._make_request('POST', '/thirdData/getKpiStationDay', data)
        dados = result.get('data', [])
        
        logger.info(f"Retornados {len(dados)} dias de dados")
        return dados
    
    def get_station_month_kpi(self, station_code: str, collect_time: str) -> Dict:
        """
        Obtém KPIs mensais de uma estação
        
        Args:
            station_code: Código da estação
            collect_time: Mês no formato YYYYMM (ex: 202311)
            
        Returns:
            Dicionário com KPIs do mês (vazio se rate limit ou erro)
        """
        self._ensure_authenticated()
        logger.info(f"Buscando KPIs mensais de {station_code} para {collect_time}...")
        
        data = {
            "stationCodes": station_code,
            "collectTime": int(collect_time)
        }
        
        try:
            result = self._make_request('POST', '/thirdData/getKpiStationMonth', data)
            return result.get('data', [{}])[0] if result.get('data') else {}
        except Exception as e:
            # Se falhar (rate limit, etc), retorna vazio para permitir fallback
            logger.warning(f"Erro ao obter KPI mensal (será usado fallback): {e}")
            return {}
    
    def get_station_hour_kpi(self, station_code: str, collect_time: str) -> List[Dict]:
        """
        Obtém KPIs por hora de uma estação para um dia específico
        
        Args:
            station_code: Código da estação
            collect_time: Data no formato YYYYMMDD
            
        Returns:
            Lista com KPIs de cada hora do dia
        """
        self._ensure_authenticated()
        logger.info(f"Buscando KPIs por hora de {station_code} para {collect_time}...")
        
        data = {
            "stationCodes": station_code,
            "collectTime": int(collect_time)
        }
        
        result = self._make_request('POST', '/thirdData/getKpiStationHour', data)
        return result.get('data', [])
    
    def get_device_list(self, station_code: str) -> List[Dict]:
        """
        Obtém lista de dispositivos de uma estação
        
        Args:
            station_code: Código da estação
            
        Returns:
            Lista de dispositivos (inversores, strings, etc)
        """
        self._ensure_authenticated()
        logger.info(f"Buscando dispositivos da estação {station_code}...")
        
        data = {"stationCodes": station_code}
        result = self._make_request('POST', '/thirdData/getDevList', data)
        
        return result.get('data', [])
    
    def get_device_realtime_kpi(self, device_id: str, device_type_id: int = 1) -> Dict:
        """
        Obtém KPIs em tempo real de um dispositivo específico (inversor, medidor, etc.)
        
        Args:
            device_id: ID do dispositivo
            device_type_id: Tipo do dispositivo (1=Inversor String, 38=Inversor Residencial, etc.)
            
        Returns:
            Dicionário com KPIs em tempo real do dispositivo
        """
        self._ensure_authenticated()
        logger.info(f"Buscando KPIs em tempo real do dispositivo {device_id}...")
        
        data = {
            "devIds": device_id,
            "devTypeId": device_type_id
        }
        
        try:
            result = self._make_request('POST', '/thirdData/getDevRealKpi', data)
            return result.get('data', [{}])[0] if result.get('data') else {}
        except Exception as e:
            logger.warning(f"Erro ao obter KPI do dispositivo {device_id}: {e}")
            return {}
    
    def get_alarm_list(self, station_code: str, begin_time: int, end_time: int) -> List[Dict]:
        """
        Obtém lista de alarmes de uma estação
        
        Args:
            station_code: Código da estação
            begin_time: Timestamp início (milissegundos)
            end_time: Timestamp fim (milissegundos)
            
        Returns:
            Lista de alarmes
        """
        self._ensure_authenticated()
        logger.info(f"Buscando alarmes de {station_code}...")
        
        data = {
            "stationCodes": station_code,
            "beginTime": begin_time,
            "endTime": end_time,
            "language": "pt_BR"
        }
        
        result = self._make_request('POST', '/thirdData/getAlarmList', data)
        return result.get('data', [])
    
    def logout(self):
        """Encerra sessão e limpa token"""
        if self.token:
            try:
                self._make_request('POST', '/thirdData/logout', retry_count=1)
            except Exception as e:
                logger.warning(f"Erro ao fazer logout: {e}")
            finally:
                self.token = None
                self.token_expiry = None
                logger.info("Logout realizado")
