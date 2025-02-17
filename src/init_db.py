# src/init_db.py
from datetime import datetime, timedelta
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_project():
    """Initialise le projet avec les données nécessaires"""
    from src.database.operations import DatabaseManager
    from src.data.processor import DataProcessor
    from src.config import config
    
    try:
        # Création des répertoires nécessaires
        logger.info("Création des répertoires...")
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Initialisation de la base de données
        logger.info("Initialisation de la base de données...")
        db = DatabaseManager()
        db._init_database()
        
        # Collecte des données historiques
        logger.info("Collecte des données historiques...")
        collector = DataProcessor()
        collector._collect_latest_data_async(
            timeframe="1H",
        )
        
        logger.info("Initialisation terminée avec succès!")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation: {e}")
        raise

if __name__ == "__main__":
    init_project()