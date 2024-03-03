from utilis import get_dict_by_key_value, bingx_AaWSnap_aiohttp
from urls import AaWS
import asyncio


# import requests

# host = "https://api.gateio.ws"
# prefix = "/api/v4"
# headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

# url = '/futures/usdt/contracts'
# query_param = ''
# r = requests.request('GET', host + prefix + url, headers=headers)
# a = [x["name"] for x in r.json()]

# # print(response)

# import requests

# host = "https://api.gateio.ws"
# prefix = "/api/v4"
# headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

# url = '/futures/usdt/contracts'
# query_param = ''
# r = requests.request('GET', host + prefix + url, headers=headers)
# print(r.json())


# # Gateio_btcusdt_perpetual_trades

from utilis2 import books_snapshot

print(books_snapshot("gateio_perpetual_btcusdt_depth", 1000))