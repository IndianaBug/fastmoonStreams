from utilis import get_dict_by_key_value, bingx_AaWSnap_aiohttp
from urls import AaWS
import asyncio

# d = get_dict_by_key_value([x for x in AaWS if x["type"] == "api"], "id", "bingx_perpetual_btcusdt_OI")


# loop = asyncio.get_event_loop()
# asyncio.set_event_loop(loop)
# async def mim():
#     response = await bingx_AaWSnap_aiohttp(d["url"], d["path"], d["params"],"depth", 3)

# response = await mim()

# print(response)

import requests

host = "https://api.gateio.ws"
prefix = "/api/v4"
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

url = '/futures/usdt/contracts'
query_param = ''
r = requests.request('GET', host + prefix + url, headers=headers)
print(r.json())


# Gateio_btcusdt_perpetual_trades
