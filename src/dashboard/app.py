# src/dashboard/app.py
from pathlib import Path
from shiny import App, Inputs, Outputs, Session, ui, render, reactive
import plotly.graph_objects as go
from datetime import datetime, timedelta
import polars as pl
import logging
from shinywidgets import output_widget, render_widget
from ..config import config
from ..data.processor import DataProcessor
from ..analysis.indicators import TechnicalAnalysis
from .components.charts import create_price_chart, create_technical_chart
from .components.tables import create_market_summary

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Chemin vers la racine du projet
project_root = Path(__file__).parent.parent.parent

# Configuration de l'interface utilisateur
app_ui = ui.page_fluid(
    # Inclusion des styles
    ui.head_content(
        ui.include_css(project_root / "src" / "dashboard" / "styles" / "main.css"),
        ui.tags.link(rel="preconnect", href="https://fonts.googleapis.com"),
        ui.tags.link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin="anonymous"),
        ui.tags.link(href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap", rel="stylesheet")
    ),
    
    # En-tête
    ui.h2("Bitcoin Real-time Analysis", class_="panel-title"),
    
    # Première ligne : KPIs
    ui.row(
        ui.column(3,
            ui.value_box(
                "Prix BTC",
                ui.output_text("current_price", "Chargement..."),
                class_="value-box-price"
            )
        ),
        ui.column(3,
            ui.value_box(
                "Variation 24h",
                ui.output_text("price_change", "Chargement..."),
                class_="value-box-change"
            )
        ),
        ui.column(3,
            ui.value_box(
                "Volume 24h",
                ui.output_text("volume_24h", "Chargement..."),
                class_="value-box-volume"
            )
        ),
        ui.column(3,
            ui.value_box(
                "RSI",
                ui.output_text("rsi_value", "Chargement..."),
                class_="value-box-rsi"
            )
        )
    ),
    
    # Deuxième ligne : Graphiques
    ui.row(
        ui.column(2,
            ui.card(
                ui.card_header("Configuration"),
                ui.input_select(
                    "timeframe",
                    "Période",
                    choices={
                        "1m": "1 Minute",
                        "5m": "5 Minutes",
                        "1H": "1 Heure",
                        "6H": "6 Heures",
                        "1D": "1 Jour",
                        "1W": "1 Semaine"
                    },
                    selected="1m"
                ),
                ui.input_checkbox_group(
                    "indicators",
                    "Indicateurs",
                    choices={
                        "sma": "Moyennes Mobiles",
                        "bb": "Bandes de Bollinger",
                        "rsi": "RSI",
                        "macd": "MACD"
                    },
                    selected=["sma", "bb"]
                )
            )
        ),
        ui.column(10,
            ui.card(
                ui.navset_tab(
                    ui.nav_panel("Prix",
                        output_widget("price_chart")
                    ),
                    ui.nav_panel("Indicateurs Techniques",
                        output_widget("technical_chart")
                    )
                )
            )
        )
    )
)

def validate_data(data):
    """Valide les données reçues"""
    if data is None or data.is_empty():
        logger.error("Aucune donnée disponible.")
        return False
    required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    missing = [col for col in required_columns if col not in data.columns]
    if missing:
        logger.error(f"Colonnes manquantes : {missing}")
        return False
    return True

def server(input: Inputs, output: Outputs, session: Session):
    logger.info("Démarrage du serveur Shiny...")
    
    # Initialisation du processeur de données
    dp = DataProcessor()
    
    # Variable pour le rafraîchissement
    last_update = reactive.value(datetime.utcnow())

    # Rafraîchissement périodique
    @reactive.Effect
    async def auto_refresh():
        try:
            last_update.set(datetime.utcnow())
            logger.info("Données rafraîchies automatiquement.")
        except Exception as e:
            logger.error(f"Erreur lors du rafraîchissement : {e}")
        finally:
            reactive.invalidate_later(30)  # Rafraîchissement toutes les 30 secondes

    # Données réactives
    @reactive.Calc
    @reactive.event(input.timeframe, last_update)
    async def get_data():
        logger.info(f"Mise à jour des données pour le timeframe: {input.timeframe()}")
        try:
            data = await dp.get_ohlcv_data(timeframe=input.timeframe())
            
            if validate_data(data):
                logger.info("Calcul des indicateurs techniques...")
                data = TechnicalAnalysis.add_all_indicators(data)
                logger.info(f"Données prêtes : {len(data)} points")
                return data
                
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des données: {e}")
            return None

    # Mise à jour des KPIs
    @output
    @render.text
    async def current_price():
        logger.info("Mise à jour de current_price...")
        data = await get_data()
        if data is None:
            logger.error("Aucune donnée disponible pour current_price.")
            return "Erreur"
        summary = create_market_summary(data)
        return summary["price"]
    
    @output
    @render.text
    async def price_change():
        data = await get_data()
        if data is None:
            return "Erreur"
        summary = create_market_summary(data)
        return summary["change_24h"]
    
    @output
    @render.text
    async def volume_24h():
        data = await get_data()
        if data is None:
            return "Erreur"
        summary = create_market_summary(data)
        return summary["volume_24h"]
    
    @output
    @render.text
    async def rsi_value():
        data = await get_data()
        if data is None:
            return "Erreur"
        summary = create_market_summary(data)
        return summary["rsi"]
    
    # Mise à jour des graphiques
    @output
    @render_widget
    @reactive.event(input.indicators, input.timeframe, last_update)
    async def price_chart():
        data = await get_data()
        if not validate_data(data):
            return go.Figure()
        logger.info("Création du graphique des prix...")
        return create_price_chart(data, selected_indicators=input.indicators())
    
    @output
    @render_widget
    @reactive.event(input.indicators, input.timeframe, last_update)
    async def technical_chart():
        data = await get_data()
        if not validate_data(data):
            return go.Figure()
        logger.info("Création du graphique des indicateurs...")
        return create_technical_chart(data, selected_indicators=input.indicators())

# Création de l'application
app = App(app_ui, server)

if __name__ == "__main__":
    app.run(
        host=config.HOST,
        port=config.PORT
    )