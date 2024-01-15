from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from config import coinmarketcap_api

url = "https://pro-api.coinmarketcap.com/v1/exchange/assets"

# Exchange mapping
url_map = "https://pro-api.coinmarketcap.com/v1/exchange/map"
parameters_map = {}

# Exchange assets
url_exchange_info = "https://pro-api.coinmarketcap.com/v1/exchange/assets" 
exchange_info = [
    {"exchange" : "coinbase", "id":89 },
    {"exchange" : "binance", "id":270 },
    {"exchange" : "okx", "id":294 },
    {"exchange" : "bybit", "id":521 },
    {"exchange" : "deribit", "id":522 },
]
parameters_exchange_info = {
    "id" : "id"
}

url_global_metrics = "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"


url_categories = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/categories"


headers = {
 'Accepts': 'application/json',
 'X-CMC_PRO_API_KEY': coinmarketcap_api,
}


session = Session()
session.headers.update(headers)
try:
    response = session.get(url_exchange_info, params=parameters_exchange_info)
    data = json.loads(response.text)
    print(data)
    # with open(f"", 'w') as json_file:
    #     json.dump(data, json_file, indent=4)
except (ConnectionError, Timeout, TooManyRedirects) as e:
    print(e)