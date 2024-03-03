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


import aiohttp
import time

async def fetch_data(url, params=None, headers=None):
  async with aiohttp.ClientSession() as session:
    async with session.get(url, params=params, headers=headers) as response:
      if response.status == 200:
        return await response.json()
      else:
        raise aiohttp.ClientResponseError(response.request_info, response.history, response.status, None, None)

# Example usage
d =     {  # https://www.gate.io/docs/developers/apiv4/en/#retrieve-liquidation-history
                "type" : "api",
                "id" : "gateio_perpetual_btcusdt_trades",
                "exchange":"gateio", 
                "insType":"perpetual", 
                "obj":"liquidations", 
                "instrument": "btcusdt", 
                "updateSpeed":10, 
                "url" : "https://api.gateio.ws/api/v4/futures/usdt/trades",
                "params" : {
                            "contract" : "BTC_USDT",
                            "from" : int(time.time()) - 20,
                            "to" : int(time.time())
                                },
                "headers" : {'Accept': 'application/json', 'Content-Type': 'application/json'}
            }, 
url = d["url"]
headers = d["params"]
params = d["headers"]

loop = asyncio.get_event_loop()
data = loop.run_until_complete(fetch_data(url, params=params, headers=headers))

if data:
  # Process the data
  print(data)
else:
  print("Error fetching data")
