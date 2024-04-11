import ijson
from infopulse import binanceInfo
import asyncio

def json_binance_info_spot_parse(data):
    symbols = []
    objects = ijson.items(data, 'item')
    symbols = (o.get("symbol") for o in objects)
    for symbol in symbols:
        print(symbol)

async def aaa():
    d = await binanceInfo.binance_info_async("spot")
    # data = json_binance_info_spot_parse(d)
    print(d[0])

asyncio.run(aaa())



    