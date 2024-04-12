import ijson
from infopulse import binanceInfo
import asyncio

def binance_get_option_instruments_by_underlying(data, underlying_asset):
    symbols = []
    for prefix, event, value in ijson.parse(data):
        if prefix == "optionSymbols.item.symbol":
            symbols.append(value)
    symbols = list(set([s.split("-")[1] for s in symbols if underlying_asset in s]))
    return symbols
        
async def aaa():
    d = await binanceInfo.binance_info_async("option")
    data = binance_get_option_instruments_by_underlying(d, "BTC")
    print(data)

asyncio.run(aaa())



    