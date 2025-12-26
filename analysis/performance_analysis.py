import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------------------------
# LOAD DATA
# ---------------------------
df = pd.read_csv("outputs/csv/trade_log.csv")

if df.empty:
    raise ValueError("trade_log.csv está vacío")

# Convert timestamps
df["timestamp_entry"] = pd.to_datetime(df["timestamp_entry"], unit="s")
df["timestamp_exit"] = pd.to_datetime(df["timestamp_exit"], unit="s")

# ---------------------------
# BASIC METRICS
# ---------------------------
total_trades = len(df)
wins = df[df["pnl_usd"] > 0]
losses = df[df["pnl_usd"] <= 0]

win_rate = len(wins) / total_trades
total_pnl = df["pnl_usd"].sum()
avg_pnl = df["pnl_usd"].mean()

profit_factor = wins["pnl_usd"].sum() / abs(losses["pnl_usd"].sum()) if not losses.empty else np.inf

expectancy = avg_pnl

avg_duration = df["duration_sec"].mean()

# ---------------------------
# EQUITY CURVE
# ---------------------------
initial_capital = 10_000  # AJUSTA si quieres
df["equity"] = initial_capital + df["pnl_usd"].cumsum()

# ---------------------------
# DRAWDOWN
# ---------------------------
df["equity_peak"] = df["equity"].cummax()
df["drawdown"] = (df["equity"] - df["equity_peak"]) / df["equity_peak"]
max_drawdown = df["drawdown"].min()

# ---------------------------
# CAGR
# ---------------------------
days = (df["timestamp_exit"].iloc[-1] - df["timestamp_entry"].iloc[0]).days
years = days / 365 if days > 0 else np.nan
cagr = (df["equity"].iloc[-1] / initial_capital) ** (1 / years) - 1 if years else np.nan

# ---------------------------
# SHARPE RATIO
# ---------------------------
returns = df["pnl_usd"] / initial_capital
sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() != 0 else np.nan

# ---------------------------
# PRINT RESULTS
# ---------------------------
print("\n===== PERFORMANCE SUMMARY =====")
print(f"Total trades: {total_trades}")
print(f"Win rate: {win_rate:.2%}")
print(f"Total PnL ($): {total_pnl:.2f}")
print(f"Average PnL per trade ($): {avg_pnl:.2f}")
print(f"Profit Factor: {profit_factor:.2f}")
print(f"Expectancy ($): {expectancy:.2f}")
print(f"Max Drawdown: {max_drawdown:.2%}")
print(f"CAGR: {cagr:.2%}")
print(f"Sharpe Ratio: {sharpe:.2f}")
print(f"Avg trade duration (sec): {avg_duration:.0f}")

# ---------------------------
# PLOT EQUITY CURVE
# ---------------------------
plt.figure()
plt.plot(df["timestamp_exit"], df["equity"])
plt.title("Equity Curve")
plt.xlabel("Time")
plt.ylabel("Equity ($)")
plt.grid(True)
plt.show()
