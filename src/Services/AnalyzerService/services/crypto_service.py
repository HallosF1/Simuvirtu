import ccxt
from typing import List, Dict, Optional

class CryptoService:
    def __init__(self):
        self.exchange = ccxt.binance()

    def get_crypto_time_frame(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> List[Dict]:
        """
        Returns OHLCV as a list of dicts:
        [{timestamp, open, high, low, close, volume}, ...]
        """
        ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        return [
            {"timestamp": row[0], "open": row[1], "high": row[2], "low": row[3], "close": row[4], "volume": row[5]}
            for row in ohlcv
        ]

    @staticmethod
    def moving_average(data: List[Dict], window: int = 3) -> Optional[float]:
        if len(data) < window:
            return None
        closes = [c["close"] for c in data[-window:]]
        return sum(closes) / window

    @staticmethod
    def rsi(data: List[Dict], period: int = 14) -> Optional[float]:
        if len(data) < period + 1:
            return None
        gains = 0.0
        losses = 0.0
        # last `period` differences
        for i in range(-period, 0):
            change = data[i]["close"] - data[i - 1]["close"]
            if change > 0:
                gains += change
            else:
                losses += -change
        avg_gain = gains / period if gains > 0 else 1e-9
        avg_loss = losses / period if losses > 0 else 1e-9
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def volume_trend(data: List[Dict]) -> Optional[str]:
        if len(data) < 2:
            return None
        return "Uptrend" if data[-1]["volume"] > data[-2]["volume"] else "Downtrend"

    @staticmethod
    def trend_direction(data: List[Dict]) -> Optional[str]:
        if len(data) < 3:
            return None
        if data[-1]["close"] > data[-2]["close"] > data[-3]["close"]:
            return "Uptrend"
        if data[-1]["close"] < data[-2]["close"] < data[-3]["close"]:
            return "Downtrend"
        return "Sideways"

    @classmethod
    def generate_signal(cls, data: List[Dict]) -> str:
        """Generate trading signal from all analyses"""
        ma = cls.moving_average(data, window=5)
        rsi_val = cls.rsi(data)
        vol_trend = cls.volume_trend(data)
        trend = cls.trend_direction(data)

        if ma is None or rsi_val is None or vol_trend is None or trend is None:
            return "INSUFFICIENT DATA"

        last_close = data[-1]["close"]

        if last_close > ma and rsi_val < 70 and vol_trend == "Uptrend":
            return "BUY"
        elif last_close < ma and rsi_val > 30 and trend == "Downtrend":
            return "SELL"
        else:
            return "HOLD"

    def signal_for_symbol(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> str:
        symbol = symbol.upper().strip() + "USDT"
        data = self.get_crypto_time_frame(symbol, timeframe, limit)
        return self.generate_signal(data)
