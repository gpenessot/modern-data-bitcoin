# src/dashboard/components/tables.py
import polars as pl
from ...analysis.statistics import MarketStatistics

def create_market_summary(df: pl.DataFrame) -> dict:
    """
    Crée un résumé du marché pour affichage
    """
    stats = MarketStatistics.get_market_summary(df)
    if stats is None:
        raise ValueError("Le résumé du marché est vide.")
    
    return {
        "price": stats["latest_price"],
        "change_24h": stats["change_24h"],
        "volatility": stats.get("volatility_30d", "N/A"),
        "trend": stats["trend"],
        "rsi": stats["technical_indicators"]["rsi"] if stats["technical_indicators"] else "N/A",
        "volume_24h": stats["volume_24h"]
    }