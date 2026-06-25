from kraken_client import KrakenClient
from strategy import analyse_market


SYMBOLS = [
    "BTC/USD",
    "ETH/USD",
    "SOL/USD",
    "XRP/USD",
    "ADA/USD",
    "LINK/USD"
]


def run_backtest(symbol, starting_balance=1000):
    client = KrakenClient()
    df = client.get_ohlc(symbol, interval=1)

    balance = starting_balance
    trades = []

    max_risk_per_trade_pct = 1.0
    max_hold_candles = 45

    for i in range(61, len(df) - max_hold_candles):
        current_df = df.iloc[:i + 1]

        fake_ticker = {
            "spread_pct": 0.05
        }

        analysis = analyse_market(
            symbol=symbol,
            df=current_df,
            ticker=fake_ticker,
            btc_change_15m=None
        )

        if analysis["signal"] != "PAPER_LONG":
            continue

        entry_price = analysis["price"]
        stop_loss = entry_price * 0.99
        take_profit = entry_price * 1.02

        risk_amount = balance * (max_risk_per_trade_pct / 100)
        risk_per_unit = entry_price - stop_loss
        quantity = risk_amount / risk_per_unit

        future_candles = df.iloc[i + 1:i + 1 + max_hold_candles]

        exit_price = future_candles["close"].iloc[-1]
        close_reason = "MAX_HOLD"

        for _, candle in future_candles.iterrows():
            low = candle["low"]
            high = candle["high"]

            # Conservative assumption:
            # if stop loss and take profit happen in the same candle,
            # assume stop loss happened first.
            if low <= stop_loss:
                exit_price = stop_loss
                close_reason = "STOP_LOSS"
                break

            if high >= take_profit:
                exit_price = take_profit
                close_reason = "TAKE_PROFIT"
                break

        pnl = (exit_price - entry_price) * quantity
        balance += pnl

        trades.append({
            "symbol": symbol,
            "entry_price": round(entry_price, 6),
            "exit_price": round(exit_price, 6),
            "pnl": round(pnl, 2),
            "close_reason": close_reason,
            "signal_reason": analysis["reason"]
        })

    total_pnl = balance - starting_balance

    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]

    win_rate = 0
    if trades:
        win_rate = (len(wins) / len(trades)) * 100

    return {
        "symbol": symbol,
        "starting_balance": starting_balance,
        "ending_balance": round(balance, 2),
        "total_pnl": round(total_pnl, 2),
        "total_trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 2),
        "trades": trades
    }


def main():
    print("\nTradePilot AI Backtest")
    print("======================\n")

    all_results = []

    for symbol in SYMBOLS:
        print(f"Backtesting {symbol}...")
        result = run_backtest(symbol)
        all_results.append(result)

        print(f"Symbol: {result['symbol']}")
        print(f"Ending balance: £{result['ending_balance']}")
        print(f"Total PnL: £{result['total_pnl']}")
        print(f"Trades: {result['total_trades']}")
        print(f"Win rate: {result['win_rate']}%")
        print("-" * 40)

    total_pnl = sum(r["total_pnl"] for r in all_results)
    total_trades = sum(r["total_trades"] for r in all_results)

    print("\nOverall Result")
    print("==============")
    print(f"Total PnL across symbols: £{round(total_pnl, 2)}")
    print(f"Total trades: {total_trades}")


if __name__ == "__main__":
    main()

