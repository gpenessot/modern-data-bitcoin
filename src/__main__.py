# src/__main__.py
from pathlib import Path
import sys

# Ajout du répertoire parent au PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.config import config

def main():
    from src.dashboard.app import app
    print(f"Lancement de l'application sur http://{config.HOST}:{config.PORT}")
    app.run(
        host=config.HOST,
        port=config.PORT
    )

if __name__ == "__main__":
    main()