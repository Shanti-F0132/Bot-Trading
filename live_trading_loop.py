import time
import math
import yfinance as yf
import pandas as pd

from strategies.data_normalizer import normalize_columns
from strategies.strategy_loader import run_strategy
from broker_api.state_manager import state
from utils.trade_executor import handle_signal
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from broker_api.alpaca_client import client  # cliente alpaca ya existente en tu proyecto

# ---------------------------
# CONFIG
# ---------------------------
SYMBOL = "AAPL"
STRATEGY = "sma"  # "sma", "macd", "rsi", "bollinger", "combo_sma_macd"
PERIOD = "1d"
INTERVAL = "5m"
SLEEP_SECONDS = 30

# PARAMS de estrategias
PARAMS = {
    "sma": {"short": 5, "long": 20},
    "macd": {"fast": 6, "slow": 13, "signal": 5},
    "rsi": {"window": 7},
    "bollinger": {"window": 10, "num_std": 2},
    "combo_sma_macd": {
        "sma_short": 5, "sma_long": 20,
        "macd_fast": 6, "macd_slow": 13, "macd_signal": 5
    }
}

# ---------------------------
# RISK MANAGEMENT / EXECUTION POLICY
# ---------------------------
RISK_PER_TRADE = 0.005         # 0.5% del equity por operación (ajusta)
STOP_LOSS_PCT = 0.006          # 0.6% stop-loss por defecto (ajusta)
TAKE_PROFIT_PCT = 0.0010        # 0.1% take-profit por defecto (ajusta)
COOLDOWN_SECONDS = 60 * 3     # 3 minutos entre trades sobre el mismo símbolo
MIN_ATR_PCT = 0.0005           # ATR/price mínimo para operar (evita ultra-bajo volumen/noise)
ATR_PERIOD = 14                # para calcular volatilidad
MIN_QTY = 1                    # qty mínimo a comprar
MAX_QTY = 1000                 # cap por seguridad

# ---------------------------
# Estado runtime (persistente mientras el proceso corre)
# ---------------------------
initialized = False            # warm-up
_last_trade_time = {}         # symbol -> last trade timestamp
_entry_info = {}              # symbol -> dict(entry_price, stop_price, tp_price, qty)
# ---------------------------


def get_latest_data(symbol):
    df = yf.download(symbol, period=PERIOD, interval=INTERVAL, auto_adjust=True)
    df = normalize_columns(df)
    return df


def clamp_change(x):
    if x > 1:
        return 1
    if x < -1:
        return -1
    return int(x)


def compute_atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> float:
    """
    Returns the most recent ATR value (not normalized) and ATR_pct (atr/close).
    """
    if len(df) < period + 1:
        return 0.0, 0.0

    high = df["high"]
    low = df["low"]
    close = df["close"]

    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean().iloc[-1]
    atr_pct = atr / close.iloc[-1] if close.iloc[-1] != 0 else 0.0
    return float(atr), float(atr_pct)


def get_account_equity():
    """
    Intenta obtener el equity/cash del account desde Alpaca client.
    Si falla, retorna None y el loop usará fallback de qty fijo.
    """
    try:
        acct = client.get_account()
        # try common attributes
        equity = None
        if hasattr(acct, "equity"):
            equity = float(acct.equity)
        elif hasattr(acct, "cash"):
            equity = float(acct.cash)
        elif hasattr(acct, "buying_power"):
            equity = float(acct.buying_power)
        return equity
    except Exception:
        return None


def compute_position_size(equity, entry_price, stop_loss_pct):
    """
    Compute qty based on risk per trade and stop distance:
    qty = (equity * RISK_PER_TRADE) / (entry_price * stop_loss_pct)
    """
    try:
        risk_amount = equity * RISK_PER_TRADE
        dollar_risk_per_share = entry_price * stop_loss_pct
        if dollar_risk_per_share <= 0:
            return MIN_QTY
        qty = math.floor(risk_amount / dollar_risk_per_share)
        if qty < MIN_QTY:
            qty = MIN_QTY
        if qty > MAX_QTY:
            qty = MAX_QTY
        return int(qty)
    except Exception:
        return MIN_QTY


def has_recent_trade(symbol):
    t = _last_trade_time.get(symbol)
    if t is None:
        return False
    return (time.time() - t) < COOLDOWN_SECONDS


def mark_trade_time(symbol):
    _last_trade_time[symbol] = time.time()


def build_entry_levels(entry_price, stop_loss_pct, take_profit_pct):
    stop_price = entry_price * (1.0 - stop_loss_pct)
    tp_price = entry_price * (1.0 + take_profit_pct)
    return float(stop_price), float(tp_price)


def update_entry_info(symbol, entry_price, stop_price, tp_price, qty):
    _entry_info[symbol] = {
        "entry_price": float(entry_price),
        "stop_price": float(stop_price),
        "tp_price": float(tp_price),
        "qty": int(qty),
        "entered_at": time.time()
    }


def clear_entry_info(symbol):
    if symbol in _entry_info:
        del _entry_info[symbol]


def is_in_position(symbol):
    """
    Check Alpaca for an open position for symbol.
    Returns (bool, qty, avg_entry_price) or (False, 0, None)
    """
    try:
        pos = client.get_position(symbol)
        qty = int(float(pos.qty))
        avg_entry = float(pos.avg_entry_price) if hasattr(pos, "avg_entry_price") else float(pos.avg_entry_price or 0)
        return True, qty, avg_entry
    except Exception:
        return False, 0, None


def monitor_stop_take(symbol, last_price):
    info = _entry_info.get(symbol)
    if not info:
        return False

    stop_price = info["stop_price"]
    tp_price = info["tp_price"]

    if last_price <= stop_price or last_price >= tp_price:
        print(f"SL/TP hit for {symbol}: price={last_price} stop={stop_price} tp={tp_price}. Closing position.")
        safe_execute_sell(symbol)
        clear_entry_info(symbol)
        mark_trade_time(symbol)
        return True
    return False


def safe_execute_buy(symbol, qty, entry_price):
    try:
        handle_signal(1, symbol, qty=qty)   #  <-- ahora sí pasa qty correctamente

        stop_price, tp_price = build_entry_levels(entry_price, STOP_LOSS_PCT, TAKE_PROFIT_PCT)
        update_entry_info(symbol, entry_price, stop_price, tp_price, qty)
        mark_trade_time(symbol)
        print(f"Executed BUY {symbol} qty={qty} entry={entry_price} stop={stop_price} tp={tp_price}")
    except Exception as e:
        print("Error executing buy:", e)



def safe_execute_sell(symbol):
    try:
        # Confirmar posición real en broker
        in_pos, qty, avg_entry = is_in_position(symbol)

        if not in_pos or qty <= 0:
            print(f"No open position to SELL for {symbol}.")
            return

        # Crear orden MARKET SELL explícita
        order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )

        resp = client.submit_order(order_data=order)

        print(
            f"SELL order submitted | symbol={symbol} qty={qty} order_id={resp.id}"
        )

        # Limpiar estado SOLO después de enviar orden
        clear_entry_info(symbol)
        mark_trade_time(symbol)

    except Exception as e:
        print("Error executing SELL:", e)


# ---------------------------
# MAIN LOOP (mejorado)
# ---------------------------
def main():
    global initialized
    print("Starting live loop with risk management:", STRATEGY, SYMBOL)
    strategy_params = PARAMS.get(STRATEGY, {})

    while True:
        try:
            df = get_latest_data(SYMBOL)
            if df.empty:
                print("No data returned, sleeping...")
                time.sleep(SLEEP_SECONDS)
                continue

            # compute ATR filter
            atr, atr_pct = compute_atr(df)
            last_close = float(df["close"].iloc[-1])

            # skip if volatility too low
            if atr_pct < MIN_ATR_PCT:
                print(f"ATR too low ({atr_pct:.6f}) — skipping this iteration.")
                time.sleep(SLEEP_SECONDS)
                continue

            # run strategy
            df_out = run_strategy(df, STRATEGY, **strategy_params)
            last = df_out.iloc[-1]

            action = 0  # -1 sell, 0 hold, 1 buy

            # ---------------- combo_sma_macd handling ----------------
            if STRATEGY == "combo_sma_macd":
                sma_curr = int(last.get("sma_signal", 0))
                macd_curr = int(last.get("macd_signal", 0))

                sma_prev = state.get_prev("sma")
                macd_prev = state.get_prev("macd")

                sma_change = clamp_change(sma_curr - sma_prev)
                macd_change = clamp_change(macd_curr - macd_prev)

                # WARM-UP
                if not initialized:
                    print("Warm-up: initializing state (no trades this iteration).")
                    state.set_prev("sma", sma_curr)
                    state.set_prev("macd", macd_curr)
                    initialized = True
                    time.sleep(SLEEP_SECONDS)
                    continue

                # decide action (conservador: requiere cruce)
                if sma_curr == 1 and macd_curr == 1 and (sma_change == 1 or macd_change == 1):
                    action = 1
                elif sma_curr == -1 and macd_curr == -1 and (sma_change == -1 or macd_change == -1):
                    action = -1

                state.set_prev("sma", sma_curr)
                state.set_prev("macd", macd_curr)

                print("Latest (close):", last_close)
                print(f"sma_curr={sma_curr} macd_curr={macd_curr} sma_change={sma_change} macd_change={macd_change}")

            # ---------------- simple strategies handling ----------------
            else:
                if "signal" in df_out.columns:
                    curr = int(last.get("signal", 0))
                elif "position_change" in df_out.columns:
                    prev = state.get_prev(STRATEGY)
                    curr = prev + int(last.get("position_change", 0))
                    if curr > 1:
                        curr = 1
                    if curr < -1:
                        curr = -1
                else:
                    curr = 0

                prev = state.get_prev(STRATEGY)

                # WARM-UP
                if not initialized:
                    print("Warm-up: initializing state for", STRATEGY, "(no trades this iteration).")
                    state.set_prev(STRATEGY, curr)
                    initialized = True
                    time.sleep(SLEEP_SECONDS)
                    continue

                change = clamp_change(curr - prev)
                if change == 1:
                    action = 1
                elif change == -1:
                    action = -1
                else:
                    action = 0

                state.set_prev(STRATEGY, curr)
                print("Latest (close, curr):", last_close, curr, "prev:", prev, "change:", change)

            # ---------------- check open position & cooldown ----------------
            in_pos, pos_qty, pos_entry = is_in_position(SYMBOL)

            # PRIORIDAD ABSOLUTA: si hay posición y hay señal de SELL, cerrar inmediatamente
            if action == -1 and in_pos:
                safe_execute_sell(SYMBOL)
                continue
            
            # If we have tracked entry info, monitor SL/TP
            monitor_stop_take(SYMBOL, last_close)

            # If a trade was recently executed, skip new entries for this symbol
            if action == 1:
                if has_recent_trade(SYMBOL):
                    print("Skipping BUY due cooldown.")
                    action = 0

            if action == -1:
                # If no position open, skipping sell
                if not in_pos:
                    print("No open position to close (skipping SELL).")
                    action = 0

            # ---------------- EXECUTION ----------------
            if action == 1:
                # position sizing
                equity = get_account_equity()
                if equity is None:
                    print("Could not get account equity, using MIN_QTY.")
                    qty = MIN_QTY
                else:
                    qty = compute_position_size(equity, last_close, STOP_LOSS_PCT)

                # double-check qty validity
                if qty <= 0:
                    qty = MIN_QTY

                # if there's already a position, avoid doubling (conservative)
                if in_pos:
                    print(f"Already in position qty={pos_qty}: skipping additional BUY.")
                else:
                    # perform buy and register entry info
                    safe_execute_buy(SYMBOL, qty, last_close)
            else:
                print("HOLD -> no action")

        except Exception as e:
            print("Loop error:", e)

        time.sleep(SLEEP_SECONDS)


if __name__ == "__main__":
    main()
