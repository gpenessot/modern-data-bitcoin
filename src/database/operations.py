# src/database/operations.py
import duckdb
import polars as pl
from datetime import datetime
from typing import List, Optional
import logging
from ..config import config
from .models import BitcoinPrice

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestionnaire des opérations de base de données"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or config.DATABASE_PATH)
        # On maintient une connexion persistante
        self.conn = duckdb.connect(self.db_path)
        self._init_database()
        logger.info(f"Base de données connectée: {self.db_path}")
    
    def _init_database(self):
        """Initialise la structure de la base de données"""
        try:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS bitcoin_prices (
                    timestamp TIMESTAMP PRIMARY KEY,
                    open DECIMAL(15,2),
                    high DECIMAL(15,2),
                    low DECIMAL(15,2),
                    close DECIMAL(15,2),
                    volume DECIMAL(20,8),
                    trades INTEGER
                );
                
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON bitcoin_prices(timestamp);
            """)
            logger.debug("Structure de la base de données vérifiée")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
            raise
    
    async def get_prices_async(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> pl.DataFrame:
        """Récupère les données de prix"""
        try:
            query = ["SELECT * FROM bitcoin_prices"]
            conditions = []
            params = []
            
            if start_time:
                conditions.append("timestamp >= ?")
                params.append(start_time)
            if end_time:
                conditions.append("timestamp <= ?")
                params.append(end_time)
            
            if conditions:
                query.append("WHERE " + " AND ".join(conditions))
            
            query.append("ORDER BY timestamp")  # Ordre chronologique
            
            if limit:
                query.append(f"LIMIT {limit}")
            
            # Exécution directe de la requête
            result = pl.from_arrow(
                self.conn.execute(" ".join(query), params).arrow()
            )
            
            if result.is_empty():
                logger.warning("Aucune donnée en base")
            else:
                logger.info(f"Données récupérées : {len(result)} points")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données : {e}")
            raise
    
    async def insert_prices_async(self, prices: List[BitcoinPrice]):
        """Insère ou met à jour les données de prix"""
        if not prices:
            return
            
        try:
            # Conversion en DataFrame Polars
            df = pl.DataFrame([
                {
                    "timestamp": p.timestamp,
                    "open": float(p.open),
                    "high": float(p.high),
                    "low": float(p.low),
                    "close": float(p.close),
                    "volume": float(p.volume),
                    "trades": p.trades
                }
                for p in prices
            ])
            
            # Insertion avec UPSERT
            self.conn.execute("""
                INSERT OR REPLACE INTO bitcoin_prices 
                SELECT * FROM df
            """)
            
            logger.info(f"Données insérées : {len(prices)} points")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'insertion des données : {e}")
            raise
    
    async def clean_old_data_async(self, older_than: datetime):
        """Supprime les données plus anciennes qu'une date donnée"""
        try:
            deleted = self.conn.execute("""
                DELETE FROM bitcoin_prices 
                WHERE timestamp < ?;
            """, [older_than]).fetchone()[0]
            
            if deleted > 0:
                logger.info(f"Données nettoyées : {deleted} points supprimés")
                
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des données : {e}")
            raise
    
    def __del__(self):
        """Ferme la connexion à la destruction de l'objet"""
        if self.conn:
            try:
                self.conn.close()
                logger.debug("Connexion à la base de données fermée")
            except:
                pass