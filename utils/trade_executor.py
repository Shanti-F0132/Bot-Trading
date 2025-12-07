# trade_executor.py
import os
import time
import logging
from decimal import Decimal

from broker_api.alpaca_client import client
from alpaca.trading.requests import MarketOrderRequest, OrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.client import TradingClient
from alpaca.common.exceptions import APIError

# Config desde env
LIVE = os.getenv("LIVE_TRADING", "0") == "1"   # si LIVE_TRADING=1 ejecuta en real, si no, paper
MAX_POSITION_PCT = float(os.getenv("MAX_POSITION_PCT", "0.1"))  # % del capital por operación (ej: 0.1 -> 10%)
MAX_POSITIONS_OPEN = int(os.getenv("MAX_POSITIONS_OPEN", "5"))
MIN_CASH_BUFFER = float(os.getenv("MIN_CASH_BUFFER", "100"))  # deja este cash libre
ORDER_THROTTLE_SEC = float(os.getenv("ORDER_THROTTLE_SEC", "1.0"))  # evitar ordenar muy seguido

# Logging
LOGFILE = os.getenv("TRADING_LOG", "trades.log")
logging.basicConfig(filename=LOGFILE,
                    level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

_last_order_time = 0.0

def _throttle():
    global _last_order_time
    now = time.time()
    dt = now - _last_order_time
    if dt < ORDER_THROTTLE_SEC:
        time.sleep(ORDER_THROTTLE_SEC - dt)
    _last_order_time = time.time()

def get_account():
    return client.get_account()

def get_cash_available() -> float:
    acct = get_account()
    try:
        return float(acct.cash)  # cash disponible
    except Exception:
        # fallback to equity - positions
        return float(acct.equity)

def list_open_positions():
    try:
        return client.get_all_positions()
    except Exception as e:
        logger.exception("Error listando posiciones: %s", e)
        return []

def get_position_for(symbol: str):
    try:
        return client.get_position(symbol)
    except Exception:
        return None

def _can_open_new_position(symbol: str, qty: int = 1) -> bool:
    # Regla simple: no abrir si ya existe posición en el mismo símbolo
    pos = get_position_for(symbol)
    if pos is not None:
        logger.info("Ya existe posición sobre %s, no abrir duplicada.", symbol)
        return False

    # limitar número de posiciones abiertas
    open_positions = list_open_positions()
    if len(open_positions) >= MAX_POSITIONS_OPEN:
        logger.info("Máximo de posiciones abiertas alcanzado (%d).", MAX_POSITIONS_OPEN)
        return False

    # comprobar cash disponible y buffer
    cash = get_cash_available()
    if cash <= MIN_CASH_BUFFER:
        logger.info("Efectivo insuficiente (%.2f <= buffer %.2f)", cash, MIN_CASH_BUFFER)
        return False

    return True

def _calc_qty_for_symbol(symbol: str, pct_of_equity: float = None) -> int:
    """
    Calcula qty según % del equity y precio del activo.
    pct_of_equity: si es None usa MAX_POSITION_PCT
    """
    if pct_of_equity is None:
        pct_of_equity = MAX_POSITION_PCT

    acct = get_account()
    equity = float(acct.equity)
    budget = equity * pct_of_equity
    # conseguir precio actual (último trade)
    try:
        barset = client.get_latest_trade(symbol)
        price = float(barset.price)
    except Exception:
        # fallback a un valor por defecto para evitar crash
        logger.exception("No se pudo obtener precio para %s, tomando qty=1", symbol)
        return 1

    qty = int(max(1, budget // price))
    return qty

def place_market_buy(symbol: str, qty: int = None, pct_of_equity: float = None, client_obj: TradingClient = client):
    if qty is None:
        qty = _calc_qty_for_symbol(symbol, pct_of_equity)

    if not _can_open_new_position(symbol, qty):
        logger.info("No se cumplen las condiciones para abrir %s", symbol)
        return None

    _throttle()

    order_req = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY
    )

    try:
        if LIVE:
            resp = client_obj.submit_order(order_req)
            logger.info("BUY (LIVE): %s %d -> %s", symbol, qty, resp)
        else:
            resp = client_obj.submit_order(order_req)
            logger.info("BUY (PAPER): %s %d -> %s", symbol, qty, resp)
        return resp
    except Exception as e:
        logger.exception("Error enviando orden BUY %s %d : %s", symbol, qty, e)
        return None

def close_position(symbol: str):
    """Cierra la posición long sobre `symbol`. Devuelve la respuesta o None."""
    symbol = str(symbol).upper().strip()
    try:
        pos = get_position_for(symbol)
    except Exception as e:
        logger.exception("Error consultando posición para %s: %s", symbol, e)
        pos = None

    if pos is None:
        logger.info("No hay posición para cerrar en %s (get_position devolvió None).", symbol)
        # DEBUG adicional: listar posiciones abiertas
        try:
            open_pos = client.get_all_positions()
            logger.info("Posiciones abiertas (count=%d): %s", len(open_pos), [p.symbol for p in open_pos])
        except Exception as e:
            logger.exception("No se pudo listar posiciones: %s", e)
        return None

    qty = int(float(pos.qty))
    _throttle()
    try:
        # Intentar convenience method close_position primero
        try:
            resp = client.close_position(symbol)
            logger.info("Close position (convenience): %s -> %s", symbol, resp)
            return resp
        except Exception as e_close:
            logger.warning("close_position convenience falló para %s: %s — Intentando ORDER sell fallback", symbol, e_close)
            # fallback a market sell order
            order_req = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            resp = client.submit_order(order_req)  # order_req o order_data según versión; aquí usamos submit_order(order_req)
            logger.info("SELL (fallback): %s %d -> %s", symbol, qty, resp)
            return resp
    except Exception as e:
        logger.exception("Error cerrando posición %s: %s", symbol, e)
        return None


def handle_signal(signal, symbol: str, qty: int = None, pct_of_equity: float = None):
    """
    signal: acepta int (1,0,-1) o strings 'buy','sell','hold','close'
    """
    # Normalizar symbol y signal
    symbol = str(symbol).upper().strip()

    # Normalizar numeric signals a texto
    if isinstance(signal, (int, float)):
        if int(signal) == 1:
            s = "buy"
        elif int(signal) == -1:
            s = "sell"
        else:
            s = "hold"
    else:
        # string-like
        s = str(signal).strip().lower()

    logger.info("Handle signal %s para %s (raw=%s)", s, symbol, signal)

    if s == "buy":
        return place_market_buy(symbol, qty=qty, pct_of_equity=pct_of_equity)
    elif s in ("sell", "close"):
        return close_position(symbol)
    elif s == "hold":
        logger.info("Hold sobre %s — no se hace nada.", symbol)
        return None
    else:
        logger.warning("Signal desconocida: %s (raw=%s)", s, signal)
        return None
