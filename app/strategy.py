def percentage_change(current, previous):
    if previous == 0:
        return 0

    return ((current - previous) / previous) * 100


def calculate_rsi(prices, period=14):
    """
    Basic RSI calculation.
    RSI above 70 = potentially overbought.
    RSI below 30 = potentially oversold.
    """
    if len(prices) < period + 1:
        return None

    deltas = prices.diff()

    gains = deltas.clip(lower=0)
    losses = -deltas.clip(upper=0)

    avg_gain = gains.rolling(window=period).mean().iloc[-1]
    avg_loss = losses.rolling(window=period).mean().iloc[-1]

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return round(rsi, 2)


def analyse_market(symbol, df, ticker, btc_change_15m=None):
    """
    Turns Kraken data into a simple trading signal.
    """
    if len(df) < 61:
        return {
            "symbol": symbol,
            "signal": "AVOID",
            "reason": "Not enough candle data yet."
        }

    latest_price = df["close"].iloc[-1]

    price_5m_ago = df["close"].iloc[-6]
    price_15m_ago = df["close"].iloc[-16]
    price_60m_ago = df["close"].iloc[-61]

    change_5m = percentage_change(latest_price, price_5m_ago)
    change_15m = percentage_change(latest_price, price_15m_ago)
    change_60m = percentage_change(latest_price, price_60m_ago)

    latest_volume = df["volume"].iloc[-1]
    average_volume = df["volume"].iloc[-31:-1].mean()

    if average_volume == 0:
        volume_spike = 0
    else:
        volume_spike = latest_volume / average_volume

    rsi = calculate_rsi(df["close"])

    spread_pct = ticker["spread_pct"]

    signal = "AVOID"
    reason = "No strong setup."

    if (
        change_15m > 2.0
        and volume_spike > 1.8
        and spread_pct < 0.25
        and rsi is not None
        and rsi < 78
    ):
        signal = "PAPER_LONG"
        reason = "Strong 15m momentum with volume confirmation and acceptable spread."

    elif (
        change_15m > 1.0
        and volume_spike > 1.3
        and spread_pct < 0.35
    ):
        signal = "WATCH"
        reason = "Some momentum, but not strong enough for paper trade."

    if btc_change_15m is not None and btc_change_15m < -1.0 and symbol != "BTC/USD":
        signal = "AVOID"
        reason = "BTC is dropping, so avoiding altcoin momentum trade."

    if rsi is not None and rsi > 82:
        signal = "AVOID"
        reason = "RSI too high. Move may already be overextended."

    if spread_pct > 0.5:
        signal = "AVOID"
        reason = "Spread too wide."

    return {
        "symbol": symbol,
        "price": round(latest_price, 6),
        "change_5m": round(change_5m, 2),
        "change_15m": round(change_15m, 2),
        "change_60m": round(change_60m, 2),
        "volume_spike": round(volume_spike, 2),
        "spread_pct": round(spread_pct, 4),
        "rsi": rsi,
        "signal": signal,
        "reason": reason
    }

