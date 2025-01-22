#!/bin/bash
# setup.sh

# Installation des dépendances si nécessaire
echo "Installation des dépendances..."
uv pip install -e ".[dev]"

# Copie du fichier .env si nécessaire
if [ ! -f .env ]; then
    echo "Création du fichier .env..."
    cp .env.example .env
    echo "Pensez à configurer vos variables d'environnement dans .env"
fi

# Initialisation de la base de données
echo "Initialisation de la base de données et collecte des données..."
python -m src.init_db

echo "Configuration terminée ! Vous pouvez lancer l'application avec:"
echo "python -m src"