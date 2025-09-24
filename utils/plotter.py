import matplotlib.pyplot as plt

def plot_price_with_sma(df, symbol):
    plt.figure(figsize=(12,6))
    plt.plot(df['Close'], label='Precio', color='black')
    plt.plot(df['SMA_short'], label='SMA corta', color='blue')
    plt.plot(df['SMA_long'], label='SMA larga', color='red')
    plt.title(f"{symbol} con SMA")
    plt.legend()
    plt.show()

def plot_equity_curve(eq):
    plt.figure(figsize=(10,5))
    plt.plot(eq['equity'], label='Equity Curve', color='green')
    plt.title("Crecimiento del capital en el backtest")
    plt.legend()
    plt.show()
