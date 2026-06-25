import time
from rich.console import Console
from rich.table import Table

from kraken_client import KrakenClient
from strategy import analyse_market, percentage_change
from paper_trader import PaperTrader
from notifier import notify
from signal_logger import SignalLogger


SYMBOLS = [
    "BTC/USD",
    "ETH/USD",
    "SOL/USD",
    "XRP/USD",
    "ADA/USD",
    "LINK/USD"
]


def get_btc_15m_change(client):
    btc_df = client.get_ohlc("BTC/USD", interval=1)

    latest = btc_df["close"].iloc[-2]
    previous = btc_df["close"].iloc[-17]

    return percentage_change(latest, previous)


def main():
    console = Console()
    client = KrakenClient()
    trader = PaperTrader(starting_balance=1000)
    signal_logger = SignalLogger()

    console.print("[bold green]TradePilot AI started[/bold green]")
    console.print("Mode: PAPER TRADING ONLY")
    console.print("Alerts: Mac notifications enabled")
    console.print("Signal log: data/signals.csv")
    console.print("Press CTRL+C to stop.\n")

    while True:
        try:
            btc_change_15m = get_btc_15m_change(client)
            latest_prices = {}
            analyses = []

            for symbol in SYMBOLS:
                try:
                    df = client.get_ohlc(symbol, interval=1)
                    ticker = client.get_ticker(symbol)

                    analysis = analyse_market(
                        symbol=symbol,
                        df=df,
                        ticker=ticker,
                        btc_change_15m=btc_change_15m
                    )

                    analyses.append(analysis)
                    signal_logger.log(analysis)

                    if "price" in analysis:
                        latest_prices[symbol] = analysis["price"]

                    if analysis["signal"] == "PAPER_LONG":
                        trade = trader.open_long(
                            symbol=symbol,
                            entry_price=analysis["price"],
                            stop_loss_pct=analysis.get("stop_loss_pct", 1.0),
                            take_profit_pct=analysis.get("take_profit_pct", 2.0)
                        )

                        if trade:
                            alert_message = (
                                f"{symbol} at {analysis['price']} | "
                                f"SL {analysis.get('stop_loss_pct')}% | "
                                f"TP {analysis.get('take_profit_pct')}%"
                            )

                            notify("TradePilot PAPER_LONG", alert_message)

                            console.print(
                                f"[bold yellow]Opened paper trade:[/bold yellow] "
                                f"{symbol} at {analysis['price']}"
                            )

                except Exception as symbol_error:
                    console.print(f"[red]Error with {symbol}: {symbol_error}[/red]")

            trader.update_trades(latest_prices)

            table = Table(title="TradePilot AI Live Scanner")

            table.add_column("Symbol", justify="left")
            table.add_column("Price", justify="right")
            table.add_column("5m %", justify="right")
            table.add_column("15m %", justify="right")
            table.add_column("60m %", justify="right")
            table.add_column("Vol Spike", justify="right")
            table.add_column("Spread %", justify="right")
            table.add_column("RSI", justify="right")
            table.add_column("Signal", justify="left")
            table.add_column("Reason", justify="left")

            for a in analyses:
                signal = a.get("signal", "ERROR")

                if signal == "PAPER_LONG":
                    signal_style = "[bold green]PAPER_LONG[/bold green]"
                elif signal == "WATCH":
                    signal_style = "[bold yellow]WATCH[/bold yellow]"
                else:
                    signal_style = "[red]AVOID[/red]"

                table.add_row(
                    str(a.get("symbol", "-")),
                    str(a.get("price", "-")),
                    str(a.get("change_5m", "-")),
                    str(a.get("change_15m", "-")),
                    str(a.get("change_60m", "-")),
                    str(a.get("volume_spike", "-")),
                    str(a.get("spread_pct", "-")),
                    str(a.get("rsi", "-")),
                    signal_style,
                    str(a.get("reason", "-"))
                )

            console.clear()
            console.print(table)

            summary = trader.summary()

            console.print("\n[bold cyan]Paper Portfolio[/bold cyan]")
            console.print(f"Balance: £{summary['balance']}")
            console.print(f"Total PnL: £{summary['total_pnl']}")
            console.print(f"Open trades: {summary['open_trades']}")
            console.print(f"Closed trades: {summary['closed_trades']}")
            console.print(f"Win rate: {summary['win_rate']}%")

            if trader.open_trades:
                console.print("\n[bold magenta]Open Paper Trades[/bold magenta]")
                for trade in trader.open_trades:
                    console.print(trade)

            time.sleep(60)

        except KeyboardInterrupt:
            console.print("\n[bold red]Stopped TradePilot AI.[/bold red]")
            break

        except Exception as error:
            console.print(f"[red]Main loop error: {error}[/red]")
            time.sleep(30)


if __name__ == "__main__":
    main()
