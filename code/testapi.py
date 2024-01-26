import json
import requests


r = requests.get("https://api.bybit.com/v5/market/tickers?category=option&baseCoin=BTC")



with open("bybit_option_oi_btc.json", 'w') as json_file:
    json.dump(r.json(), json_file, indent=2)  