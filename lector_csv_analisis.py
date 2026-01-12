import pandas as pd
import numpy as np

df = pd.read_csv("outputs/csv/trade_log.csv")

total_trades = len(df)
wins = df[df["pnl_usd"] > 0]
losses = df[df["pnl_usd"] < 0]

win_rate = len(wins) / total_trades if total_trades else 0
avg_win = wins["pnl_usd"].mean() if len(wins) else 0
avg_loss = losses["pnl_usd"].mean() if len(losses) else 0
profit_factor = wins["pnl_usd"].sum() / abs(losses["pnl_usd"].sum()) if len(losses) else float("inf")
expectancy = win_rate * avg_win + (1 - win_rate) * avg_loss
total_pnl = df["pnl_usd"].sum()

print("Total trades:", total_trades)
print("Win rate:", round(win_rate, 3))
print("Avg win ($):", round(avg_win, 2))
print("Avg loss ($):", round(avg_loss, 2))
print("Profit Factor:", round(profit_factor, 2))
print("Expectancy ($):", round(expectancy, 2))
print("Total PnL ($):", round(total_pnl, 2))
