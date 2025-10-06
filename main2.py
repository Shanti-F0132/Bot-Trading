import matplotlib.pyplot as plt
from utils.data_loader import get_data
from strategies.sma_strategy import sma_strategy
from backtesting.simple_backtester import backtest
import pandas as pd


# ==============================
# 📥 Cargar datos
# ==============================
symbol = "AAPL"
print(f"📥 Descargando datos de {symbol}...")
df = get_data(symbol, start="2020-01-01", end="2025-01-01")

# Normalizamos nombres de columnas
df.columns = df.columns.str.lower()

print("✅ Datos cargados correctamente:")
print(df.head())


# ==============================
# ⚙️ Función: Evaluar estrategia en distintos timeframes
# ==============================
def evaluate_timeframes(df, strategy_func, short=10, long=50):
    """
    Evalúa una estrategia (por ejemplo SMA) en distintos timeframes:
    Diario, Semanal y Mensual.
    Retorna un diccionario con métricas y curvas de equity.
    """
    results = {}
    timeframes = {"Diario": "D", "Semanal": "W", "Mensual": "ME"}

    for name, tf in timeframes.items():
        print(f"\n📊 Procesando timeframe: {name}")

        # Resample OHLCV según el timeframe
        df_tf = df.resample(tf).agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        }).dropna()

        # Aplicar estrategia
        df_strategy = strategy_func(df_tf.copy(), short, long)

        # Ejecutar backtest
        res = backtest(df_strategy)
        

        results[name] = res

    return results


# ==============================
# 📈 Ejecución principal
# ==============================
print("\n🚀 Comparación de SMA 10-50 en distintos timeframes...")

results_tf = evaluate_timeframes(df, sma_strategy, short=10, long=50)

# ==============================
# 📊 Gráfica + Tabla comparativa de timeframes
# ==============================
print("\n📊 Generando gráfica comparativa con tabla...")

plt.figure(figsize=(12, 7))

# Curvas de capital
for name, res in results_tf.items():
    plt.plot(res["equity_curve"], label=name)

plt.title(f"Comparación de SMA 10-50 en distintos timeframes ({symbol})")
plt.xlabel("Fecha")
plt.ylabel("Capital ($)")
plt.legend()
plt.grid(True)

# ---- Crear tabla de métricas ----
table_data = []
for name, res in results_tf.items():
    table_data.append([
        name,
        f"${res['final_equity']:,.2f}",
        f"{res['cagr']*100:.2f}%",
        f"{res['sharpe_ratio']:.2f}",
        f"{res['max_drawdown']:.2f}%"
    ])

df_table = pd.DataFrame(table_data, columns=["Timeframe", "Final Equity", "CAGR", "Sharpe", "Max DD"])

# Insertar tabla debajo de la gráfica
plt.table(
    cellText=df_table.values,
    colLabels=df_table.columns,
    loc="bottom",
    cellLoc="center",
    bbox=[0, -0.35, 1, 0.25]
)
plt.subplots_adjust(left=0.1, bottom=0.3)

# Guardar figura
plt.savefig("timeframes_comparison.png", bbox_inches="tight")
plt.show()

print("\n✅ Tabla comparativa generada correctamente.")
print(df_table)


# ==============================
# 🧾 Mostrar métricas por timeframe
# ==============================
print("\n📋 Resultados comparativos:")
for name, res in results_tf.items():
    print(f"\n{name}:")
    print(f"  💰 Capital final: ${res['final_equity']:.2f}")
    print(f"  📈 CAGR: {res['cagr']*100:.2f}%")
    print(f"  ⚖️ Sharpe Ratio: {res['sharpe_ratio']:.2f}")
    print(f"  📉 Max Drawdown: {res['max_drawdown']*100:.2f}%")

print("\n✅ Comparación completada y guardada como 'timeframes_comparison.png'")
