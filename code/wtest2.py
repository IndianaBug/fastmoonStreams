from utilis import get_dict_by_key_value, bingx_AaWSnap_aiohttp
from urls import AaWS
import asyncio
from utilis2 import books_snapshot
import json

a = books_snapshot("kucoin_spot_btcusdt_depth", 100)

with open("data/kucoin_btcusdt_spot_depth.json") as file:
    d = json.load(file)
    new_data = { 
        "exchange" : "kucoin",
        "instrument" : "as",
        "insType" : "spot",
        "obj" : "depth",
        "btc_price" : 66532,
        "timestamp" : 564613486315810,  
        "data" : a
        }
    d.append(new_data)

with open("data/kucoin_btcusdt_spot_depth.json", 'w') as file2:
    json.dump(d, file2, indent=2)