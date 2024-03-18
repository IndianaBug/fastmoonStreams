import requests
import aiohttp
import http
import asyncio
import websockets
import time
from datetime import datetime
import json
import re
import ssl
from cryptography.hazmat.primitives import serialization
import jwt
import secrets
import urllib.parse
import base64
import hashlib
import hmac
from hashlib import sha256 
from utilis import generate_random_integer
from functools import partial
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

from producers.clientpoints.binance import *
from producers.clientpoints.bybit import *
# from producers.clientpoints.okx import *
# from producers.clientpoints.coinbase import *
# from producers.clientpoints.deribit import *
# from producers.clientpoints.kucoin import *
# from producers.clientpoints.htx import *
# from producers.clientpoints.bitget import *
# from producers.clientpoints.gateio import *
# from producers.clientpoints.mexc import *
# from producers.clientpoints.bingx import *


# BNB-240320-545-C


# Use for Binance
# a = binance.binance_build_ws_connectionData("spot", needSnap=True, symbol="btcfdusd", objective="depth", pullSpeed="500ms")
# #print(a.get("sbPar"))
# books = a.get("sbmethod")(a.get("instType"), a.get("objective"), **a.get("sbPar"))
# result = d['aiohttpMethod'](**kwargs)
# print(books)


# import asyncio

# async def main():
#     # Your asynchronous code here
#     a = binance.binance_build_api_connectionData("perpetual", "oi", 1, symbol="BTCUSDT")
#     result = await a['aiohttpMethod'](**a.get("params"))
#     print(result)

# if __name__ == "__main__":
#     asyncio.run(main())

from exchangeinfo import binanceInfo

class CommunicationsManager:

    @classmethod
    def make_request(cls, connection_data : dict):
        if "maximum_retries"  not in connection_data:
            raise ValueError("maximum_retries are not in connection data")
        for index, _ in enumerate(range(connection_data.get("maximum_retries"))):
            response = requests.get(connection_data.get("url"), params=connection_data.get("params"), headers=connection_data.get("headers"))
            if response.status_code == 200:
                return {
                    "instrument" : connection_data.get("instrumentName").lower(),
                    "exchange" : connection_data.get("exchange").lower(),
                    "insType" : connection_data.get("insTypeName").lower(),
                    "response" : response.json() ,
                }
            if response.get('code', None) == connection_data.get("repeat_response_code"):
                connection_data["params"]["limit"] = connection_data["params"]["limit"] - connection_data.get("books_decrement")
                time.sleep(1)
            if index == len(connection_data.get("maximum_retries")):
                print(response.status_code)
    
    @classmethod
    def make_request_v2(cls, connection_data:dict):
        url = connection_data.get("url")
        headers = connection_data.get("headers")
        payload = connection_data.get("payload")
        response = requests.request("GET", url, headers=headers, data=payload)
        return {
            "instrument" : connection_data.get("instrumentName").lower(),
            "exchange" : connection_data.get("exchange").lower(),
            "insType" : connection_data.get("insTypeName").lower(),
            "response" : response.json() ,
        }

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

class binance(CommunicationsManager, binanceInfo):
    """
        Abstraction for binance API calls for depth, funding, oi, tta, ttp and gta
    """
    binance_api_endpoints = binance_api_endpoints
    binance_api_basepoints = binance_api_basepoints
    binance_api_basepoints_params = binance_api_basepoints_params
    binance_ws_endpoints = binance_ws_endpoints
    binance_ws_basepoints = binance_ws_basepoints
    binance_ws_request_params = binance_ws_request_params
    binance_repeat_response_code = -1130
    binance_stream_keys = binance_stream_keys

    def __init__(self):
        pass

    @classmethod
    def binance_buildRequest(cls, insType:str, objective:str, maximum_retries:int=10, books_dercemet:int=500, **kwargs)->dict: 
        """
            insType : spot, perpetual, future, option
            objective : depth, funding, oi, tta, ttp, gta
            maximum_retries : if the request was unsuccessufl because of the length
            books_decremet : length of the books to decrease for the next request
            @@kwargs : depends on the request
        """
        # Strandarize names name
        params = dict(kwargs)
        params["symbol"] = params["symbol"].upper()
        instrument_name = params["symbol"].lower().replace("_", "")

        # Find marginType
        marginType=""
        if insType == "perpetual":
            marginType = "LinearPerpetual" if "USDT" in  params["symbol"].upper() else "InversePerpetual"
        if insType == "future":
            marginType = "LinearFuture" if "USDT" not in  params["symbol"].upper() else "InverseFuture"

        # this apis are not standarize, correct it
        if objective in "tta_ttp_gta" and "Inverse" in marginType:
            params["pair"] = params.pop("symbol").split("_")[0]
        if insType == "option":
            params["underlyingAsset"] = params.pop("symbol").split("_")[0]
        objective = "tta_ttp_gta" if objective in "tta_ttp_gta" else objective

        # Get url
        if insType in ["perpetual", "future"]:
            endpoint = cls.binance_api_endpoints.get(insType).get(marginType)
            basepoint = cls.binance_api_basepoints.get(insType).get(marginType).get(objective)
        else:
            endpoint = cls.binance_api_endpoints.get(insType)
            basepoint = cls.binance_api_basepoints.get(insType).get(objective)
        url = f"{endpoint}{basepoint}"
        headers = {}
        return {
            "url" : url, 
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrumentName" : instrument_name, 
            "insTypeName" : insType, 
            "exchange" : "binance", 
            "repeat_code" : cls.binance_repeat_response_code,
            "maximum_retries" : maximum_retries, 
            "books_dercemet" : books_dercemet
            }
    
    @classmethod
    def binance_fetch(cls, *args, **kwargs):
        connection_data = cls.binance_buildRequest(*args, **kwargs)
        response = cls.make_request(connection_data)
        return response

    @classmethod
    async def binance_aiohttpFetch(cls, *args, **kwargs):
        connection_data = cls.binance_buildRequest(*args, **kwargs)
        response = await cls.make_aiohttpRequest(connection_data)
        return response   
    
    @classmethod
    def binance_build_ws_method(cls, insType, **kwargs):
        """
            insType : spot, perpetual, option, future
            kwargs order: symbol, objective, everything else
        """
        params = dict(kwargs)
        standart_objective_name = params["objective"]
        params["objective"] = cls.binance_stream_keys.get(params["objective"])
        params["symbol"] = params["symbol"].lower()
        values = list(params.values())
        message = {
            "method": "SUBSCRIBE", 
            "params": [f"{'@'.join(values)}"], 
            "id": generate_random_integer(10)
        }
        return message, insType, standart_objective_name    
    
    @classmethod
    def binance_option_expiration(cls, symbol):
        """
            Looks for unexpired onption
        """
        data = cls.binance_info("option").get("optionSymbols")
        symbols = [x["symbol"] for x in data if symbol.upper() in x["symbol"].upper() and  datetime.fromtimestamp(int(x["expiryDate"]) / 1000) > datetime.now()]
        expirations = list(set([x.split("-")[1] for x in symbols]))
        return expirations

    @classmethod
    async def binance_retrive_option_oi(cls, symbol):
        """
            BTC, ETH ...
        """
        expirations =  cls.binance_option_expiration(symbol)
        full = []
        for expiration in expirations:
            data = await cls.binance_aiohttpFetch("option", "oi", expiration=expiration, symbol=symbol)
            full.append(data)
        return full

    @classmethod
    def binance_build_option_api_connectionData(cls, symbol, pullTimeout):
        """
            call aiohttp method with args
        """
    
        data =  {
                "type" : "api",
                "id_ws" : f"binance_ws_option_oi_{symbol.lower()}",
                "exchange":"binance", 
                "instrument": symbol.lower(),
                "instType": "option",
                "objective": "oi", 
                "pullTimeout" : pullTimeout,
                "aiohttpMethod" : cls.binance_retrive_option_oi,
                "args" : symbol
                }
        
        return data
    
    @classmethod
    def binance_build_ws_connectionData(cls, insType, needSnap=False, snaplimit=1000, **kwargs):
        """
            insType : deptj, trades, liquidations
            order : symbol, objective, everything else
            needSnap and snap limit: you need to fetch the full order book, use these
            Example of snaping complete books snapshot : connectionData.get("sbmethod")(dic.get("instType"), connectionData.get("objective"), **connectionData.get("sbPar"))
        """
        params = dict(kwargs)
        message, insType, standart_objective_name = cls.binance_build_ws_method(insType, **params)
        # Find marginType
        marginType=""
        if insType == "perpetual":
            marginType = "LinearPerpetual" if "USDT" in  params["symbol"].upper() else "InversePerpetual"
        if insType == "future":
            marginType = "LinearFuture" if "USDT" in  params["symbol"].upper() else "InverseFuture"

        endpoint = cls.binance_ws_endpoints.get(insType)
        if insType in ["perpetual", "future"]:
            endpoint = endpoint.get(insType)
            
        connection_data =     {
                                "type" : "ws",
                                "id_ws" : f"binance_ws_{insType}_{standart_objective_name}_{params['symbol'].lower()}",
                                "exchange":"binance", 
                                "instrument": params['symbol'].lower(),
                                "instType": insType,
                                "objective":standart_objective_name, 
                                "updateSpeed" : None,
                                "url" : endpoint,
                                "msg" : message,
                                "sbmethod" : None
                            }
        
        if needSnap is True:
            connection_data["id_api"] = f"binance_api_{insType}_{standart_objective_name}_{params['symbol'].lower()}",
            connection_data["sbmethod"] = cls.binance_fetch 
            connection_data["sbPar"] = {
                "symbol": params['symbol'].upper(), 
                "limit" : int(snaplimit)
            }

        return connection_data

    @classmethod
    def binance_build_api_connectionData(cls, insType:str, objective:str, pullTimeout:int, **kwargs):
        """
            insType : deptj, funding, oi, tta, ttp, gta
            **kwargs, symbol limit, period. Order doesnt matter
            result = d['aiohttpMethod'](**kwargs)
            pullTimeout : how many seconds to wait before you make another call
        """
        connectionData = cls.binance_buildRequest(insType, objective, **kwargs)
        params = dict(**kwargs)
            
        data =  {
                "type" : "api",
                "id_ws" : f"binance_api_{insType}_{objective}_{params['symbol'].lower()}",
                "exchange":"binance", 
                "instrument": params['symbol'].lower(),
                "instType": insType,
                "objective": objective, 
                "pullTimeout" : pullTimeout,
                "connectionData" : connectionData,
                "aiohttpMethod" : partial(cls.binance_aiohttpFetch, insType=insType, objective=objective),
                "params" : dict(**kwargs)
                }
        
        return data

class bybit(CommunicationsManager):
    bybit_api_endpoint = bybit_api_endpoint
    bybit_api_basepoints = bybit_api_basepoint
    bybit_ws_endpoints = bybit_ws_endpoints
    bybit_stream_keys = bybit_stream_keys
    bybit_repeat_response_code = -1130
    bybit_api_category_map = bybit_api_category_map
# {
#             "op": 
#             "subscribe","args": [
#                 "publicTrade.BTCUSDT" if depth there is something else
#                 ]
#             }

    @classmethod
    def bybit_buildRequest(cls, instType:str, objective:str, maximum_retries:int=10, books_dercemet:int=100, **kwargs)->dict: 
        """ 
            instType : "perpetual", "spot", "option", "future"
            Maxium retries of an API with different parameters in case API call is impossible. Useful when you cant catch the limit
            books_dercemet : the derement of books length in case of api call being unsuccessful. If applicable
            **kwargs : request parameters
        """
        params = dict(kwargs)
        params["symbol"] = params["symbol"].upper()

        symbol_name = params["symbol"]
        if instType == "option":
            params["baseCoin"] = params.pop("symbol")

        marginCoin = ""
        if instType == "perpetual":
            marginCoin = "LinearPerpetual" if "USDT" in params["symbol"] else "InversePerpetual"
        if instType == "future":
            marginCoin = "LinearFuture" if "USDT" in params["symbol"] else "InverseFuture"

        try:
            params["category"] = cls.bybit_api_category_map.get(instType).get(marginCoin)
        except:
            params["category"] = cls.bybit_api_category_map.get(instType)
        endpoint = cls.bybit_api_endpoint
        basepoint = cls.bybit_api_basepoints.get(objective)

        url = f"{endpoint}{basepoint}"
        headers = {}
        return {
            "url" : url, 
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrumentName" : symbol_name,
            "insTypeName" : instType,
            "exchange" : "bybit", 
            "repeat_code" : cls.bybit_repeat_response_code,
            "maximum_retries" : maximum_retries, 
            "books_dercemet" : books_dercemet
            }

    @classmethod
    def bybit_fetch(cls, *args, **kwargs):
        connection_data = cls.bybit_buildRequest(*args, **kwargs)
        response = cls.make_request(connection_data)
        return response

    @classmethod
    async def bybit_aiohttpFetch(cls, *args, **kwargs):
        connection_data = cls.bybit_buildRequest(*args, **kwargs)
        response = await cls.make_aiohttpRequest(connection_data)
        return response

    @classmethod
    def bybit_build_ws_method(cls, insType, **kwargs):
        """
            insType : spot, perpetual, option, future
            you must pass pullinterval to books
            kwargs order: symbol is the last
        """
        params = dict(kwargs)
        standart_objective_name = params["objective"]
        params["objective"] = cls.bybit_stream_keys.get(params["objective"])
        params["symbol"] = params["symbol"]
        values = list(params.values())
        message = {
            "op": 
            "subscribe","args": [f"{'.'.join(values)}"]
            }

        return message, insType, standart_objective_name    

    @classmethod
    def bybit_build_api_connectionData(cls, insType:str, objective:str, pullTimeout:int, **kwargs):
        """
            insType : depth, gta
            **kwargs, symbol limit ...  Order doesnt matter
            result = d['aiohttpMethod'](**kwargs)
            pullTimeout : how many seconds to wait before you make another call
        """
        connectionData = cls.bybit_buildRequest(insType, objective, **kwargs)
        params = dict(**kwargs)
            
        data =  {
                "type" : "api",
                "id_ws" : f"bybit_api_{insType}_{objective}_{params['symbol'].lower()}",
                "exchange":"bybit", 
                "instrument": params['symbol'].lower(),
                "instType": insType,
                "objective": objective, 
                "pullTimeout" : pullTimeout,
                "connectionData" : connectionData,
                "aiohttpMethod" : partial(cls.bybit_aiohttpFetch, insType=insType, objective=objective),
                "params" : dict(**kwargs)
                }
        
        return data

    @classmethod
    def bybit_build_ws_connectionData(cls, insType, needSnap=False, snaplimit=1000, **kwargs):
        """
            insType : depth, trades, oifunding
            order : symbol, objective, everything else
            needSnap and snap limit: you need to fetch the full order book, use these
            Example of snaping complete books snapshot : connectionData.get("sbmethod")(dic.get("instType"), connectionData.get("objective"), **connectionData.get("sbPar"))
        """
        params = dict(kwargs)
        message, insType, standart_objective_name = cls.bybit_build_api_connectionData(insType, **params)
        # Find marginType
        marginType=""
        if insType == "perpetual":
            marginType = "LinearPerpetual" if "USDT" in  params["symbol"].upper() else "InversePerpetual"
        if insType == "future":
            marginType = "LinearFuture" if "USDT" in  params["symbol"].upper() else "InverseFuture"

        endpoint = cls.binance_ws_endpoints.get(insType)
        if insType in ["perpetual", "future"]:
            endpoint = endpoint.get(insType)
            
        connection_data =     {
                                "type" : "ws",
                                "id_ws" : f"binance_ws_{insType}_{standart_objective_name}_{params['symbol'].lower()}",
                                "exchange":"binance", 
                                "instrument": params['symbol'].lower(),
                                "instType": insType,
                                "objective":standart_objective_name, 
                                "updateSpeed" : None,
                                "url" : endpoint,
                                "msg" : message,
                                "sbmethod" : None
                            }
        
        if needSnap is True:
            connection_data["id_api"] = f"binance_api_{insType}_{standart_objective_name}_{params['symbol'].lower()}",
            connection_data["sbmethod"] = cls.binance_fetch 
            connection_data["sbPar"] = {
                "symbol": params['symbol'].upper(), 
                "limit" : int(snaplimit)
            }

        return connection_data
    
print(bybit.fetch("perpetual", "depth", symbol="btcusd", limit=100))
    
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

# Fix instType Kucoin

class kucoin(CommunicationsManager):
    """
        Abstraction of kucoin api calls
    """

    def __init__ (self, apikey, secretkey, password):
        self.repeat_response_code = -1130
        self.apikey = apikey
        self.secretkey = secretkey
        self.password = password
        self.repeat_response_code = -1130
        self.endpoints = {
            "spot" : "https://api.kucoin.com",
            "perp" : "https://api-futures.kucoin.com",
        }
        self.basepoints = {
            "spot" : {
                "depth" : "/api/v3/market/orderbook/level2"
            },
            "perp" : {
                "depth" : "/api/v1/level2/snapshot"
            }
        }
        self.default_params  = {
            "spot" :  { "depth" : {"symbol": {"type": str, "default": "BTC-USDT"}}},
            "perp" :  { "depth" :  {"symbol": {"type": str, "default": "XBTUSDTM"}}},
                }

    def buildRequest(self, instType:str, objective:str, maximum_retries:int=10, books_dercemet:int=100, **kwargs)->dict: 
        """
            instType : spot, perp
            objective :  depth
            Maxium retries of an API with different parameters in case API call is impossible. Useful when you cant catch the limit
            books_dercemet : the derement of books length in case of api call being unsuccessful. If applicable
            **kwargs : request parameters like symbol
        """
        params = dict(kwargs)
        if instType == "spot":
            instrument = params.get("symbol")
        if instType == "perp":
            instrument = params.get("symbol").replace("XBT", "BTC").replace("USDTM", "USDT")
        insTypeName = instType
        endpoint = self.endpoints.get(instType)
        basepoint = self.basepoints.get(instType).get(objective)
        # basepoint_headers = "?".join([basepoint, urllib.parse.urlencode(params)])
        # basepoint_headers = self.parse_basepoint_params(basepoint, params)
        payload = ''
        headers = self.build_headers(basepoint, params)
        return {
            "url" : endpoint + basepoint,
            "endpoint" : endpoint, 
            "basepoint" : basepoint,
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrumentName" : instrument.replace("-", ""),
            "insTypeName" : insTypeName, 
            "exchange" : "kucoin", 
            "repeat_code" : self.repeat_response_code,
            "maximum_retries" : maximum_retries, 
            "books_dercemet" : books_dercemet,
            "payload" : payload
            }
    
    def parse_basepoint_params(self, basepoint, params):
        return "?".join([basepoint, urllib.parse.urlencode(params) if params else ""])
        # return basepoint + ("?" + urllib.parse.urlencode(params) if params else "")

    def build_headers(self, basepoint, params):
        basepoint_headers = self.parse_basepoint_params(basepoint, params)
        apikey = self.apikey 
        secretkey = self.secretkey
        password = self.password 
        now = int(time.time() * 1000)
        str_to_sign = str(now) + "GET" + basepoint_headers
        signature = base64.b64encode(hmac.new(secretkey.encode("utf-8"), str_to_sign.encode("utf-8"), hashlib.sha256).digest())
        headers = {
            "KC-API-SIGN": signature,
            "KC-API-TIMESTAMP": str(now),
            "KC-API-KEY": apikey,
            "KC-API-PASSPHRASE": password,
        }
        return headers

    def fetch(self, *args, **kwargs):
        connection_data = self.buildRequest(*args, **kwargs)
        response = CommunicationsManager.make_request(connection_data)
        return response

class bingx(CommunicationsManager):
    """
        Abstraction of kucoin api calls
    """
    default_params  = {
        "spot" :  { 
            "depth" : {
                    "symbol": {"type": str, "default": "BTC-USDT"},
                    "limit": {"type": int, "default": 1000}, # p = [5, 10, 20, 50, 100, 500, 1000]
                },
        "perp": {  
                "depth" : {
                        "symbol": {"type": str, "default": "BTC-USDT"},
                        "limit": {"type": int, "default": 1000}, # p = [5, 10, 20, 50, 100, 500, 1000]
                    },
                "oi" : {
                        "symbol": {"type": str, "default": "BTC-USDT"},
                },
                "funding" : {
                        "symbol": {"type": str, "default": "BTC-USDT"},
                }
            }
        }
    }

    def __init__ (self, apikey, secretkey):
        self.repeat_response_code = -1130
        self.apikey = apikey
        self.secretkey = secretkey
        self.endpoint = "https://open-api.bingx.com"
        self.basepoints = {
            "spot" : {
                "depth" : "/openApi/spot/v1/market/depth"
            },
            "perp" : {
                "depth" : "/openApi/swap/v2/quote/depth",
                "oi" : "/openApi/swap/v2/quote/openInterest",
                "funding" : "/openApi/swap/v2/quote/premiumIndex",
            }
        }


    def buildRequest(self, instType:str, objective:str, 
                     possible_limits:list=[1000, 500, 100, 50, 20, 10, 5], books_dercemet:int=100, **kwargs)->dict: 
        """
            instType : spot, derivate
            objective :  depth, funding, oi
            Maxium retries of an API with different parameters in case API call is impossible. Useful when you cant catch the limit
            books_dercemet : the derement of books length in case of api call being unsuccessful. If applicable
            **kwargs : request parameters like symbol
        """
        params = dict(kwargs)
        instrument = params.get("symbol").replace("-", "").lower()
        if instType == "derivate":
            insTypeName = "future" if bool(re.search(r'\d', instrument)) else "perp"
        if instType == "spot":
            insTypeName = "spot"
        endpoint = self.endpoint
        basepoint = self.basepoints.get(insTypeName).get(objective)
        payload = {}
        url, headers = self.get_url_headers(endpoint, basepoint, params, self.apikey, self.secretkey)
        return {
            "url" : url,
            "endpoint" : endpoint, 
            "basepoint" : url,
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrumentName" : instrument,
            "insTypeName" : insTypeName, 
            "exchange" : "bingx", 
            "repeat_code" : self.repeat_response_code,
            "maximum_retries" : 1, 
            "books_dercemet" : books_dercemet,
            "payload" : payload,
            "possible_limits" : possible_limits
            }

    @classmethod
    def get_url_headers(cls, endpoint, basepoint, params, api, secret):
        parsed_params = cls.parseParam(params)
        url = "%s%s?%s&signature=%s" % (endpoint, basepoint, parsed_params, cls.get_sign(secret, parsed_params))
        headers = {
            'X-BX-APIKEY': api,
        }
        return url, headers

    @classmethod
    def parseParam(cls, params):
        sortedKeys = sorted(params)
        paramsStr = "&".join(["%s=%s" % (x, params[x]) for x in sortedKeys])
        if paramsStr != "": 
            return paramsStr+"&timestamp="+str(int(time.time() * 1000))
        else:
            return paramsStr+"timestamp="+str(int(time.time() * 1000))
    
    @classmethod
    def get_sign(cls, api_secret, payload):
        signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
        return signature

    def fetch(self, *args, **kwargs):
        connection_data = self.buildRequest(*args, **kwargs)
        if "limit" in connection_data:
            possible_limits = connection_data.get("possible_limits")
            possible_limits = sorted(possible_limits, reverse=True)
            for limit in possible_limits:
                try:
                    connection_data["limit"] = limit
                    response = CommunicationsManager.make_request_v2(connection_data)
                    return response
                except Exception as e:
                    print(f"Connection failed with limit {limit}: {e}")
                    continue
        else:
            return CommunicationsManager.make_request_v2(connection_data)

    async def aiohttpFetch(self, *args, **kwargs):
        connection_data = self.buildRequest(*args, **kwargs)
        if "limit" in connection_data:
            possible_limits = connection_data.get("possible_limits")
            possible_limits = sorted(possible_limits, reverse=True)
            for limit in possible_limits:
                try:
                    connection_data["limit"] = limit
                    response = await CommunicationsManager.make_aiohttpRequest(connection_data)
                    return response
                except Exception as e:
                    print(f"Connection failed with limit {limit}: {e}")
                    time.sleep(2)
                    continue
        else:
            return CommunicationsManager.make_request_v2(connection_data)
    
class bitget(CommunicationsManager):
    """
        Abstraction of bybit api calls
    """
    repeat_response_code = -1130
    endpoint = "https://api.bitget.com"
    basepoints = {
        "spot" : {
            "depth" : "/api/v2/spot/market/orderbook",
        },
        "perp" : {
            "depth" : "/api/v2/mix/market/merge-depth",
        }
    }
    default_params  = {
        "spot" : {
            "depth" :  {
                "symbol" : { "type" : str},
                "type" : { "type" : str, "default": "step0"}, # no aggregation
                "limit" : { "type" : int, "max": 150},
                }
        },
        "perp" : {
            "depth" : {
                "symbol" : { "type" : str},
                "limit" : { "type" : int, "max": 1000},
                "productType" : {"type" : str, "default" : "usdt-futures"}
            }
        }
    }
            

        # "url" : "https://api.bitget.com/api/v2/spot/market/orderbook?symbol=BTCUSDT&type=step0&limit=150" , # simple get request
        # "url" : "https://api.bitget.com/api/v2/mix/market/merge-depth?productType=usdt-futures&symbol=BTCUSDT&limit=1000", 

    @classmethod
    def buildRequest(cls, instType:str, objective:str, maximum_retries:int=10, books_dercemet:int=100, **kwargs)->dict: 
        """
            objective :  depth
            **kwargs : request parameters
        """
        params = dict(kwargs)
        instrument = params.get("symbol").replace("-", "")
        if instType == "derivate":
            insTypeName = "future" if bool(re.search(r'\d', instrument)) else "perp"
        if instType == "spot":
            insTypeName = "spot"
        if insTypeName == "perp":
            params["productType"] = "usdt-futures"
        endpoint = cls.endpoint
        basepoint = cls.basepoints.get(insTypeName).get(objective)
        url = endpoint + basepoint
        headers = {}
        return {
            "url" : url,
            "basepoint" : basepoint,  
            "endpoint" : endpoint,  
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrumentName" : instrument.lower(), 
            "insTypeName" : insTypeName.lower(), 
            "exchange" : "bitget", 
            "repeat_code" : cls.repeat_response_code,
            "maximum_retries" : maximum_retries, 
            "books_dercemet" : books_dercemet,
            "payload" : "",
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

class deribit(CommunicationsManager):
    """
        Abstraction of bybit api calls
    """
    repeat_response_code = -1130
    endpoint = "wss://test.deribit.com/ws/api/v2"
    endpoints = {
        "derivate" : {
            "derivate" : { 
                "depth" : "get_order_book",
            }
        },
        "option" : {
            "oifunding" : "get_book_summary_by_currency"
        }
    }
    params = {
        "derivate" : {
            "derivate" : { 
                "depth" : {"get_order_book" : ["limit", "symbol"]},
            }
        },
        "option" : {
            "oifunding" : {"get_book_summary_by_currency" : ["currency", "kind"]},
        }
    }


    @classmethod
    def create_payload(cls, basepoint, params):
        payload =  {
            "jsonrpc": "2.0", "id": generate_random_integer(10), 
            "method": f"public/{basepoint}",
            "params": params,
        }
        return payload


    @classmethod
    def buildRequest(cls, instType:str, objective:str, maximum_retries:int=10, books_dercemet:int=100, **kwargs)->dict: 
        """
            instType : derivative, option
            objective :  depth, oifunding
            **kwargs : limit, symbol for  depth
                        currency, kind for oi
        """
        params = dict(kwargs)
        # Some logic here
        if None:
            pass
        instrument = params





        if instType == "option":
            instrument = params.get("symbol").lower()


        instrument = params.get("symbol").replace("-", "")
        if instType == "derivate":
            insTypeName = "future" if bool(re.search(r'\d', instrument)) else "perp"
        if instType == "spot":
            insTypeName = "spot"
        if insTypeName == "perp":
            params["productType"] = "usdt-futures"
        endpoint = cls.endpoint
        basepoint = cls.basepoints.get(insTypeName).get(objective)
        url = endpoint + basepoint
        headers = {}
        return {
            "url" : url,
            "basepoint" : basepoint,  
            "endpoint" : endpoint,  
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrumentName" : instrument.lower(), 
            "insTypeName" : insTypeName.lower(), 
            "exchange" : "bitget", 
            "repeat_code" : cls.repeat_response_code,
            "maximum_retries" : maximum_retries, 
            "books_dercemet" : books_dercemet,
            "payload" : "",
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


# print(bitget.buildRequest("derivate", "depth", symbol="BTCUSDT", limit=150))

# print(bitget.fetch("derivate", "depth", symbol="BTCUSDT", limit=25))

# b = bingx("", "")
# async def example():
#     a = await b.aiohttpFetch("derivate", "depth", symbol="BTC-USDT")
#     print(a)

# asyncio.run(example())
    






#     "mexc" : {
#         "spot" : "https://api.mexc.com", 
#         "perp" : "https://contract.mexc.com",
#     },
#     "htx" : {
#         "spot" : "https://api.huobi.pro",
#         "perp" : "https://api.hbdm.com",
#     },
#     "gateio" : "https://api.gateio.ws",
#     "deribit" : "wss://test.deribit.com",

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

