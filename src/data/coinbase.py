# src/data/coinbase.py
import aiohttp
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging
from ..config import config
from ..database.models import BitcoinPrice

logger = logging.getLogger(__name__)

class CoinbaseClient:
    """Client API asynchrone pour Coinbase"""
    
    def __init__(
        self,
        api_url: Optional[str] = None
    ):
        self.api_url = api_url or config.COINBASE_API_URL
        self.session = None
        self._lock = asyncio.Lock()
    
    async def _ensure_session(self):
        """S'assure qu'une session est disponible"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Ferme la session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        retries: int = None
    ) -> Dict[str, Any]:
        """
        Effectue une requête à l'API avec gestion des erreurs et retry
        """
        if retries is None:
            retries = config.MAX_RETRIES
            
        url = f"{self.api_url}{endpoint}"
        
        for attempt in range(retries):
            try:
                await self._ensure_session()
                
                async with self.session.request(
                    method=method,
                    url=url,
                    params=params
                ) as response:
                    response.raise_for_status()
                    return await response.json()
                    
            except aiohttp.ClientError as e:
                if attempt == retries - 1:
                    logger.error(f"Échec de la requête après {retries} tentatives: {e}")
                    raise
                
                wait_time = config.RETRY_DELAY * (2 ** attempt)  # Backoff exponentiel
                logger.warning(f"Tentative {attempt + 1} échouée, nouvel essai dans {wait_time}s")
                await asyncio.sleep(wait_time)
    
    async def get_historical_rates(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        granularity: int = 60  # 1 minute par défaut
    ) -> List[BitcoinPrice]:
        """
        Récupère les données historiques de prix de façon asynchrone
        """
        async with self._lock:  # Protection contre les appels simultanés
            endpoint = "/products/BTC-USD/candles"
            
            params = {"granularity": granularity}
            if start_time:
                params["start"] = start_time.isoformat()
            if end_time:
                params["end"] = end_time.isoformat()
            
            try:
                data = await self._make_request("GET", endpoint, params=params)
                return [BitcoinPrice.from_coinbase(candle) for candle in data]
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des données historiques: {e}")
                return []
    
    async def get_latest_price(self) -> Optional[BitcoinPrice]:
        """Récupère le dernier prix disponible de façon asynchrone"""
        async with self._lock:
            try:
                endpoint = "/products/BTC-USD/stats"
                data = await self._make_request("GET", endpoint)
                
                return BitcoinPrice(
                    timestamp=datetime.utcnow(),
                    open=float(data['open']),
                    high=float(data['high']),
                    low=float(data['low']),
                    close=float(data['last']),
                    volume=float(data['volume']),
                    trades=None
                )
            except Exception as e:
                logger.error(f"Erreur lors de la récupération du dernier prix: {e}")
                return None
    
    def __del__(self):
        """Nettoyage à la destruction de l'objet"""
        if self.session and not self.session.closed:
            asyncio.create_task(self.close())