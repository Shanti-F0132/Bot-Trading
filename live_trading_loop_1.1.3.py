import time
import math
import json
import os

import pandas as pd
from datetime import datetime
import pytz
from alpaca.trading.requests import GetOrdersRequest, MarketOrderRequest
from alpaca.trading.enums import OrderStatus, OrderSide, TimeInForce, OrderClass, OrderType

from strategies.data_normalizer import normalize_columns
from strategies.strategy_loader import run_strategy
from broker_api.state_manager import state
from broker_api.alpaca_client import client
from utils.trade_logger import log_trade, init_trade_log
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.requests import StockLatestTradeRequest
init_trade_log()

# Archivo de persistencia de estado (sobrevive reinicios del bot)
STATE_FILE = "outputs/bot_state.json"

# Mapeo de INTERVAL config → TimeFrame de Alpaca
INTERVAL_MAP = {
    "1m":  TimeFrame.Minute,
    "5m":  TimeFrame(5,  TimeFrameUnit.Minute),
    "15m": TimeFrame(15, TimeFrameUnit.Minute),
    "1h":  TimeFrame.Hour,
    "1d":  TimeFrame.Day
}

# ---------------------------
# CONFIG
# ---------------------------
SYMBOL = "NVDA"
STRATEGY = "sma"   # "sma", "macd", "rsi", "bollinger", "combo_sma_macd"
PERIOD = "5d"
INTERVAL = "5m"
SLEEP_SECONDS = 30
WARMUP_BARS = 100

PARAMS = {
    "sma": {"short": 5, "long": 20},
    "macd": {"fast": 6, "slow": 13, "signal": 5},
    "rsi": {"window": 7},
    "bollinger": {"window": 10, "num_std": 2},
    "combo_sma_macd": {
        "sma_short": 20, "sma_long": 50,
        "macd_fast": 12, "macd_slow": 26, "macd_signal": 9
    }
}

# ---------------------------
# RISK MANAGEMENT
# ---------------------------
RISK_PER_TRADE = 0.002         # arriesgar 0.2% del equity por trade
STOP_ATR_MULT = 1.2            # stop loss at 1.2x ATR
TP_ATR_MULT = 2.1              # take profit at 2.1x ATR
COOLDOWN_SECONDS = 300         # 5 minutos de cooldown entre trades
MIN_ATR_PCT = 0.0001           # mínimo 0.01% volatilidad
ATR_PERIOD = 14                # para calcular volatilidad
MIN_QTY = 1                    # qty mínimo a comprar
MAX_QTY = 1000                 # cap por seguridad


# ---------------------------
# SESSION / TIME FILTERS
# ---------------------------
USE_SESSION_FILTER = True

MARKET_TZ = "US/Eastern"

# Horarios válidos (ET)
SESSION_START = (9, 45)
SESSION_END   = (15, 45)

# Si quieres múltiples ventanas
TRADING_WINDOWS = [
    ((9, 45), (12, 30)),
    ((13, 30), (15, 45))
]

#TRADING_WINDOWS = [
 #   (9, 45), (15, 45)
#]

# ---------------------------
# STATE
# ---------------------------
initialized = False
_last_trade_time = {}
_current_trade = None

# ---------------------------
# STATE PERSISTENCE
# ---------------------------
def save_state():
    """Escribe _current_trade y _last_trade_time en disco."""
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        payload = {
            "current_trade":   _current_trade,
            "last_trade_time": _last_trade_time,
        }
        with open(STATE_FILE, "w") as f:
            json.dump(payload, f, indent=2)
    except Exception as e:
        print("State save error:", e)

def load_state():
    """
    Lee el estado del disco al arrancar.
    Si no existe el archivo (primera vez), no hace nada.
    """
    global _current_trade, _last_trade_time
    if not os.path.exists(STATE_FILE):
        return
    try:
        with open(STATE_FILE, "r") as f:
            payload = json.load(f)
        _current_trade   = payload.get("current_trade")
        _last_trade_time = payload.get("last_trade_time", {})
        if _current_trade:
            print(f"State recovered — open trade detected: {_current_trade['symbol']} "
                  f"order_id={_current_trade.get('order_id')}")
        if _last_trade_time:
            print(f"Cooldown state recovered: {_last_trade_time}")
    except Exception as e:
        print("State load error (starting fresh):", e)

# ---------------------------
# DATA
# ---------------------------

data_client = StockHistoricalDataClient(
    client._api_key,
    client._secret_key
)

def get_latest_data(symbol):
    tf = INTERVAL_MAP.get(INTERVAL, TimeFrame.Minute)
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=tf,
        limit=300
    )
    bars = data_client.get_stock_bars(request).df

    if bars.empty:
        return bars

    bars = bars.reset_index()
    bars.rename(columns={
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume"
    }, inplace=True)

    return normalize_columns(bars)

def get_live_price(symbol):
    trade = data_client.get_stock_latest_trade(
        StockLatestTradeRequest(symbol_or_symbols=symbol)
    )
    return float(trade[symbol].price)

def clamp_change(x):
    return max(-1, min(1, int(x)))

def compute_atr(df, period=ATR_PERIOD):
    if len(df) < period + 1:
        return 0.0, 0.0

    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)

    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)

    atr = tr.rolling(period).mean().iloc[-1]
    atr_pct = atr / close.iloc[-1]
    return float(atr), float(atr_pct)

# ---------------------------
# BROKER HELPERS
# ---------------------------
def get_account_equity():
    try:
        acct = client.get_account()
        return float(acct.equity)
    except Exception:
        return None

def compute_position_size(equity, entry_price, atr):
    risk_amount = equity * RISK_PER_TRADE
    dollar_risk_per_share = atr * STOP_ATR_MULT
    if dollar_risk_per_share <= 0:
        return MIN_QTY
    qty = math.floor(risk_amount / dollar_risk_per_share)
    return max(MIN_QTY, min(MAX_QTY, qty))

def has_recent_trade(symbol):
    t = _last_trade_time.get(symbol)
    return t and (time.time() - t) < COOLDOWN_SECONDS

def mark_trade_time(symbol):
    _last_trade_time[symbol] = time.time()
    save_state()

def is_in_position(symbol):
    try:
        for pos in client.get_all_positions():
            if pos.symbol == symbol and float(pos.qty) > 0:
                return True
        return False
    except Exception:
        return False
    
def is_within_trading_hours():
    if not USE_SESSION_FILTER:
        return True

    tz = pytz.timezone(MARKET_TZ)
    now = datetime.now(tz)

    # Market closed on weekends
    if now.weekday() >= 5:
        return False

    current_time = (now.hour, now.minute)

    for start, end in TRADING_WINDOWS:
        if start <= current_time <= end:
            return True

    return False

# ---------------------------
# BRACKET ORDER
# ---------------------------
def _wait_for_fill(order_id, timeout=12, interval=2):
    """
    Polling de la orden padre hasta que esté FILLED.
    Retorna el filled_avg_price real, o None si se agota el timeout.
    """
    elapsed = 0
    while elapsed < timeout:
        try:
            order = client.get_order_by_id(order_id)
            if order.status == OrderStatus.FILLED and order.filled_avg_price:
                return float(order.filled_avg_price)
        except Exception as e:
            print(f"Polling fill error: {e}")
        time.sleep(interval)
        elapsed += interval
    return None

def submit_bracket_order(symbol, qty, entry_price, atr):
    """
    Envía la bracket order con retry (máx 3 intentos, backoff 2s/4s).
    Antes de cada reintento verifica que no se haya abierto posición
    para evitar duplicados. Usa el filled_avg_price real como entry.
    """
    stop_price = round(entry_price - STOP_ATR_MULT * atr, 2)
    tp_price   = round(entry_price + TP_ATR_MULT   * atr, 2)

    order = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.GTC,
        order_class=OrderClass.BRACKET,
        take_profit={"limit_price": tp_price},
        stop_loss={"stop_price": stop_price}
    )

    resp        = None
    last_error  = None
    max_retries = 3

    for attempt in range(1, max_retries + 1):
        try:
            # Anti-duplicado: si ya hay posición, la orden anterior llegó
            if attempt > 1 and is_in_position(symbol):
                print(f"Position already open after attempt {attempt - 1} — skipping retry")
                break

            resp = client.submit_order(order_data=order)
            break  # éxito — salir del loop

        except Exception as e:
            last_error = e
            print(f"submit_bracket_order attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                backoff = attempt * 2   # 2s, 4s
                print(f"Retrying in {backoff}s...")
                time.sleep(backoff)

    if resp is None:
        # Verificación final: puede que la última orden llegó igual
        if is_in_position(symbol):
            print("Order likely went through despite error — position detected")
        else:
            raise RuntimeError(
                f"submit_bracket_order failed after {max_retries} attempts: {last_error}"
            )
        return

    order_id = getattr(resp, "id", None)
    mark_trade_time(symbol)

    # --- Fix #6: obtener el fill real en lugar del precio pre-orden ---
    real_entry = _wait_for_fill(order_id)
    if real_entry is None:
        print(f"Fill not confirmed in time — using estimated price {entry_price:.2f}")
        real_entry = entry_price
    else:
        print(f"Fill confirmed: real entry = {real_entry:.2f} (estimated was {entry_price:.2f})")

    print(
        f"BRACKET SENT | {symbol} qty={qty} "
        f"entry={real_entry:.2f} SL={stop_price} TP={tp_price} "
        f"id={order_id}"
    )

    global _current_trade
    _current_trade = {
        "symbol":          symbol,
        "strategy":        STRATEGY,
        "qty":             qty,
        "entry_price":     real_entry,
        "stop_loss":       stop_price,
        "take_profit":     tp_price,
        "timestamp_entry": int(time.time()),
        "order_id":        order_id
    }
    save_state()
    

def check_trade_closed():
    global _current_trade

    if _current_trade is None:
        return

    symbol = _current_trade["symbol"]

    # Posición aún abierta — nada que hacer
    if is_in_position(symbol):
        return

    print("Position closed — resolving exit via bracket order legs")

    order_id = _current_trade.get("order_id")
    if not order_id:
        print("No order_id stored — cannot resolve exit order")
        return

    try:
        # Traer la orden padre del bracket directamente por ID
        parent_order = client.get_order_by_id(order_id)
    except Exception as e:
        print("Error fetching parent order:", e)
        return

    # Las legs del bracket vienen en parent_order.legs
    legs = getattr(parent_order, "legs", None) or []

    exit_order = None
    for leg in legs:
        if (
            leg.side == OrderSide.SELL
            and leg.status == OrderStatus.FILLED
            and leg.filled_avg_price is not None
        ):
            exit_order = leg
            break

    if exit_order is None:
        print("Exit leg not filled yet — will retry next loop")
        return

    exit_price  = float(exit_order.filled_avg_price)
    entry_price = _current_trade["entry_price"]
    qty         = _current_trade["qty"]

    pnl_usd = (exit_price - entry_price) * qty
    pnl_pct = (exit_price - entry_price) / entry_price

    # OrderType.LIMIT → TP | OrderType.STOP → SL
    exit_reason = "TP" if exit_order.type == OrderType.LIMIT else "SL"

    timestamp_exit = int(time.time())

    trade_log = {
        "timestamp_entry": _current_trade["timestamp_entry"],
        "timestamp_exit":  timestamp_exit,
        "symbol":          symbol,
        "strategy":        _current_trade["strategy"],
        "qty":             qty,
        "entry_price":     entry_price,
        "exit_price":      exit_price,
        "stop_loss":       _current_trade["stop_loss"],
        "take_profit":     _current_trade["take_profit"],
        "pnl_usd":         round(pnl_usd, 2),
        "pnl_pct":         round(pnl_pct * 100, 2),
        "duration_sec":    timestamp_exit - _current_trade["timestamp_entry"],
        "exit_reason":     exit_reason,
        "order_id":        order_id
    }

    success = log_trade(trade_log)

    if success:
        print("TRADE CLOSED & LOGGED:", trade_log)
        _current_trade = None
        save_state()
    else:
        print("Trade closed but NOT logged — will retry next loop")



# ---------------------------
# MAIN LOOP
# ---------------------------
def main():
    global initialized
    print("LIVE BOT WITH BRACKET ORDERS | Strategy:", STRATEGY)

    load_state()   # recuperar _current_trade y cooldowns si el bot fue reiniciado

    strategy_params = PARAMS.get(STRATEGY, {})

    while True:
        try:
            df = get_latest_data(SYMBOL)
            if df.empty or len(df) < WARMUP_BARS:
                time.sleep(SLEEP_SECONDS)
                continue

            atr, atr_pct = compute_atr(df)
            last_close = get_live_price(SYMBOL)

            if atr_pct < MIN_ATR_PCT:
                print("ATR too low — skipping")
                time.sleep(SLEEP_SECONDS)
                continue

            df_out = run_strategy(df, STRATEGY, **strategy_params)
            last = df_out.iloc[-1]

            action = 0

            if "signal" in df_out.columns:
                curr = int(last.get("signal", 0))
                prev = state.get_prev(STRATEGY)

                if not initialized:
                    state.set_prev(STRATEGY, curr)
                    initialized = True
                    time.sleep(SLEEP_SECONDS)
                    continue

                change = clamp_change(curr - prev)
                action = 1 if change == 1 else 0
                state.set_prev(STRATEGY, curr)

            print(f"Price={last_close:.2f} Action={action}")

            if action == 1:
                if not is_within_trading_hours():
                    print("Outside trading session - skipping BUY")
                    continue

                if has_recent_trade(SYMBOL):
                    print("Cooldown active")
                    continue

                if is_in_position(SYMBOL):
                    print("Already in position")
                    continue

                equity = get_account_equity()
                qty = compute_position_size(equity, last_close, atr) if equity else MIN_QTY
                submit_bracket_order(SYMBOL, qty, last_close, atr)

        except Exception as e:
            print("Loop error:", e)

        finally:
            check_trade_closed()

        time.sleep(SLEEP_SECONDS)

if __name__ == "__main__":
    main()