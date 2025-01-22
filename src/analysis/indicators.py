# src/analysis/indicators.py
from typing import Optional
import polars as pl
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TechnicalAnalysis:
    """Calcul des indicateurs techniques sur les données Bitcoin"""
    
    @staticmethod
    def add_moving_averages(
        df: pl.DataFrame,
        periods: list[int] = [20, 50, 200]
    ) -> pl.DataFrame:
        """
        Ajoute les moyennes mobiles simples (SMA) au DataFrame
        """
        try:
            # S'assurer que les données sont triées chronologiquement
            df = df.sort("timestamp")
            
            for period in periods:
                df = df.with_columns([
                    pl.col("close")
                      .rolling_mean(
                          window_size=period,
                          min_periods=1  # Permettre le calcul même avec peu de données
                      )
                      .alias(f"SMA_{period}")
                ])
                
            logger.debug(f"Moyennes mobiles calculées: {periods}")
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des moyennes mobiles: {e}")
            return df
    
    @staticmethod
    def add_bollinger_bands(
        df: pl.DataFrame,
        period: int = 20,
        std_dev: float = 2.0
    ) -> pl.DataFrame:
        """
        Ajoute les bandes de Bollinger au DataFrame
        """
        try:
            df = df.with_columns([
                pl.col("close")
                  .rolling_mean(window_size=period, min_periods=1)
                  .alias("BB_middle"),
                pl.col("close")
                  .rolling_std(window_size=period, min_periods=1)
                  .alias("BB_std")
            ])
            
            df = df.with_columns([
                (pl.col("BB_middle") + (std_dev * pl.col("BB_std")))
                  .alias("BB_upper"),
                (pl.col("BB_middle") - (std_dev * pl.col("BB_std")))
                  .alias("BB_lower")
            ]).drop("BB_std")
            
            logger.debug("Bandes de Bollinger calculées")
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des bandes de Bollinger: {e}")
            return df
    
    @staticmethod
    def add_rsi(
        df: pl.DataFrame,
        period: int = 14
    ) -> pl.DataFrame:
        """
        Ajoute le Relative Strength Index (RSI) au DataFrame
        """
        try:
            # Calcul des variations
            df = df.with_columns([
                pl.col("close").diff().alias("price_diff")
            ])
            
            # Séparation gains et pertes
            df = df.with_columns([
                pl.when(pl.col("price_diff") > 0)
                  .then(pl.col("price_diff"))
                  .otherwise(0)
                  .alias("gains"),
                pl.when(pl.col("price_diff") < 0)
                  .then(-pl.col("price_diff"))
                  .otherwise(0)
                  .alias("losses")
            ])
            
            # Calcul des moyennes mobiles des gains et pertes
            df = df.with_columns([
                pl.col("gains")
                  .rolling_mean(window_size=period, min_periods=1)
                  .alias("avg_gains"),
                pl.col("losses")
                  .rolling_mean(window_size=period, min_periods=1)
                  .alias("avg_losses")
            ])
            
            # Calcul du RSI
            df = df.with_columns([
                (100 - (100 / (1 + (pl.col("avg_gains") / pl.col("avg_losses")))))
                  .alias("RSI")
            ])
            
            # Nettoyage des colonnes temporaires
            df = df.drop(["price_diff", "gains", "losses", "avg_gains", "avg_losses"])
            
            logger.debug("RSI calculé")
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du RSI: {e}")
            return df
    
    @staticmethod
    def add_macd(
        df: pl.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> pl.DataFrame:
        """
        Ajoute le MACD (Moving Average Convergence Divergence) au DataFrame
        """
        try:
            df = df.with_columns([
                # Calcul des moyennes mobiles exponentielles
                pl.col("close")
                  .ewm_mean(span=fast_period, min_periods=1)
                  .alias("EMA_fast"),
                pl.col("close")
                  .ewm_mean(span=slow_period, min_periods=1)
                  .alias("EMA_slow")
            ])
            
            # Calcul du MACD
            df = df.with_columns([
                (pl.col("EMA_fast") - pl.col("EMA_slow"))
                  .alias("MACD")
            ])
            
            # Calcul de la ligne de signal
            df = df.with_columns([
                pl.col("MACD")
                  .ewm_mean(span=signal_period, min_periods=1)
                  .alias("MACD_Signal")
            ])
            
            # Calcul de l'histogramme
            df = df.with_columns([
                (pl.col("MACD") - pl.col("MACD_Signal"))
                  .alias("MACD_Histogram")
            ])
            
            # Nettoyage des colonnes temporaires
            df = df.drop(["EMA_fast", "EMA_slow"])
            
            logger.debug("MACD calculé")
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du MACD: {e}")
            return df
    
    @staticmethod
    def add_all_indicators(
        df: pl.DataFrame,
        sma_periods: list[int] = [20, 50, 200],
        bb_period: int = 20,
        rsi_period: int = 14
    ) -> pl.DataFrame:
        """
        Ajoute tous les indicateurs techniques au DataFrame
        """
        try:
            df = TechnicalAnalysis.add_moving_averages(df, sma_periods)
            df = TechnicalAnalysis.add_bollinger_bands(df, bb_period)
            df = TechnicalAnalysis.add_rsi(df, rsi_period)
            df = TechnicalAnalysis.add_macd(df)
            
            logger.debug("Tous les indicateurs techniques calculés")
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des indicateurs: {e}")
            return df