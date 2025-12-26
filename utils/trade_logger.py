import csv
import os
import time
from datetime import datetime

LOG_FILE = "outputs/csv/trade_log.csv"

FIELDS = [
    "timestamp_entry",
    "timestamp_exit",
    "symbol",
    "strategy",
    "qty",
    "entry_price",
    "exit_price",
    "stop_loss",
    "take_profit",
    "pnl_usd",
    "pnl_pct",
    "duration_sec",
    "exit_reason",
    "order_id"
]


def init_trade_log():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode="w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()


def log_trade(trade: dict):
    with open(LOG_FILE, mode="a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writerow(trade)


def now_ts():
    return int(time.time())


def ts_to_str(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
