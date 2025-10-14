import matplotlib.pyplot as plt

def plot_equity_curve(df, title="Equity Curve"):
    plt.figure(figsize=(10,5))
    plt.plot(df["Equity"], linewidth=2)
    plt.title(title)
    plt.xlabel("Iteración")
    plt.ylabel("Capital ($)")
    plt.grid(True)
    plt.show()
