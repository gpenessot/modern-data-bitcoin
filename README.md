# Bitcoin Real-time Analysis Dashboard

Un dashboard interactif en Python pour analyser le Bitcoin en temps réel utilisant des technologies modernes : Polars, DuckDB et Shiny.

## 🚀 Fonctionnalités

- **Suivi en temps réel** du prix, volume et variation du Bitcoin
- **Indicateurs techniques** :
  - Moyennes mobiles (SMA 20, 50, 200)
  - Bandes de Bollinger
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
- **Graphiques interactifs** avec Plotly
- **Interface utilisateur moderne** avec Shiny
- **Stockage performant** avec DuckDB
- **Traitement des données optimisé** avec Polars

## 🛠️ Technologies

- **Backend** : Python, AsyncIO
- **Interface** : Shiny for Python
- **Base de données** : DuckDB
- **Traitement des données** : Polars
- **Visualisation** : Plotly
- **API** : Coinbase

## 📦 Installation

1. Cloner le repository
```bash
git clone https://github.com/votre-username/modern-data-bitcoin.git
cd modern-data-bitcoin
```

2. Créer un environnement virtuel
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows
```

3. Installer les dépendances
```bash
pip install -r requirements.txt
```

4. Créer un fichier .env à la racine du projet
```env
HOST=localhost
PORT=8026
FETCH_INTERVAL=60
LOG_LEVEL=INFO
```

## 🚀 Démarrage

1. Initialiser la base de données
```bash
python -m src.init_db
```

2. Lancer l'application
```bash
python -m src
```

L'application sera accessible à l'adresse : http://localhost:8026

## 📊 Architecture du Projet

```
modern-data-bitcoin/
├── src/
│   ├── analysis/          # Calculs des indicateurs techniques
│   ├── dashboard/         # Interface utilisateur Shiny
│   │   ├── components/    # Composants réutilisables
│   │   └── styles/       # Fichiers CSS
│   ├── data/             # Collecte et traitement des données
│   └── database/         # Gestion de la base de données
├── data/                 # Données stockées (DuckDB)
└── tests/               # Tests unitaires et d'intégration
```

## 🔄 Flux de données

1. Collecte des données via l'API Coinbase
2. Stockage dans DuckDB
3. Traitement avec Polars
4. Calcul des indicateurs techniques
5. Affichage dans l'interface Shiny

## 📝 Licence

MIT

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## ✍️ Auteur

Créé avec ❤️ par [Gaël Penessot](https://www.linkedin.com/in/gael-penessot), auteur de [Business Intelligence with Python](https://amzn.to/42jjs1o)