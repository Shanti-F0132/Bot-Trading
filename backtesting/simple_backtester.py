import pandas as pd
import numpy as np

def backtest(
    df,
    initial_cash=10000,
    commission=0.001,
    slippage=0.0005,
    risk_free_rate=0.02,
    position_size=1.0,
    stop_loss=None,
    take_profit=None,
    fixed_risk=None   # NUEVO: riesgo fijo por operación (ej: 0.01 = 1%)
):
    """
    Backtester con gestión avanzada de riesgo:
    - Comisiones
    - Slippage
    - Position sizing fijo o riesgo fijo por operación
    - Stop-Loss y Take-Profit opcionales
    - Métricas avanzadas
    """

    cash = initial_cash
    position = 0
    entry_price = None
    equity_curve = []

    for index, row in df.iterrows():
        price = row["Close"]

        price_with_slippage_buy = price * (1 + slippage)
        price_with_slippage_sell = price * (1 - slippage)

        # === COMPRA ===
        if row["position_change"] == 1 and cash > 0 and position == 0:
            if fixed_risk and stop_loss:  
                # Monto máximo a arriesgar (ej: 1% del capital)
                risk_capital = cash * fixed_risk
                risk_per_share = price * stop_loss
                shares = risk_capital / risk_per_share if risk_per_share > 0 else 0
                investable_cash = shares * price
            else:
                # Position sizing fijo tradicional
                investable_cash = cash * position_size

            if investable_cash > 0:
                position = (investable_cash * (1 - commission)) / price_with_slippage_buy
                cash -= investable_cash
                entry_price = price_with_slippage_buy

        # === VENTA por señal ===
        elif row["position_change"] == -1 and position > 0:
            cash += position * price_with_slippage_sell * (1 - commission)
            position = 0
            entry_price = None

        # === VENTA por STOP-LOSS o TAKE-PROFIT ===
        elif position > 0 and entry_price is not None:
            pnl_pct = (price - entry_price) / entry_price

            if stop_loss is not None and pnl_pct <= -stop_loss:
                cash += position * price_with_slippage_sell * (1 - commission)
                position = 0
                entry_price = None
            elif take_profit is not None and pnl_pct >= take_profit:
                cash += position * price_with_slippage_sell * (1 - commission)
                position = 0
                entry_price = None

        # === EQUITY TOTAL ===
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
