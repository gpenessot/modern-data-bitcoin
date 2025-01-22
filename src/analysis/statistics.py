# src/analysis/statistics.py
from typing import Dict, Any
import numpy as np
import polars as pl
from datetime import datetime, timedelta
import logging
from .indicators import TechnicalAnalysis

logger = logging.getLogger(__name__)

class MarketStatistics:
    """Calcul des statistiques de marché"""
    
    @staticmethod
    def calculate_returns(df: pl.DataFrame) -> pl.DataFrame:
        """
        Calcule les rendements sur différentes périodes
        """
        try:
            df = df.with_columns([
                # Rendements journaliers
                (pl.col("close") / pl.col("close").shift(1) - 1)
                  .alias("daily_return"),
                
                # Rendements hebdomadaires (5 périodes si horaire)
                (pl.col("close") / pl.col("close").shift(5) - 1)
                  .alias("weekly_return"),
                
                # Rendements mensuels (20 périodes si horaire)
                (pl.col("close") / pl.col("close").shift(20) - 1)
                  .alias("monthly_return")
            ])
        except Exception as e:
            logger.error(f"Erreur lors du calcul des rendements: {e}")
            
        return df
    
    @staticmethod
    def calculate_volatility(df: pl.DataFrame) -> pl.DataFrame:
        """
        Calcule la volatilité sur différentes périodes
        """
        try:
            df = df.with_columns([
                # Volatilité sur 7 jours
                pl.col("daily_return")
                  .rolling_std(window_size=7)
                  .mul(np.sqrt(365))
                  .alias("volatility_7d"),
                
                # Volatilité sur 30 jours
                pl.col("daily_return")
                  .rolling_std(window_size=30)
                  .mul(np.sqrt(365))
                  .alias("volatility_30d")
            ])
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la volatilité: {e}")
            
        return df
    
    @staticmethod
    def get_market_summary(
        df: pl.DataFrame,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Calcule un résumé des statistiques de marché
        
        Args:
            df: DataFrame avec indicateurs techniques
            lookback_days: Nombre de jours pour l'analyse
            
        Returns:
            Dictionnaire avec les statistiques de marché
        """
        if len(df) == 0:
            return {
                "price": "N/A",
                "change_24h": "N/A",
                "volume_24h": "N/A",
                "rsi": "N/A",
                "trend": "N/D"
            }
            
        try:
            # Calcul des rendements et volatilité
            df = MarketStatistics.calculate_returns(df)
            df = MarketStatistics.calculate_volatility(df)
            
            # Prix actuel et variation
            latest_price = float(df["close"].tail(1)[0])

            # Calcul de la variation sur 24 périodes
            first_price = float(df["close"].tail(24).head(1)[0])
            change_24h = ((latest_price - first_price) / first_price) * 100
            
            # Volume sur 24 périodes
            volume_24h = float(df["volume"].tail(24).sum())
            
            # Tendance basée sur les SMA si disponibles
            trend = None
            if "SMA_20" in df.columns and "SMA_50" in df.columns:
                sma_20 = float(df["SMA_20"].tail(1)[0]) if not df["SMA_20"].tail(1)[0] is None else None
                sma_50 = float(df["SMA_50"].tail(1)[0]) if not df["SMA_50"].tail(1)[0] is None else None
                if sma_20 is not None and sma_50 is not None:
                    trend = "Haussière" if sma_20 > sma_50 else "Baissière"
            
            # RSI et MACD si disponibles
            rsi = float(df["RSI"].tail(1)[0]) if "RSI" in df.columns else None
            macd = float(df["MACD"].tail(1)[0]) if "MACD" in df.columns else None
            macd_signal = float(df["MACD_Signal"].tail(1)[0]) if "MACD_Signal" in df.columns else None
            
            # Formatage des résultats
            return {
                "latest_price": f"${latest_price:,.2f}",
                "change_24h": f"{change_24h:+.1f}%",
                "volume_24h": f"${volume_24h:,.0f}",
                "rsi": f"{rsi:.1f}" if rsi is not None else "N/A",
                "trend": trend if trend is not None else "N/D",
                "technical_indicators": {
                    "rsi": rsi,
                    "macd": macd,
                    "macd_signal": macd_signal,
                    "sma_20": sma_20 if 'sma_20' in locals() else None,
                    "sma_50": sma_50 if 'sma_50' in locals() else None
                } if rsi is not None else None
            }
            
        except Exception as e:
            logger.error(f"Erreur dans get_market_summary: {e}")
            return {
                "price": "Erreur",
                "change_24h": "Erreur",
                "volume_24h": "Erreur",
                "rsi": "Erreur",
                "trend": "N/D"
            }


# Script de test
if __name__ == "__main__":
    from ..data.processor import DataProcessor
    
    # Test des indicateurs
    processor = DataProcessor()
    data = processor.get_ohlcv_data(
        start_time=datetime.utcnow() - timedelta(days=60),
        timeframe="1H"
    )
    
    # Ajout des indicateurs
    data = TechnicalAnalysis.add_all_indicators(data)
    
    # Calcul des statistiques
    stats = MarketStatistics.get_market_summary(data)
    
    # Affichage des résultats
    print("\nRésumé du marché Bitcoin:")
    print(f"Prix actuel: {stats['price']}")
    print(f"Variation 24h: {stats['change_24h']}")
    print(f"Volume 24h: {stats['volume_24h']}")
    print(f"RSI: {stats['rsi']}")
    print(f"Tendance: {stats['trend']}")
    
    if stats.get('technical_indicators'):
        print("\nIndicateurs techniques:")
        ti = stats['technical_indicators']
        if ti['rsi'] is not None:
            print(f"RSI: {ti['rsi']:.1f}")
        if ti['macd'] is not None:
            print(f"MACD: {ti['macd']:.2f}")