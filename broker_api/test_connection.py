from alpaca_client import client

account = client.get_account()
print("Estado de la cuenta:", account.status)
print("Capital:", account.equity)
