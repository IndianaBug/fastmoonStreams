import requests
import aiohttp
import http
import asyncio
import websockets
import time
import json
import re
import ssl
from cryptography.hazmat.primitives import serialization
import jwt
import secrets
import urllib.parse




ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Exchnages than require to fetch books before : binance, bybit


class CommunicationsManager:

    @classmethod
    def make_request(cls, connection_data : dict):
        if "maximum_retries"  not in connection_data:
            raise ValueError("maximum_retries are not in connection data")
        for index, _ in enumerate(range(connection_data.get("maximum_retries"))):
            response = requests.get(connection_data.get("url"), params=connection_data.get("params"), headers=connection_data.get("headers"))
            if response.status_code == 200:
                return {
                    "instrument" : connection_data.get("instrumentName"),
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
        conn = http.client.HTTPSConnection(connection_data.get("endpoint"))
        basepoint = "?".join([connection_data.get("basepoint"), urllib.parse.urlencode(connection_data.get("params"))])
        print(basepoint)
        conn.request(
            "GET", 
            basepoint, 
            connection_data.get("payload"), 
            connection_data.get("headers"),
            )
        res = conn.getresponse()
        response = json.loads(res.read())
        return {
            "instrument" : connection_data.get("instrumentName"),
            "exchange" : connection_data.get("exchange"),
            "insType" : connection_data.get("insTypeName").lower(),
            "response" : response,
        }
        

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
    }
    instrument_category_mapping = {
        "spot" : "spot",
        "perp" : "linear",
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
            "period": {"type": str, "default": "1d"},
            "limit": {"type": int, "default": 1},
                },
        "oi": {
            "baseCoin" : {"type": str, "default": ""},
        }
        }

    @classmethod
    def buildRequest(cls, insType:str, objective:str, maximum_retries:int=10, books_dercemet:int=100, **kwargs)->dict: 
        """
            instrument : ex btcusdt btc_12313 for spot/derivative
                            btc for option
            insType : spot, derivate, option
            objective :  depth, gta, oi (from tickers, for options)
            Maxium retries of an API with different parameters in case API call is impossible. Useful when you cant catch the limit
            books_dercemet : the derement of books length in case of api call being unsuccessful. If applicable
            **kwargs : request parameters
        """
        params = dict(kwargs)
        if insType == "option":
            params["baseCoin"] = params["baseCoin"].upper()
            instrument = params.get("baseCoin")
        else:
            params["symbol"] = params["symbol"].upper()
            instrument = params.get("symbol")
        # is it spot, perp or vanilla future, or option?
        if bool(re.search(r'\d', instrument)) and insType=="derivate":
            insTypeName = "future"
        if bool(re.search(r'\d', instrument)) is False and insType=="derivate":
            insTypeName = "perp"
        if insType in ["spot", "option"]:
            insTypeName = insType
        # create url        
        endpoint = cls.endpoint
        basepoint = cls.basepoints.get(objective)
        params["category"] = cls.instrument_category_mapping.get(insType)
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
            "exchange" : "bybit", 
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
    

### OKX ###

class okx(CommunicationsManager):
    """
        Abstraction of bybit api calls
    """
    repeat_response_code = -1130
    endpoint = "https://www.okx.com"
    basepoints = {
        "gta" : "/api/v5/rubik/stat/contracts/long-short-account-ratio",
        "oi" : "/api/v5/public/open-interest"
    }
    default_params  = {
        "gta" : {
            "ccy": {"type": str, "default": "BTC"},
            "period": {"type": str, "default": "5m"},
                },
        "oi": {
            "instType" : {"type": str, "default": "OPTION"},
            "instFamily" : {"type": str, "default": "BTC-USD"},
        }
        }

    @classmethod
    def buildRequest(cls, objective:str, maximum_retries:int=10, books_dercemet:int=100, **kwargs)->dict: 
        """
            objective :  gta, oi 
            **kwargs : request parameters
        """
        params = dict(kwargs)
        if objective == "gta":
            insTypeName = "perp"
        if objective != "gta":
            if params["instType"].upper() == "SWAP":
                insTypeName = "perp"
            if params["instType"].upper() == "OPTION":
                insTypeName = "option"
            if params["instType"].upper() == "FUTURES":
                insTypeName = "future"
            if params["instType"].upper() == "SPOT":
                insTypeName = "spot"
        
        for key in ["ccy", "instType", "instFamily"]:
            if key in params:
                params[key] = params[key].upper()
        
        if objective == "gta":
            instrument = params.get("ccy")
        if objective == "oi":
            instrument = "".join(params.get("instFamily").split("-"))

   
        endpoint = cls.endpoint
        basepoint = cls.basepoints.get(objective)
        url = endpoint + basepoint
        headers = {}
        return {
            "url" : url, 
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrumentName" : instrument.lower(), 
            "insTypeName" : insTypeName.lower(), 
            "exchange" : "okx", 
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
    

### COINBASE ###


class coinbase(CommunicationsManager):
    """
        Abstraction of bybit api calls
    """

    def __init__ (self, apikey, secretkey):
        self.apikey = apikey
        self.secretkey = secretkey
        self.repeat_response_code = -1130
        self.endpoint = "api.coinbase.com"
        self.basepoints = {
            "depth" : "/api/v3/brokerage/product_book",
        }
        self.default_params  = {
            "depth" : {
                "product_id": {"type": str, "default": "BTC-USD"},
                    },
            }
    def buildRequest(self, objective:str, maximum_retries:int=10, books_dercemet:int=100, **kwargs)->dict: 
        """
            instrument : ex: BTC-USD
            objective :  depth
            # OMIT Maxium retries of an API with different parameters in case API call is impossible. Useful when you cant catch the limit
            # OMIT books_dercemet : the derement of books length in case of api call being unsuccessful. If applicable
            **kwargs : request parameters
        """
        params = dict(kwargs)
        instrument = params.get("product_id")
        insTypeName = "spot"
        endpoint = self.endpoint
        basepoint = self.basepoints.get(objective)
        payload = ''
        headers = {
            "Authorization": f"Bearer {self.build_jwt(objective)}",
            'Content-Type': 'application/json'
        }
        return {
            "endpoint" : endpoint, 
            "basepoint" : basepoint,
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrumentName" : instrument.replace("-", ""),
            "insTypeName" : insTypeName, 
            "exchange" : "coinbase", 
            "repeat_code" : self.repeat_response_code,
            "maximum_retries" : maximum_retries, 
            "books_dercemet" : books_dercemet,
            "payload" : payload
            }
    
    def build_jwt(self, objective):
        if objective == "depth":
            objectiveCoinbase = "product_book"
        key_name       =  self.apikey
        key_secret     =  self.secretkey
        request_method = "GET"
        request_host   = "api.coinbase.com"
        request_path   = f"/api/v3/brokerage/{objectiveCoinbase}"
        service_name   = "retail_rest_api_proxy"
        private_key_bytes = key_secret.encode('utf-8')
        private_key = serialization.load_pem_private_key(private_key_bytes, password=None)
        uri = f"{request_method} {request_host}{request_path}"
        jwt_payload = {
            'sub': key_name,
            'iss': "coinbase-cloud",
            'nbf': int(time.time()),
            'exp': int(time.time()) + 120,
            'aud': [service_name],
            'uri': uri,
        }
        jwt_token = jwt.encode(
            jwt_payload,
            private_key,
            algorithm='ES256',
            headers={'kid': key_name, 'nonce': secrets.token_hex()},
        )
        return jwt_token

    def fetch(self, *args, **kwargs):
        connection_data = self.buildRequest(*args, **kwargs)
        response = CommunicationsManager.make_httpRequest(connection_data)
        return response







# c = coinbase(coinbaseAPI, coinbaseSecret)

# print(c.fetch("depth", product_id="BTC-USD"))

# async def example():
#     a = await okx.aiohttpFetch("gta", period="5m", ccy="BTC")
#     print(a)

# asyncio.run(example())
    
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
#     "coinbase" : "api.coinbase.com",
#     "gateio" : "https://api.gateio.ws",
#     "bitget" : "https://api.bitget.com",7
#     "deribit" : "wss://test.deribit.com",
#     "bingx" : "https://open-api.bingx.com",
#     "okx" : "https://www.okx.com",
# }

# APIbasepoints = {
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
#     "gateio" : "https://api.gateio.ws",
#     "bitget" : "https://api.bitget.com",
#     "deribit" : "wss://test.deribit.com",
#     "bingx" : "https://open-api.bingx.com",
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