import time
import math
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

from strategies.data_normalizer import normalize_columns
from strategies.strategy_loader import run_strategy
from broker_api.state_manager import state
from utils.trade_logger import log_trade
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from broker_api.alpaca_client import client
from utils.trade_logger import log_trade, init_trade_log
init_trade_log()

# ---------------------------
# CONFIG
# ---------------------------
SYMBOL = "AAPL"
STRATEGY = "sma"
PERIOD = "5d"
INTERVAL = "5m"
SLEEP_SECONDS = 30
WARMUP_BARS = 50

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
# RISK MANAGEMENT
# ---------------------------
RISK_PER_TRADE = 0.002         # arriesgar 0.2% del equity por trade
STOP_ATR_MULT = 1.5            # stop loss at 1.5x ATR
TP_ATR_MULT = 1.3              # take profit at 1.3x ATR
COOLDOWN_SECONDS = 120         # 2 minutos de cooldown entre trades
MIN_ATR_PCT = 0.0005           # mínimo 0.05% volatilidad
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

# Si quieres múltiples ventanas (más profesional)
TRADING_WINDOWS = [
    ((9, 45), (11, 30)),
    ((13, 30), (15, 45)),
]


# ---------------------------
# STATE
# ---------------------------
initialized = False
_last_trade_time = {}
_current_trade = None

# ---------------------------
# DATA
# ---------------------------
def get_latest_data(symbol):
    df = yf.download(symbol, period=PERIOD, interval=INTERVAL, auto_adjust=False)
    return normalize_columns(df)

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
def submit_bracket_order(symbol, qty, entry_price, atr):
    stop_price = round(entry_price - STOP_ATR_MULT * atr, 2)
    tp_price = round(entry_price + TP_ATR_MULT * atr, 2)

    order = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.GTC,
        order_class=OrderClass.BRACKET,
        take_profit={"limit_price": tp_price},
        stop_loss={"stop_price": stop_price}
    )

    resp = client.submit_order(order_data=order)
    mark_trade_time(symbol)

    print(
        f"BRACKET SENT | {symbol} qty={qty} "
        f"entry≈{entry_price:.2f} SL={stop_price} TP={tp_price} "
        f"id={getattr(resp, 'id', None)}"
    )

    global _current_trade
    _current_trade = {
    "symbol": symbol,
    "strategy": STRATEGY,
    "qty": qty,
    "entry_price": entry_price,
    "stop_loss": stop_price,
    "take_profit": tp_price,
    "timestamp_entry": int(time.time()),
    "order_id": getattr(resp, "id", None)
}
    

def check_trade_closed():
    global _current_trade

    if _current_trade is None:
        return

    symbol = _current_trade["symbol"]

    # Si ya no hay posición, el bracket cerró el trade
    if not is_in_position(symbol):
        try:
            last_trade = client.get_latest_trade(symbol)
            exit_price = float(last_trade.price)
        except Exception:
            exit_price = None

        entry_price = _current_trade["entry_price"]
        qty = _current_trade["qty"]

        if exit_price is not None:
            pnl_usd = (exit_price - entry_price) * qty
            pnl_pct = (exit_price - entry_price) / entry_price
        else:
            pnl_usd = pnl_pct = 0.0

        exit_reason = (
            "TP" if exit_price and exit_price >= _current_trade["take_profit"]
            else "SL"
        )

        timestamp_exit = int(time.time())

        trade_log = {
            "timestamp_entry": _current_trade["timestamp_entry"],
            "timestamp_exit": timestamp_exit,
            "symbol": symbol,
            "strategy": _current_trade["strategy"],
            "qty": qty,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "stop_loss": _current_trade["stop_loss"],
            "take_profit": _current_trade["take_profit"],
            "pnl_usd": round(pnl_usd, 2),
            "pnl_pct": round(pnl_pct * 100, 2),
            "duration_sec": timestamp_exit - _current_trade["timestamp_entry"],
            "exit_reason": exit_reason,
            "order_id": _current_trade["order_id"]
        }

        log_trade(trade_log)
        print("TRADE CLOSED & LOGGED:", trade_log)

        _current_trade = None


# ---------------------------
# MAIN LOOP
# ---------------------------
def main():
    global initialized
    print("LIVE BOT WITH BRACKET ORDERS | Strategy:", STRATEGY)

    strategy_params = PARAMS.get(STRATEGY, {})

    while True:
        try:
            check_trade_closed()
            df = get_latest_data(SYMBOL)
            if df.empty or len(df) < WARMUP_BARS:
                time.sleep(SLEEP_SECONDS)
                continue

            atr, atr_pct = compute_atr(df)
            last_close = float(df["close"].iloc[-1])

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

        time.sleep(SLEEP_SECONDS)

if __name__ == "__main__":
    main()
