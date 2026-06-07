"""
simple_backtester.py  –  v2.0
==============================
Refactorizado para trabajar con la columna 'signal' que generan
las estrategias actualizadas (sma, rsi, macd, bollinger).

Cambio principal respecto a v1
-------------------------------
- Antes esperaba 'position_change' (columna que ya no existe).
- Ahora lee 'signal' (1 = largo, -1 = corto/flat, 0 = hold) y
  deriva los cambios de posición internamente comparando signal
  actual vs signal anterior.

Señales soportadas
------------------
  signal = 1  → abrir/mantener largo
  signal = -1 → cerrar largo (o abrir corto si short_selling=True)
  signal = 0  → mantener estado actual

Métricas que retorna
--------------------
  final_equity, total_return_pct, cagr, sharpe_ratio, sortino_ratio,
  calmar_ratio, profit_factor, win_rate, max_drawdown, equity_curve
"""

import numpy as np
import pandas as pd


def backtest(
    df: pd.DataFrame,
    initial_capital: float = 10_000.0,
    commission: float = 0.001,       # 0.1% por operación
    slippage: float = 0.0005,        # 0.05% slippage
    position_size: float = 1.0,      # fracción del capital a invertir (1.0 = 100%)
    short_selling: bool = False,      # permitir posiciones cortas
    price_col: str = "close",
    signal_col: str = "signal",
) -> dict:
    """
    Ejecuta un backtest vectorizado sobre el DataFrame de una estrategia.

    Parámetros
    ----------
    df            : DataFrame con columnas de precio y señal
    initial_capital: Capital inicial en USD
    commission    : Comisión por operación (fracción, ej: 0.001 = 0.1%)
    slippage      : Slippage por operación (fracción)
    position_size : Fracción del capital a invertir por trade
    short_selling : Si True, permite posiciones cortas en signal=-1
    price_col     : Nombre de la columna de precio de cierre
    signal_col    : Nombre de la columna de señal

    Retorna
    -------
    dict con todas las métricas y la equity_curve como pd.Series
    """

    # ------------------------------------------------------------------
    # Validaciones
    # ------------------------------------------------------------------
    if price_col not in df.columns:
        raise KeyError(
            f"Columna de precio '{price_col}' no encontrada. "
            f"Disponibles: {list(df.columns)}"
        )
    if signal_col not in df.columns:
        raise KeyError(
            f"Columna de señal '{signal_col}' no encontrada. "
            f"Disponibles: {list(df.columns)}\n"
            f"Asegúrate de que la estrategia genera la columna '{signal_col}'."
        )

    df = df.copy()
    prices  = df[price_col].values
    signals = df[signal_col].values
    n       = len(df)

    # ------------------------------------------------------------------
    # Simulación barra a barra
    # ------------------------------------------------------------------
    cash          = initial_capital
    position      = 0          # número de acciones en cartera
    equity        = np.zeros(n)
    trades        = []         # lista de (pnl_por_trade)

    entry_price   = 0.0
    prev_signal   = 0

    for i in range(n):
        price  = prices[i]
        signal = int(signals[i])

        # Detectar cambio de señal
        signal_changed = (signal != prev_signal)

        # ---------- CERRAR posición larga ----------
        should_close_long = (
            position > 0
            and signal_changed
            and signal != 1
        )
        if should_close_long:
            exit_price = price * (1 - slippage)
            proceeds   = position * exit_price * (1 - commission)
            pnl        = proceeds - (position * entry_price * (1 + commission + slippage))
            trades.append(pnl)
            cash      += proceeds
            position   = 0
            entry_price = 0.0

        # ---------- CERRAR posición corta ----------
        if short_selling:
            should_close_short = (
                position < 0
                and signal_changed
                and signal != -1
            )
            if should_close_short:
                exit_price = price * (1 + slippage)
                cost       = abs(position) * exit_price * (1 + commission)
                pnl        = (abs(position) * entry_price) - cost
                trades.append(pnl)
                cash      += (abs(position) * entry_price) + pnl
                position   = 0
                entry_price = 0.0

        # ---------- ABRIR posición larga ----------
        should_open_long = (
            signal == 1
            and position == 0
            and cash > 0
            and signal_changed
        )
        if should_open_long:
            buy_price  = price * (1 + slippage)
            invest     = cash * position_size
            shares     = (invest / buy_price) * (1 - commission)
            if shares > 0:
                position    = shares
                entry_price = buy_price
                cash       -= invest

        # ---------- ABRIR posición corta ----------
        if short_selling:
            should_open_short = (
                signal == -1
                and position == 0
                and cash > 0
                and signal_changed
            )
            if should_open_short:
                sell_price  = price * (1 - slippage)
                invest      = cash * position_size
                shares      = (invest / sell_price) * (1 - commission)
                if shares > 0:
                    position    = -shares
                    entry_price = sell_price
                    cash       -= invest   # margen reservado

        # ---------- Calcular equity de esta barra ----------
        if position > 0:
            equity[i] = cash + position * price
        elif position < 0 and short_selling:
            # ganancia del short = (entry - current) * |position|
            equity[i] = cash + abs(position) * (entry_price - price)
        else:
            equity[i] = cash

        prev_signal = signal

    # Cerrar posición abierta al final si queda alguna
    if position != 0:
        final_price = prices[-1]
        if position > 0:
            proceeds = position * final_price * (1 - commission - slippage)
            pnl      = proceeds - (position * entry_price * (1 + commission + slippage))
            trades.append(pnl)
            equity[-1] = cash + proceeds
        elif position < 0 and short_selling:
            cost = abs(position) * final_price * (1 + commission + slippage)
            pnl  = (abs(position) * entry_price) - cost
            trades.append(pnl)
            equity[-1] = cash + (abs(position) * entry_price) + pnl

    # ------------------------------------------------------------------
    # Construir equity_curve como Series con el índice del DataFrame
    # ------------------------------------------------------------------
    equity_curve = pd.Series(equity, index=df.index, name="equity")
    # Rellenar ceros iniciales (antes de la primera señal) con capital inicial
    equity_curve = equity_curve.replace(0, np.nan).ffill().fillna(initial_capital)

    # ------------------------------------------------------------------
    # Métricas
    # ------------------------------------------------------------------
    final_equity     = float(equity_curve.iloc[-1])
    total_return_pct = (final_equity / initial_capital - 1) * 100

    # CAGR
    returns_series = equity_curve.pct_change().dropna()
    n_days         = len(returns_series)
    years          = n_days / 252
    if years > 0 and final_equity > 0:
        cagr = (final_equity / initial_capital) ** (1 / years) - 1
    else:
        cagr = 0.0

    # Sharpe Ratio (anualizado, rf=0)
    if returns_series.std() != 0:
        sharpe_ratio = float(np.sqrt(252) * returns_series.mean() / returns_series.std())
    else:
        sharpe_ratio = 0.0

    # Sortino Ratio
    downside = returns_series[returns_series < 0]
    if len(downside) > 0 and downside.std() != 0:
        sortino_ratio = float(np.sqrt(252) * returns_series.mean() / downside.std())
    else:
        sortino_ratio = 0.0

    # Max Drawdown
    roll_max     = equity_curve.cummax()
    drawdown     = (equity_curve - roll_max) / roll_max
    max_drawdown = float(drawdown.min())

    # Calmar Ratio
    if max_drawdown != 0:
        calmar_ratio = float(cagr / abs(max_drawdown))
    else:
        calmar_ratio = 0.0

    # Win Rate y Profit Factor
    if len(trades) > 0:
        wins        = [t for t in trades if t > 0]
        losses      = [t for t in trades if t <= 0]
        win_rate    = len(wins) / len(trades) * 100
        gross_profit = sum(wins)
        gross_loss   = abs(sum(losses))
        profit_factor = gross_profit / gross_loss if gross_loss != 0 else float("inf")
    else:
        win_rate      = 0.0
        profit_factor = 0.0

    return {
        "final_equity":     round(final_equity, 2),
        "total_return_pct": round(total_return_pct, 2),
        "cagr":             round(cagr, 4),
        "sharpe_ratio":     round(sharpe_ratio, 4),
        "sortino_ratio":    round(sortino_ratio, 4),
        "calmar_ratio":     round(calmar_ratio, 4),
        "profit_factor":    round(profit_factor, 4),
        "win_rate":         round(win_rate, 2),
        "max_drawdown":     round(max_drawdown, 4),
        "equity_curve":     equity_curve,
        "n_trades":         len(trades),
    }