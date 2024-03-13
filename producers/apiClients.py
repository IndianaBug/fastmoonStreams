import requests
import aiohttp
import asyncio
import websockets
import time
import json
import re
import ssl

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


class CommunicationsManager:

    @classmethod
    def make_request(cls, connection_data : dict):
        if "maximum_retries"  not in connection_data:
            raise ValueError("maximum_retries are not in connection data")
        for index, _ in enumerate(range(connection_data.get("maximum_retries"))):
            response = requests.get(connection_data.get("url"), params=connection_data.get("params"), headers=connection_data.get("headers"))
            if response.status_code == 200:
                return {
                    "instrument" : connection_data.get("instrument"),
                    "exchange" : connection_data.get("exchange"),
                    "insType" : connection_data.get("insTypeName").lower(),
                    "response" : response.json() ,
                }
            if response.get('code', None) == connection_data.get("repeat_response_code"):
                connection_data["params"]["limit"] = connection_data["params"]["limit"] - connection_data.get("books_decrement")
                time.sleep(1)
            if index == len(connection_data.get("maximum_retries")):
                print(response.status_code)
    
    @classmethod
    def make_httpRequest(cls, connection_data):
        pass


# For gate
# headers = info["headers"]
# headers["from"] = f"{int(time.time()) - 10}"
# headers["to"] = f"{int(time.time())}" 

# Bingx   
# async with aiohttp.ClientSession() as session:
#     async with session.request(
#         method, url, headers={"X-BX-APIKEY": APIKEY}, json=payload
#     ) as response:
#         response.raise_for_status()  # Raise an exception for error responses
#         return await response.text()


    @classmethod
    async def make_aiohttpRequest(cls, connection_data):
        async with aiohttp.ClientSession() as session:
            async with session.get(connection_data["url"], headers=connection_data["headers"], params=connection_data["params"]) as response:
                response =  await response.text()
                return {
                    "instrument" : connection_data.get("instrumentName").lower(),
                    "exchange" : connection_data.get("exchange").lower(),
                    "insType" : connection_data.get("insTypeName").lower(),
                    "objective" : connection_data.get("objective").lower(),
                    "response" : response,
                } 


    @classmethod
    def make_wsRequest(cls, connection_data):
        async def wsClient(connection_data):
            async with websockets.connect(connection_data.get("url"),  ssl=ssl_context) as websocket:
                await websocket.send(json.dumps(connection_data.get("headers")))
                response = await websocket.recv()
                return response
        loop = asyncio.get_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(wsClient(connection_data))
        finally:
            loop.close()
        return {
            "instrument" : connection_data.get("instrumentName").lower(),
            "exchange" : connection_data.get("exchange").lower(),
            "insType" : connection_data.get("insTypeName").lower(),
            "objective" : connection_data.get("objective").lower(),
            "response" : response,
        } 


# Binance

class binance(CommunicationsManager):
    """
        Abstraction for binance API calls for depth, funding, oi, tta, ttp and gta
    """
    repeat_response_code = -1130
    endpoints = {
            "spot" : "https://api.binance.com",
            "coin-m" : "https://fapi.binance.com",
            "coin-c" : "https://dapi.binance.com",
        }
    basepoints = {
            "spot" : {
                "depth" : "/api/v3/depth",
            },
            "coin-m" : {
                "depth" : "/fapi/v1/depth",
                "funding" : "/fapi/v1/fundingRate",
                "oi" : "/fapi/v1/openInterest",
                "tta" : "/futures/data/topLongShortAccountRatio",
                "ttp" : "/futures/data/topLongShortPositionRatio",
                "gta" : "/futures/data/globalLongShortAccountRatio",
            },
            "coin-c" : {
                "depth" : "/dapi/v1/depth",
                "funding" : "/dapi/v1/fundingRate",
                "oi" : "/dapi/v1/openInterest",
                "tta" : "/futures/data/topLongShortAccountRatio",
                "ttp" : "/futures/data/topLongShortPositionRatio",
                "gta" : "/futures/data/globalLongShortAccountRatio",
            },
        }

    default_params  = {
        "depth" : {
                "symbol": {"type": str, "default": ""},
                "limit": {"type": int, "default": 1000}
            },
        "funding" : {
                "symbol": {"type": str, "default": ""},
                "limit": {"type": int, "default": 100}
            },
        "oi" : {
                "symbol": {"type": str, "default": ""}
            },
        "tta_ttp_gta" : {
            "coin-m" : {
                "symbol": {"type": str, "default": ""},
                "period": {"type": str, "default": "5m"},
                "limit": {"type": int, "default": 1},
                        },
            "coin-c" : {
                "pair": {"type": str, "default": ""},
                "period": {"type": str, "default": "5m"},
                "limit": {"type": int, "default": 1},
                        },
        }
    }
    def __init__(self):
        pass

    @classmethod
    def buildRequest(cls, insType:str, objective:str, maximum_retries:int=10, books_dercemet:int=500, **kwargs)->dict: 
        """
            instrument : ex btcusdt for spot/coin-m 
                            brcusd_perp or bnb_perp or btcusd_4145 for coin-c
            insType : spot, derivate
            objective :  depth, funding, oi, tta, ttp, gta
            Maxium retries of an API with different parameters in case API call is impossible. Useful when you cant catch the limit
            books_dercemet : the derement of books length in case of api call being unsuccessful. If applicable
            **kwargs : request parameters
        """
        params = dict(kwargs)
        params["symbol"] = params["symbol"].upper()
        instrument = params.get("symbol")
        # is it spot, perp or vanilla future?
        marginCoin = "coin-c" if len(instrument.split("_")) > 1 else "coin-m"
        marginCoin = "spot" if insType=="spot" else marginCoin
        insTypeName = "future" if bool(re.search(r'\d', instrument)) else "perp"
        insTypeName = "spot" if insType=="spot" else insTypeName
        # trim the name if perpetual, there are no the coin-m marginated instruments that end with usd
        instrumentName = instrument.split("_")[0] if insTypeName=="perp" else instrument
        # create url        
        endpoint = cls.endpoints.get(marginCoin)
        basepoints = cls.basepoints.get(marginCoin).get(objective)
        if objective in "tta_ttp_gta" and marginCoin == "coin-c":
            params["pair"] = params.pop("symbol").split("_")[0]
        url = endpoint + basepoints
        # verify params
        objective = "tta_ttp_gta" if objective in "tta_ttp_gta" else objective
        headers = {}
        return {
            "url" : url, 
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrumentName" : instrumentName, 
            "insTypeName" : insTypeName, 
            "exchange" : "binance", 
            "repeat_code" : cls.repeat_response_code,
            "maximum_retries" : maximum_retries, 
            "books_dercemet" : books_dercemet
            }
    
    @classmethod
    def fetch(cls, *args, **kwargs):
        connection_data = cls.buildRequest(*args, **kwargs)
        response = cls.make_request(connection_data)
        return response

    @classmethod
    async def aiohttpFetch(cls, *args, **kwargs):
        connection_data = cls.buildRequest(*args, **kwargs)
        response = await cls.make_aiohttpRequest(connection_data)
        return response

### Bybit ###
    

class bybit(CommunicationsManager):
    """
        Abstraction of bybit api calls
    """
    repeat_response_code = -1130
    endpoint = "https://api.bybit.com"
    basepoints = {
        "depth" : "/v5/market/orderbook",
        "gta" : "/v5/market/account-ratio",
        "oi" : "/v5/market/tickers"
    },
    instrument_category_mapping = {
        "spot" : "spot",
        "derivate" : "linear",
        "option" : "option",
    }
    default_params  = {
        "depth" : {
                "symbol": {"type": str, "default": ""},
                "limit": {"type": int, "default": 1000}
            },
        "gta" : {
            "symbol": {"type": str, "default": ""},
            "period": {"type": str, "default": "5m"},
            "limit": {"type": int, "default": 1},
                },
        "oi": {
            "baseCoin" : {"type": str, "default": ""},
        }
        }

    @classmethod
    def buildRequest(cls, insType:str, objective:str, maximum_retries:int=10, books_dercemet:int=100, **kwargs)->dict: 
        """
            instrument : ex btcusdt for spot/coin-m 
                            brcusd_perp or bnb_perp or btcusd_4145 for coin-c
            insType : spot, derivate, option
            objective :  depth, gta, oi (from tickers, for options)
            Maxium retries of an API with different parameters in case API call is impossible. Useful when you cant catch the limit
            books_dercemet : the derement of books length in case of api call being unsuccessful. If applicable
            **kwargs : request parameters
        """
        params = dict(kwargs)
        params["symbol"] = params["symbol"].upper()
        instrument = params.get("symbol")
        # is it spot, perp or vanilla future?
        insTypeName = "future" if bool(re.search(r'\d', instrument)) else "perp"
        insTypeName = "spot" if insType=="spot" else insTypeName
        # create url        
        endpoint = cls.endpoint
        basepoint = cls.basepoints.get(objective)
        url = endpoint + basepoint
        # verify params
        headers = {}
        return {
            "url" : url, 
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrumentName" : instrument.lower(), 
            "insTypeName" : insTypeName.lower(), 
            "exchange" : "binance", 
            "repeat_code" : cls.repeat_response_code,
            "maximum_retries" : maximum_retries, 
            "books_dercemet" : books_dercemet
            }

    @classmethod
    def fetch(cls, *args, **kwargs):
        connection_data = cls.buildRequest(*args, **kwargs)
        response = cls.make_request(connection_data)
        return response

    @classmethod
    async def aiohttpFetch(cls, *args, **kwargs):
        connection_data = cls.buildRequest(*args, **kwargs)
        response = await cls.make_aiohttpRequest(connection_data)
        return response




async def example():
    a = await bybit.aiohttpFetch("derivate", "depth", symbol="btcusdt", limit=50)
    print(a)

asyncio.run(example())
    
    # @classmethod
    # @APIClientDecorator.api_request_decorato
    # def fetch(cls, instrument:str, insType:str, objective:str, maximum_retries:int=10, books_dercemet:int=500):
    #     url, params, headers, cls.repeat_response_code, maximum_retries, books_dercemet, insTypeName, exchange = cls.buildRequest(
    #         instrument, insType, objective, maximum_retries, books_dercemet
    #         )
    #     return url, params, headers, cls.repeat_response_code, maximum_retries, books_dercemet, insTypeName, exchange
 









#     "kucoin" : {
#         "spot" : "https://api.kucoin.com", 
#         "perp" : "https://api-futures.kucoin.com",
#     },
#     "mexc" : {
#         "spot" : "https://api.mexc.com", 
#         "perp" : "https://contract.mexc.com",
#     },
#     "htx" : {
#         "spot" : "https://api.huobi.pro",
#         "perp" : "https://api.hbdm.com",
#     },
#     "bybit" :  "https://api.bybit.com",
#     "coinbase" : "api.coinbase.com",
#     "gateio" : "https://api.gateio.ws",
#     "bitget" : "https://api.bitget.com",7
#     "deribit" : "wss://test.deribit.com",
#     "bingx" : "https://open-api.bingx.com",
#     "okx" : "https://www.okx.com",
# }

# APIbasepoints = {
#     "binance" : {
#         "spot" : {
#             "depth" : "/api/v3/depth",
#         },
#         "perp" : {
#             "mfutures" : {
#                 "depth" : "/fapi/v1/depth",
#             },
#             "cfutures" : {
#                 "depth" : "/dapi/v1/depth",

#             },
#         }
#     },
#     "kucoin" : {
#         "spot" : "https://api.kucoin.com", 
#         "perp" : "https://api-futures.kucoin.com",
#     },
#     "mexc" : {
#         "spot" : "https://api.mexc.com", 
#         "perp" : "https://contract.mexc.com",
#     },
#     "htx" : {
#         "spot" : "https://api.huobi.pro",
#         "perp" : "https://api.hbdm.com",
#     },
#     "bybit" :  {
#         "depth" : "/v5/market/orderbook",
#     },
#     "coinbase" : "api.coinbase.com",
#     "gateio" : "https://api.gateio.ws",
#     "bitget" : "https://api.bitget.com",
#     "deribit" : "wss://test.deribit.com",
#     "bingx" : "https://open-api.bingx.com",
#     "okx" : "https://www.okx.com",
# }




# APIparams = {
#     "binance" : {
#         "spot" : {
#             "depth" : {
#                 "symbol" : "",
#                 "limit" : int("")
#             }
#         },
#         "perp" : {
#             "mfutures" : {
#                 "depth" : "/fapi/v1/depth"
#             },
#             "cfutures" : {
#                 "depth" : "/dapi/v1/depth",

#             },
#         }
#     },
# }