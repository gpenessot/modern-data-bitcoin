# src/config.py
from pathlib import Path
import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv
import logging

def read_env_file():
    """Lit le fichier .env et retourne un dictionnaire nettoyé des valeurs"""
    env_file = Path(__file__).parent.parent / '.env'
    if not env_file.exists():
        return {}
    
    cleaned_vars = {}
    current_lines = env_file.read_text().splitlines()
    
    for line in current_lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            cleaned_vars[key] = value
            
    return cleaned_vars

# Lecture manuelle du fichier .env
env_vars = read_env_file()

# Configuration du logging
log_level = env_vars.get('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Config:
    """Configuration globale de l'application"""
    
    # Chemins
    PROJECT_ROOT: Path = field(default=Path(__file__).parent.parent)
    DATA_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data")
    DATABASE_PATH: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data" / "bitcoin.duckdb")
    
    # API Coinbase
    COINBASE_API_URL: str = field(default="https://api.exchange.coinbase.com")
    
    # Paramètres de collecte
    FETCH_INTERVAL: int = field(default=60)
    MAX_RETRIES: int = field(default=3)
    RETRY_DELAY: int = field(default=5)
    
    # Configuration serveur
    HOST: str = field(default="localhost")
    PORT: int = field(default=8026)
    
    # Paramètres d'analyse
    MAX_HISTORY_DAYS: int = field(default=30)
    
    def __post_init__(self):
        """Initialisation post-création avec gestion des variables d'environnement"""
        # Création des répertoires nécessaires
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Configuration depuis les variables d'environnement nettoyées
        if env_vars:
            if 'FETCH_INTERVAL' in env_vars:
                self.FETCH_INTERVAL = int(env_vars['FETCH_INTERVAL'])
            if 'MAX_RETRIES' in env_vars:
                self.MAX_RETRIES = int(env_vars['MAX_RETRIES'])
            if 'RETRY_DELAY' in env_vars:
                self.RETRY_DELAY = int(env_vars['RETRY_DELAY'])
            if 'HOST' in env_vars:
                self.HOST = env_vars['HOST']
            if 'PORT' in env_vars:
                self.PORT = int(env_vars['PORT'])
        
        logger.info(f"Configuration chargée: HOST={self.HOST}, PORT={self.PORT}, FETCH_INTERVAL={self.FETCH_INTERVAL}")

try:
    config = Config()
except Exception as e:
    logger.error(f"Erreur lors du chargement de la configuration: {e}")
    raise