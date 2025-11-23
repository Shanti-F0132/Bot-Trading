from alpaca.trading.client import TradingClient
import os
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_API_SECRET")

# Crear cliente para Paper Trading
client = TradingClient(API_KEY, API_SECRET, paper=True)