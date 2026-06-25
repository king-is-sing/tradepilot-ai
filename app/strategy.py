def percentage_change(current, previous):
    if previous == 0:
        return 0

    return ((current - previous) / previous) * 100


def calculate_rsi(prices, period=14):
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

    return round(float(rsi), 2)


STRATEGY_SETTINGS = {
    "ADA/USD": {
        "change_threshold": 0.4,
        "volume_threshold": 1.2,
        "rsi_max": 70,
        "stop_loss_pct": 0.5,
        "take_profit_pct": 1.2
    },
    "XRP/USD": {
        "change_threshold": 0.4,
        "volume_threshold": 1.0,
        "rsi_max": 70,
        "stop_loss_pct": 0.5,
        "take_profit_pct": 0.8
    },
    "DEFAULT": {
        "change_threshold": 0.8,
        "volume_threshold": 1.4,
        "rsi_max": 70,
        "stop_loss_pct": 0.75,
        "take_profit_pct": 1.2
    }
}


def analyse_market(symbol, df, ticker, btc_change_15m=None):
    """
    Uses the last COMPLETED candle, not the current unfinished candle.
    This makes volume spike and momentum signals more reliable.
    """
    if len(df) < 62:
        return {
            "symbol": symbol,
            "signal": "AVOID",
            "reason": "Not enough candle data yet."
        }

    settings = STRATEGY_SETTINGS.get(symbol, STRATEGY_SETTINGS["DEFAULT"])

    # Use last completed candle
    latest_price = df["close"].iloc[-2]

    price_5m_ago = df["close"].iloc[-7]
    price_15m_ago = df["close"].iloc[-17]
    price_60m_ago = df["close"].iloc[-62]

    change_5m = percentage_change(latest_price, price_5m_ago)
    change_15m = percentage_change(latest_price, price_15m_ago)
    change_60m = percentage_change(latest_price, price_60m_ago)

    latest_volume = df["volume"].iloc[-2]
    average_volume = df["volume"].iloc[-32:-2].mean()

    if average_volume == 0:
        volume_spike = 0
    else:
        volume_spike = latest_volume / average_volume

    rsi = calculate_rsi(df["close"].iloc[:-1])
    spread_pct = ticker["spread_pct"]

    signal = "AVOID"
    reason = "No strong setup."

    if (
        change_15m > settings["change_threshold"]
        and volume_spike > settings["volume_threshold"]
        and spread_pct < 0.35
        and rsi is not None
        and rsi < settings["rsi_max"]
    ):
        signal = "PAPER_LONG"
        reason = (
            f"Optimised setup: 15m change > {settings['change_threshold']}%, "
            f"volume spike > {settings['volume_threshold']}x, RSI < {settings['rsi_max']}."
        )

    elif (
        change_15m > settings["change_threshold"] * 0.6
        and volume_spike > 1.0
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
        "price": round(float(latest_price), 6),
        "change_5m": round(float(change_5m), 2),
        "change_15m": round(float(change_15m), 2),
        "change_60m": round(float(change_60m), 2),
        "volume_spike": round(float(volume_spike), 2),
        "spread_pct": round(float(spread_pct), 4),
        "rsi": rsi,
        "signal": signal,
        "reason": reason,
        "stop_loss_pct": settings["stop_loss_pct"],
        "take_profit_pct": settings["take_profit_pct"]
    }
