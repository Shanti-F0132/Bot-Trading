import pandas as pd
import numpy as np

def backtest(df, initial_cash=10000, commission=0.001, slippage=0.0005, 
             risk_free_rate=0.02, position_size=1.0):
    """
    Backtester con:
    - Comisiones
    - Slippage
    - Position sizing (porcentaje de capital invertido por trade)
    - Métricas avanzadas
    
    Parámetros:
    -----------
    df : DataFrame con ['Close', 'position_change']
    initial_cash : float, capital inicial
    commission : float, % cobrado en cada trade
    slippage : float, % de diferencia en el precio de ejecución
    risk_free_rate : float, tasa libre de riesgo anual
    position_size : float, fracción del capital a invertir (1.0 = 100%, 0.5 = 50%)
    """

    cash = initial_cash
    position = 0
    equity_curve = []

    for index, row in df.iterrows():
        price = row["Close"]
        price_with_slippage = price * (1 + slippage if row["position_change"] == 1 else (1 - slippage))

        # Compra con fracción del capital
        if row["position_change"] == 1 and cash > 0:
            investable_cash = cash * position_size
            position = (investable_cash * (1 - commission)) / price_with_slippage
            cash -= investable_cash  # mantenemos el resto en reserva

        # Venta
        elif row["position_change"] == -1 and position > 0:
            cash += position * price_with_slippage * (1 - commission)
            position = 0

        equity = cash + position * price
        equity_curve.append(equity)

    equity_series = pd.Series(equity_curve, index=df.index)

    # === MÉTRICAS ===
    final_equity = equity_series.iloc[-1]
    total_return_pct = (final_equity - initial_cash) / initial_cash * 100

    num_years = (equity_series.index[-1] - equity_series.index[0]).days / 365.25
    cagr = (final_equity / initial_cash) ** (1 / num_years) - 1

    daily_returns = equity_series.pct_change().dropna()
    excess_returns = daily_returns - (risk_free_rate / 252)
    sharpe_ratio = np.sqrt(252) * excess_returns.mean() / excess_returns.std()

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
