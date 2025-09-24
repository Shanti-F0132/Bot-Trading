import pandas as pd
import numpy as np

def backtest(df, initial_cash=10000, risk_free_rate=0.02):
    """
    Backtester simple que simula compra/venta basado en señales de posición
    y calcula métricas de desempeño (CAGR, Sharpe, Max Drawdown).
    """

    cash = initial_cash
    position = 0
    equity_curve = []

    for index, row in df.iterrows():
        price = row["Close"]

        # Compra
        if row["position_change"] == 1 and cash > 0:
            position = cash / price
            cash = 0

        # Venta
        elif row["position_change"] == -1 and position > 0:
            cash = position * price
            position = 0

        equity = cash + position * price
        equity_curve.append(equity)

    equity_series = pd.Series(equity_curve, index=df.index)

    # === MÉTRICAS AVANZADAS ===
    final_equity = equity_series.iloc[-1]
    total_return_pct = (final_equity - initial_cash) / initial_cash * 100

    # CAGR
    num_years = (equity_series.index[-1] - equity_series.index[0]).days / 365.25
    cagr = (final_equity / initial_cash) ** (1 / num_years) - 1

    # Retornos diarios
    daily_returns = equity_series.pct_change().dropna()

    # Sharpe Ratio
    excess_returns = daily_returns - (risk_free_rate / 252)
    sharpe_ratio = np.sqrt(252) * excess_returns.mean() / excess_returns.std()

    # Max Drawdown
    rolling_max = equity_series.cummax()
    drawdown = (equity_series - rolling_max) / rolling_max
    max_drawdown = drawdown.min()

    return {
        "final_equity": final_equity,
        "total_return_pct": total_return_pct,
        "cagr": cagr,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown,
        "equity_curve": equity_series
    }
