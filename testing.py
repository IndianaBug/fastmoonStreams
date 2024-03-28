# from producers.clients import *

# class clientTest(binance, bybit, bitget, deribit, okx, htx, mexc, gateio, bingx):
    
#     @classmethod
#     def test_deribit_apiData(cls, **kwargs):
#         # a = cls.deribit_fetch("option", "oifunding", symbol="BTC")
#         # print(a)
#         async def example():
#             d = cls.deribit_build_api_connectionData("option", "depth", 100, symbol="BTC-PERPETUAL", limit=1000)
#             result = await d['aiohttpMethod'](**d["params"])
#             # a = await cls.deribit_aiohttpFetch("option", "oifunding", symbol="BTC", limit=1000) # works even with unnecessary arguments
#             print(result)

#         asyncio.run(example())

#     @classmethod
#     def test_deribit_wsData(cls, **kwargs):
#         #async def example():
#         d = cls.deribit_build_ws_connectionData("option", symbol="BTC", objective="oifunding", limit=1000)
#         result =  d['sbmethod'](**d["sbPar"])
#         print(result)
#         #asyncio.run(example())

#     @classmethod
#     def test_htx_api(cls):
#         print(cls.htx_fetch(instType="perpetual", objective="tta", symbol="BTC-USD"))

#     @classmethod
#     def test_htx_ws(cls):
#         ht = cls.htx_build_api_connectionData("perpetual", "tta", "BTC-USD", 10)
#         async def example():
#             d = await ht["aiohttpMethod"]()
#             print(d)
#         asyncio.run(example())
    
#     @classmethod
#     def test_ws(cls):
#         connData = htx.htx_build_ws_connectionData("perpetual", "depth", "BTC-USD")
#         print(connData.get("kickoffMethod")())
#         print(connData)

#     @classmethod
#     def test(cls):
#         async def example():
#             d = await cls.htx_aiohttpFetch_futureTrades()
#             print(d)
#         asyncio.run(example())

#     @classmethod
#     def test_mexc_ws(cls):
#         connData = cls.mexc_build_ws_connectionData("spot", "depth", "BTCUSDT")
#         print(connData["kickoffMethod"]())

#     @classmethod
#     def gate_test_api(cls):
#         async def example():
#             connData =  cls.gateio_build_api_connectionData("perpetual", "funding", "BTC_USDT", 100)
#             r = await connData["aiohttpMethod"]()
#             print(r)
#         asyncio.run(example())

#     @classmethod
#     def gate_test_ws(cls):
#         connData =  cls.gateio_build_ws_connectionData("option", "trades", "BTC_USDT")
#         print(connData["kickoffMethod"]())
#     #     asyncio.run(example())

#     @classmethod
#     def gate_option_msg(cls):
#         print(cls.gateio_build_ws_message_all_Options("depth", "BTC_USDT"))

#     @classmethod
#     def binance_instruments(cls):
#         async def example():
#             data =  await cls.binance_build_fundfutureperp_method("BTC")
#             print(data)
#         asyncio.run(example())
        
#     @classmethod
#     def binance_ws(cls):
#         s = ["option", "option"]
#         o = ["oifunding", "optionTrades"]
#         ss= ["BTC-USDT-SWAP", "BTC-USDT-SWAP"]
#         data = cls.okx_build_ws_connectionData(s,o,ss)
#         print(data)
#         # async def example():
#         #     result = data["1stBooksSnapMethod"]()
#         #     print(result)
#         # asyncio.run(example())

#     @classmethod
#     def bybit_aiohttp(cls):
#         async def example():
#             data = cls.bybit_build_api_connectionData("Linear", "oi", "BTC", 100, special_method="oifutureperp")
#             d = await data["aiohttpMethod"]()
#             print(d)
#         asyncio.run(example())

#     @classmethod
#     def bybit_ws(cls):
#         data = cls.bybit_build_ws_connectionData("Linear", "trades", "BTC", special_method="perpfutureTrades")
#         print(data)
#         # print(data["1stBooksSnapMethod"]())

#     @classmethod
#     def okx_aiohttp(cls):
#         async def example():
#             data = cls.okx_build_api_connectionData("option", "oi", "BTC", 10)
#             d = await data["aiohttpMethod"]()
#             print(d)
#         asyncio.run(example())

#     @classmethod
#     def okx_ws(cls):
#         async def example():
#             data = cls.okx_build_ws_connectionData("perpetual", "depth", "BTC-USD-SWAP", needSnap=True)
#             # d = await data["aiohttpMethod"]()
#             print(data["1stBooksSnapMethod"]())
#         asyncio.run(example())

#     @classmethod
#     def bingx_api(cls):
#         async def example():
#             data = cls.bingx_build_api_connectionData("perpetual", "depth", "BTC-USDT", 100, needSnap=True)
#             d = await data["aiohttpMethod"]()
#             # print(data["1stBooksSnapMethod"]())
#             print(d)
#         asyncio.run(example())


#     @classmethod
#     def bitget_api(cls):
#         async def example():
#             data = cls.bitget_build_api_connectionData("perpetual", "oi", "BTC", 100, special_method="oifutureperp")
#             d = await data["aiohttpMethod"]()
#             # print(data["1stBooksSnapMethod"]())
#             print(d)
#         asyncio.run(example())

#     @classmethod
#     def bitget_ws(cls):
#         async def example():
#             instTypes = ["spot"]
#             objs = ["depth"]
#             symbls = ["BTCUSDT"]
#             data = cls.bitget_build_ws_connectionData(instTypes, objs, symbls, True)
#             print(data["1stBooksSnapMethod"]())
#         asyncio.run(example())

#     @classmethod
#     def deribit_api(cls):
#         async def example():
#             data = cls.deribit_build_api_connectionData("option", "oifunding", "BTC", 100)
#             d = await data["aiohttpMethod"]()
#             # print(data["1stBooksSnapMethod"]())
#             print(d)
#         asyncio.run(example())

#     @classmethod
#     def deribit_ws(cls):
#         async def example():
#             instTypes = ["perpetual"]
#             objs = ["depth"]
#             symbls = ["BTC-PERPETUAL"]
#             data = cls.deribit_build_ws_connectionData(instTypes, objs, symbls, True)
#             # = await data["1stBooksSnapMethod"]()
#             print(data)
#         asyncio.run(example())


#     @classmethod
#     def coinbase_ws(cls):
#         async def example():
#             instTypes = ["spot"]
#             objs = ["depth"]
#             symbls = ["BTC-USD"]
#             data = cls.coinbase_build_ws_connectionData(instTypes, objs, symbls, True)
#             # = await data["1stBooksSnapMethod"]()
#             print(data)
#         asyncio.run(example())
        
        

# bing = bingx("", "")
# def bingx_api():
#     async def example():
#         data = bing.bingx_build_api_connectionData("perpetual", "oi", "BTC-USDT", 100, needSnap=True)
#         d = await data["aiohttpMethod"]()
#         # print(data["1stBooksSnapMethod"]())
#         print(d)
#     asyncio.run(example())
# bingx_api()


# coinbaseSecret = '-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIDOVctxJpAI/hHtbUN9VrHej4bWPRuT9um9FoBlTgiyaoAoGCCqGSM49\nAwEHoUQDQgAEJt8JWIh8CHm045POImBF0ZvVuX5FbQjIDhIT82hE5r1+vb8cSQ3M\nfEjriBy1/ZD3EywPNxyGe6nO/Wsq0M8hXQ==\n-----END EC PRIVATE KEY-----\n'
# coinbaseAPI = 'organizations/b6a02fc1-cbb0-4658-8bb2-702437518d70/apiKeys/697a8516-f2e2-4ec9-a593-464338d96f21'

# coinb = coinbase(coinbaseAPI, coinbaseSecret)

# # print(coinb.coinbase_productids_by_instType("future"))

# data = coinb.coinbase_build_api_connectionData("future", "depth", "BIT-26APR24-CDE", 10)

# async def example():
#     data = coinb.coinbase_build_ws_connectionData("spot", "depth", "BTC-USD")
#     print(data)
# asyncio.run(example())



# kucoinAPI = "65d92cc0291aa2000118b67b"
# kucoinSecret = "3d449464-ab5e-4415-9950-ae31648fe90c"
# kucoinPass = "sN038-(!UK}4"

# kuk = kucoin(kucoinAPI, kucoinSecret, kucoinPass)

# # print(coinb.coinbase_productids_by_instType("future"))

# async def example():
#     data = kuk.kucoin_build_api_connectionData("perpetual", "oifunding", "XBTUSDTM", 100)
#     d = await data["aiohttpMethod"]()
#     print(d)
# asyncio.run(example())

import requests
# url = "https://open-api.bingx.com/openApi/spot/v2/market/depth?symbol=BTC_USDT&depth=1000&type=step3"
url = "https://api.hbdm.com/swap-api/v1/swap_contract_info"
response = requests.get(url).json()

print(response.keys())


print(response)
# No perp, replace for USD # I you willl need to add inverse linear


# oi
# tta, 
# ttp, 
# funding