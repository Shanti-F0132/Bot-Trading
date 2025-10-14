# utils/alerts_manager.py
from datetime import datetime

def format_timestamp():
    """Devuelve la hora actual formateada para las alertas."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def send_alert(symbol, strategy, message, level="INFO"):
    """
    Envía una alerta en consola (puede expandirse a correo o Telegram).

    Parámetros:
        symbol (str): símbolo del activo.
        strategy (str): nombre de la estrategia que genera la alerta.
        message (str): contenido del mensaje de alerta.
        level (str): nivel de alerta ("INFO", "WARNING", "BUY", "SELL").
    """
    levels = {
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "BUY": "🟢",
        "SELL": "🔴"
    }

    emoji = levels.get(level.upper(), "📢")
    timestamp = format_timestamp()
    print(f"[{timestamp}] {emoji} ({strategy}) {symbol}: {message}")

def detect_signals(df, strategy_name):
    """
    Analiza un DataFrame con columnas ['Close', 'Signal'] y detecta cambios.

    Parámetros:
        df (pd.DataFrame): datos con la señal de estrategia.
        strategy_name (str): nombre de la estrategia.
    """
    if "Signal" not in df.columns:
        send_alert("N/A", strategy_name, "No se encontró columna 'Signal'.", "WARNING")
        return

    latest = df["Signal"].iloc[-1]
    prev = df["Signal"].iloc[-2] if len(df) > 1 else None

    if latest == 1 and prev != 1:
        send_alert(df.name if hasattr(df, "name") else "N/A", strategy_name, "Señal de COMPRA detectada", "BUY")
    elif latest == -1 and prev != -1:
        send_alert(df.name if hasattr(df, "name") else "N/A", strategy_name, "Señal de VENTA detectada", "SELL")
