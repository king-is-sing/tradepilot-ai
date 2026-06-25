from datetime import datetime
from pathlib import Path
import csv


class PaperTrader:
    def __init__(self, starting_balance=1000, trade_log_path="data/trades.csv"):
        self.balance = starting_balance
        self.open_trades = []
        self.closed_trades = []
        self.max_risk_per_trade_pct = 1.0
        self.trade_log_path = Path(trade_log_path)
        self._ensure_trade_log_exists()

    def _ensure_trade_log_exists(self):
        """
        Creates data/trades.csv with headers if it does not exist.
        """
        self.trade_log_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.trade_log_path.exists():
            with open(self.trade_log_path, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([
                    "symbol",
                    "side",
                    "entry_price",
                    "exit_price",
                    "quantity",
                    "stop_loss",
                    "take_profit",
                    "pnl",
                    "close_reason",
                    "opened_at",
                    "closed_at"
                ])

    def _save_closed_trade(self, trade):
        """
        Appends a closed paper trade to data/trades.csv.
        """
        with open(self.trade_log_path, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                trade["symbol"],
                trade["side"],
                trade["entry_price"],
                trade["exit_price"],
                trade["quantity"],
                trade["stop_loss"],
                trade["take_profit"],
                trade["pnl"],
                trade["close_reason"],
                trade["opened_at"],
                trade["closed_at"]
            ])

    def has_open_trade(self, symbol):
        return any(
            trade["symbol"] == symbol and trade["status"] == "OPEN"
            for trade in self.open_trades
        )

    def open_long(self, symbol, entry_price):
        """
        Opens a simulated long trade.

        Risk is capped at 1% of bankroll.
        Stop loss = -1%
        Take profit = +2%
        """
        if self.has_open_trade(symbol):
            return None

        risk_amount = self.balance * (self.max_risk_per_trade_pct / 100)

        stop_loss = entry_price * 0.99
        take_profit = entry_price * 1.02

        risk_per_unit = entry_price - stop_loss

        if risk_per_unit <= 0:
            return None

        quantity = risk_amount / risk_per_unit

        trade = {
            "symbol": symbol,
            "side": "LONG",
            "entry_price": entry_price,
            "quantity": quantity,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "status": "OPEN",
            "opened_at": datetime.utcnow().isoformat(),
            "closed_at": None,
            "exit_price": None,
            "pnl": None,
            "close_reason": None
        }

        self.open_trades.append(trade)
        return trade

    def update_trades(self, prices):
        """
        Checks whether open paper trades have hit stop loss or take profit.
        """
        for trade in self.open_trades:
            if trade["status"] != "OPEN":
                continue

            symbol = trade["symbol"]

            if symbol not in prices:
                continue

            current_price = prices[symbol]

            should_close = False
            close_reason = None

            if current_price <= trade["stop_loss"]:
                should_close = True
                close_reason = "STOP_LOSS"

            elif current_price >= trade["take_profit"]:
                should_close = True
                close_reason = "TAKE_PROFIT"

            if should_close:
                pnl = (current_price - trade["entry_price"]) * trade["quantity"]

                trade["status"] = "CLOSED"
                trade["closed_at"] = datetime.utcnow().isoformat()
                trade["exit_price"] = current_price
                trade["pnl"] = pnl
                trade["close_reason"] = close_reason

                self.balance += pnl
                self.closed_trades.append(trade)
                self._save_closed_trade(trade)

        self.open_trades = [
            trade for trade in self.open_trades
            if trade["status"] == "OPEN"
        ]

    def summary(self):
        total_pnl = sum(
            trade["pnl"]
            for trade in self.closed_trades
            if trade["pnl"] is not None
        )

        wins = [
            trade for trade in self.closed_trades
            if trade["pnl"] is not None and trade["pnl"] > 0
        ]

        total_closed = len(self.closed_trades)

        if total_closed == 0:
            win_rate = 0
        else:
            win_rate = (len(wins) / total_closed) * 100

        return {
            "balance": round(self.balance, 2),
            "total_pnl": round(total_pnl, 2),
            "open_trades": len(self.open_trades),
            "closed_trades": total_closed,
            "win_rate": round(win_rate, 2)
        }
