# src/database/models.py
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

@dataclass
class BitcoinPrice:
    """Modèle pour les données de prix Bitcoin"""
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    trades: Optional[int] = None

    @classmethod
    def from_coinbase(cls, data: dict) -> 'BitcoinPrice':
        """Crée une instance à partir des données Coinbase"""
        return cls(
            timestamp=datetime.fromtimestamp(data[0]),
            open=Decimal(str(data[1])),
            high=Decimal(str(data[2])),
            low=Decimal(str(data[3])),
            close=Decimal(str(data[4])),
            volume=Decimal(str(data[5])),
            trades=data[6] if len(data) > 6 else None
        )