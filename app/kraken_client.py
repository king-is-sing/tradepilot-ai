import requests
import pandas as pd


BASE_URL = "https://api.kraken.com/0/public"


class KrakenClient:
    def __init__(self):
        self.session = requests.Session()
        self.pair_map = self._load_pair_map()

    def _load_pair_map(self):
        """
        Maps human-readable Kraken names like BTC/USD
        to REST API pair names like XBTUSD or ETHUSD.
        """
        url = f"{BASE_URL}/AssetPairs"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("error"):
            raise RuntimeError(f"Kraken error: {data['error']}")

        pair_map = {}

        for _, info in data["result"].items():
            wsname = info.get("wsname")
            altname = info.get("altname")

            if wsname and altname:
                pair_map[wsname] = altname

        return pair_map

    def get_rest_pair(self, symbol):
        """
        Converts user-friendly symbols like BTC/USD into Kraken REST pair names.
        Kraken often uses XBT instead of BTC.
        """
        aliases = {
            "BTC/USD": "XBT/USD",
            "BTC/EUR": "XBT/EUR",
            "BTC/GBP": "XBT/GBP",
        }

        kraken_symbol = aliases.get(symbol, symbol)

        if kraken_symbol not in self.pair_map:
            available = list(self.pair_map.keys())[:20]
            raise ValueError(
                f"Symbol not found on Kraken: {symbol}. "
                f"Tried: {kraken_symbol}. "
                f"Example available symbols: {available}"
            )

        return self.pair_map[kraken_symbol]

    def get_ohlc(self, symbol, interval=1):
        """
        Gets OHLC candle data from Kraken.
        interval=1 means 1-minute candles.
        """
        pair = self.get_rest_pair(symbol)

        url = f"{BASE_URL}/OHLC"
        params = {
            "pair": pair,
            "interval": interval
        }

        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("error"):
            raise RuntimeError(f"Kraken error: {data['error']}")

        result = data["result"]
        result_key = [key for key in result.keys() if key != "last"][0]

        rows = result[result_key]

        df = pd.DataFrame(
            rows,
            columns=[
                "time",
                "open",
                "high",
                "low",
                "close",
                "vwap",
                "volume",
                "count"
            ]
        )

        numeric_columns = ["open", "high", "low", "close", "vwap", "volume"]

        for col in numeric_columns:
            df[col] = df[col].astype(float)

        df["time"] = pd.to_datetime(df["time"], unit="s")

        return df

    def get_ticker(self, symbol):
        """
        Gets current bid, ask, and last price.
        """
        pair = self.get_rest_pair(symbol)

        url = f"{BASE_URL}/Ticker"
        params = {
            "pair": pair
        }

        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("error"):
            raise RuntimeError(f"Kraken error: {data['error']}")

        result_key = list(data["result"].keys())[0]
        ticker = data["result"][result_key]

        ask = float(ticker["a"][0])
        bid = float(ticker["b"][0])
        last = float(ticker["c"][0])

        spread_pct = ((ask - bid) / last) * 100

        return {
            "symbol": symbol,
            "bid": bid,
            "ask": ask,
            "last": last,
            "spread_pct": spread_pct
        }
