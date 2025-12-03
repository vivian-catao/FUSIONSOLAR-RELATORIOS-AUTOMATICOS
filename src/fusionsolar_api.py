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
        
    def _is_token_valid(self) -> bool:
        """Verifica se o token ainda é válido"""
        if not self.token or not self.token_expiry:
            return False
        return datetime.now() < self.token_expiry
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     retry_count: int = 3) -> Dict[str, Any]:
        """
        Faz requisição à API com retry logic
        
        Args:
            method: GET ou POST
            endpoint: Endpoint da API (ex: /thirdData/login)
            data: Payload JSON (para POST)
            retry_count: Número de tentativas em caso de falha
            
        Returns:
            Resposta JSON da API
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(retry_count):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, params=data, timeout=30)
                else:
                    response = self.session.post(url, json=data, timeout=30)
                
                response.raise_for_status()
                result = response.json()
                
                # Verifica se a API retornou erro
                if not result.get('success', False):
                    error_msg = result.get('message', 'Erro desconhecido')
                    logger.error(f"API retornou erro: {error_msg}")
                    
                    # Se for erro de autenticação, tenta relogar
                    if 'token' in error_msg.lower() or 'auth' in error_msg.lower():
                        logger.info("Token expirado, refazendo login...")
                        self.login()
                        continue
                    
                    raise Exception(f"Erro na API: {error_msg}")
                
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
        
        # API FusionSolar usa senha hasheada
        password_hash = hashlib.sha256(self.password.encode()).hexdigest()
        
        data = {
            "userName": self.username,
            "systemCode": password_hash
        }
        
        try:
            result = self._make_request('POST', '/thirdData/login', data, retry_count=1)
            
            if result.get('success'):
                self.token = result.get('data')
                # Token válido por 30 minutos (margem de segurança de 5 min)
                self.token_expiry = datetime.now() + timedelta(minutes=25)
                
                # Adiciona token ao header
                self.session.headers.update({'XSRF-TOKEN': self.token})
                
                logger.info("Login realizado com sucesso!")
                return True
            else:
                logger.error(f"Falha no login: {result.get('message')}")
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
            Dicionário com dados em tempo real
        """
        self._ensure_authenticated()
        logger.info(f"Buscando dados em tempo real da estação {station_code}...")
        
        data = {"stationCodes": station_code}
        result = self._make_request('POST', '/thirdData/getStationRealKpi', data)
        
        return result.get('data', [{}])[0] if result.get('data') else {}
    
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
    
    def get_station_month_kpi(self, station_code: str, collect_time: str) -> Dict:
        """
        Obtém KPIs mensais de uma estação
        
        Args:
            station_code: Código da estação
            collect_time: Mês no formato YYYYMM (ex: 202311)
            
        Returns:
            Dicionário com KPIs do mês
        """
        self._ensure_authenticated()
        logger.info(f"Buscando KPIs mensais de {station_code} para {collect_time}...")
        
        data = {
            "stationCodes": station_code,
            "collectTime": int(collect_time)
        }
        
        result = self._make_request('POST', '/thirdData/getKpiStationMonth', data)
        return result.get('data', [{}])[0] if result.get('data') else {}
    
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
