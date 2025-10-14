# main2.py
import pandas as pd
from utils.data_loader import get_data
from utils.trade_simulator import TradeSimulator
from utils.alerts_manager import send_alert
from strategies.sma_strategy import sma_strategy
from strategies.rsi_strategy import rsi_strategy
from utils.plot_utils import plot_equity_curve

print("🚀 Iniciando Paper Trading Bot...\n")

# ==========================================================
# 1️⃣ CONFIGURACIÓN INICIAL
# ==========================================================
SYMBOL = "AAPL"
INITIAL_CAPITAL = 10000
COMMISSION = 0.001

# ==========================================================
# 2️⃣ CARGA DE DATOS HISTÓRICOS (o stream simulado)
# ==========================================================
print(f"📡 Cargando datos históricos para {SYMBOL}...")
df = get_data(SYMBOL, start="2025-04-01", end="2025-10-10")

if df is None or df.empty:
    raise ValueError("❌ Error: No se pudieron cargar los datos de mercado.")

print(f"✅ Datos cargados: {len(df)} registros\n")

# ==========================================================
# 3️⃣ APLICAR ESTRATEGIAS DE TRADING
# ==========================================================
print("⚙️ Aplicando estrategias...\n")

df_sma = sma_strategy(df.copy(), short=10, long=30)
df_rsi = rsi_strategy(df.copy(), rsi_period=14, lower=30, upper=70)

strategies = {
    "SMA": df_sma,
    "RSI": df_rsi
}

# ==========================================================
# 4️⃣ SIMULADOR DE OPERACIONES (PAPER TRADING)
# ==========================================================
bot = TradeSimulator(initial_capital=INITIAL_CAPITAL, commission=COMMISSION)

print("📈 Ejecutando operaciones simuladas...\n")

for strat_name, strat_df in strategies.items():
    strat_df.columns = [col.lower() for col in strat_df.columns]
    close_col = next((col for col in strat_df.columns if col.startswith("close")), None)
    if close_col is None:
        raise ValueError("No se encontró columna 'close' en el DataFrame.")
    print(f"=== Estrategia: {strat_name} ===\n")
    for i in range(1, len(strat_df)):
        price = strat_df[close_col].iloc[i]
        if "Signal" in strat_df.columns:
            signal = strat_df["Signal"].iloc[i]
        elif "signal" in strat_df.columns:
            signal = strat_df["signal"].iloc[i]
        else:
            continue

        # Asegúrate de que signal es escalar
        if isinstance(signal, pd.Series):
            signal = signal.iloc[0]

        if signal == 1:
            send_alert(SYMBOL, strat_name, f"Señal de compra detectada a ${price:.2f}", "BUY")
            bot.buy(price, symbol=SYMBOL)
        elif signal == -1:
            send_alert(SYMBOL, strat_name, f"Señal de venta detectada a ${price:.2f}", "SELL")
            bot.sell(price, symbol=SYMBOL)

        bot.update_equity(price)

# ==========================================================
# 5️⃣ RESUMEN FINAL DE RESULTADOS
# ==========================================================
summary = bot.summary()

# ==========================================================
# 6️⃣ EXPORTAR RESULTADOS A CSV
# ==========================================================
df_trades = pd.DataFrame(summary["trades"])
df_trades.to_csv("outputs/csv/paper_trading_trades.csv", index=False)
print("\n💾 Registro de operaciones guardado en: outputs/csv/paper_trading_trades.csv")

# ==========================================================
# 7️⃣ GRAFICAR EVOLUCIÓN DEL CAPITAL
# ==========================================================
if len(bot.equity_history) > 10:
    equity_df = pd.DataFrame({"Equity": bot.equity_history})
    plot_equity_curve(equity_df, title="Paper Trading Equity Curve")
else:
    print("\n⚠️ No se generaron suficientes puntos para graficar la curva de capital.")

print("\n✅ Simulación completada con éxito.")
