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
  while True:
    async with aiohttp.ClientSession() as session:
      async with session.get(url, params=params, headers=headers) as response:
        if response.status == 200:
          return await response.json()
          time.sleep(5)
        else:
          raise aiohttp.ClientResponseError(response.request_info, response.history, response.status, None, None)

# Example usage
d =         {
        "type" : "api",
        "id" : "gateio_perpetual_btcusdt_depth",
        "exchange":"gateio", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":10,
        "url" : "https://api.gateio.ws/api/v4/futures/usdt/order_book",
        "params" : {"contract" : "BTC_USDT", "limit" : "300"},
        "headers" : {'Accept': 'application/json', 'Content-Type': 'application/json'}          
    }
url = d["url"]
headers = d["headers"]
params = d["params"]

# loop = asyncio.get_event_loop()
# data = loop.run_until_complete(fetch_data(url, params=params, headers=headers))

# if data:
#   # Process the data
#   print(data)
# else:
#   print("Error fetching data")
import asyncio
import httpx

async def fetch_data():
    url = d["url"]
    headers = d["headers"]
    params = d["params"]

    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
                print(f"Received data: {data}")

        except httpx.HTTPError as e:
            print(f"HTTP error: {e}")

        # Optionally, introduce a delay before the next fetch
        await asyncio.sleep(5)  # 5 seconds delay (adjust as needed)

async def main():
    # Create a task using asyncio.ensure_future
    fetch_data_task = asyncio.ensure_future(fetch_data())

    # Optionally, you can add other tasks here using asyncio.ensure_future

    # Wait for the tasks to complete
    await asyncio.gather(fetch_data_task)

if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(main())