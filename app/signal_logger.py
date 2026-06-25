from pathlib import Path
from datetime import datetime
import csv


class SignalLogger:
    def __init__(self, path="data/signals.csv"):
        self.path = Path(path)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not self.path.exists():
            with open(self.path, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([
                    "timestamp",
                    "symbol",
                    "price",
                    "change_5m",
                    "change_15m",
                    "change_60m",
                    "volume_spike",
                    "spread_pct",
                    "rsi",
                    "signal",
                    "reason",
                    "stop_loss_pct",
                    "take_profit_pct"
                ])

    def log(self, analysis):
        """
        Logs only meaningful signals, not every AVOID row.
        """
        if analysis.get("signal") not in ["WATCH", "PAPER_LONG"]:
            return

        with open(self.path, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                datetime.utcnow().isoformat(),
                analysis.get("symbol"),
                analysis.get("price"),
                analysis.get("change_5m"),
                analysis.get("change_15m"),
                analysis.get("change_60m"),
                analysis.get("volume_spike"),
                analysis.get("spread_pct"),
                analysis.get("rsi"),
                analysis.get("signal"),
                analysis.get("reason"),
                analysis.get("stop_loss_pct"),
                analysis.get("take_profit_pct")
            ])
