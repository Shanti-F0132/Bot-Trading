from utils.trade_logger import log_trade, init_trade_log

init_trade_log()

log_trade({
    "timestamp_entry": 1,
    "timestamp_exit": 2,
    "symbol": "TEST",
    "strategy": "test",
    "qty": 1,
    "entry_price": 100,
    "exit_price": 105,
    "stop_loss": 95,
    "take_profit": 110,
    "pnl_usd": 5,
    "pnl_pct": 5,
    "duration_sec": 60,
    "exit_reason": "TP",
    "order_id": "123"
})