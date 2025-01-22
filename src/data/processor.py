# src/data/processor.py
from datetime import datetime, timedelta
import logging
from typing import List, Optional, Dict
import polars as pl
import asyncio
from ..database.operations import DatabaseManager
from ..database.models import BitcoinPrice
from .coinbase import CoinbaseClient

logger = logging.getLogger(__name__)

class DataProcessor:
    """Processeur des données pour l'analyse"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.client = CoinbaseClient()
        self._cache = {}  # {timeframe: (timestamp, DataFrame)}
    
    async def _collect_latest_data_async(self, timeframe: str) -> List[BitcoinPrice]:
        """Collecte les dernières données depuis l'API"""
        try:
            interval_map = {
                "1m": 60,    # 60 secondes
                "5m": 300,   # 5 minutes
                "1H": 3600,  # 1 heure
                "6H": 21600, # 6 heures
                "1D": 86400, # 1 jour
                "1W": 604800 # 1 semaine
            }
            granularity = interval_map[timeframe]
            
            start_time = datetime.utcnow() - timedelta(minutes=5)
            latest_data = await self.client.get_historical_rates(
                start_time=start_time,
                granularity=granularity
            )
            
            if latest_data:
                logger.debug(f"Nouvelles données collectées : {len(latest_data)} points")
            return latest_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des données : {e}")
            return []
    
    def _get_interval(self, data: pl.DataFrame) -> int:
        """Calcule l'intervalle en minutes entre les points de données"""
        if data.is_empty():
            return 1  # Par défaut 1 minute
            
        # Calculer la différence médiane entre les timestamps
        diff = data['timestamp'].diff()
        if diff.is_empty():
            return 1
            
        # Convertir en minutes
        try:
            interval = int(diff.median().total_seconds() / 60)
            return max(1, interval)  # Au minimum 1 minute
        except:
            return 1  # Par défaut 1 minute si erreur
    
    def _get_window_size(self, timeframe: str) -> timedelta:
        """Calcule la taille de la fenêtre pour un timeframe donné"""
        interval_map = {
            "1m": timedelta(hours=1),   # 60 points
            "5m": timedelta(hours=5),   # 60 points
            "1H": timedelta(days=2.5),  # 60 points
            "6H": timedelta(days=15),   # 60 points
            "1D": timedelta(days=60),   # 60 points
            "1W": timedelta(days=420)   # 60 points
        }
        return interval_map[timeframe]
    
    async def get_ohlcv_data(
        self,
        timeframe: str = "1m",
        use_cache: bool = True
    ) -> pl.DataFrame:
        """
        Récupère les données OHLCV selon le timeframe demandé
        """
        try:
            # 1. Vérifier le cache
            cache_key = timeframe
            if use_cache and cache_key in self._cache:
                timestamp, data = self._cache[cache_key]
                if datetime.utcnow() - timestamp < timedelta(seconds=10):
                    return data
            
            # 2. Calculer la fenêtre temporelle
            window_size = self._get_window_size(timeframe)
            start_time = datetime.utcnow() - window_size
            
            # 3. Collecter les nouvelles données
            latest_data = await self._collect_latest_data_async(timeframe)
            if latest_data:
                await self.db.insert_prices_async(latest_data)
                logger.info(f"Données mises à jour : {len(latest_data)} points")
            
            # 4. Récupérer les données depuis la base
            data = await self.db.get_prices_async(start_time=start_time)
            
            if data.is_empty():
                logger.error("Aucune donnée disponible")
                return pl.DataFrame()
            
            # 5. Agréger les données si nécessaire
            if timeframe != "1m":
                interval_map = {
                    "1m": 1,
                    "5m": 5,
                    "1H": 60,
                    "6H": 360,
                    "1D": 1440,
                    "1W": 10080
                }
                interval = interval_map[timeframe]
                
                # Arrondir les timestamps à l'intervalle
                data = data.with_columns([
                    (pl.col("timestamp")
                     .dt.truncate(f"{interval}m"))
                    .alias("time_bin")
                ]).group_by("time_bin").agg([
                    pl.col("open").first().alias("open"),
                    pl.col("high").max().alias("high"),
                    pl.col("low").min().alias("low"),
                    pl.col("close").last().alias("close"),
                    pl.col("volume").sum().alias("volume"),
                    pl.col("trades").sum().alias("trades")
                ]).sort("time_bin").rename({"time_bin": "timestamp"})
                
            # 6. Mettre à jour le cache
            self._cache[cache_key] = (datetime.utcnow(), data)
            
            logger.info(f"Données prêtes : {len(data)} points")
            return data
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement des données : {e}")
            return pl.DataFrame()
    
    async def cleanup_old_data(self):
        """Nettoie les anciennes données"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=30)
            await self.db.clean_old_data_async(cutoff_time)
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des données : {e}")
    
    def __del__(self):
        """Nettoyage à la destruction"""
        self._cache.clear()