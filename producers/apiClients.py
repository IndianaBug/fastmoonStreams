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
import base64
import hashlib
import hmac
from hashlib import sha256 
from utilis import generate_random_integer

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
        basepoint_headers = "?".join([basepoint, urllib.parse.urlencode(params)])
        payload = ''
        headers = self.build_headers(basepoint_headers)
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

    def build_headers(self, basepoint):
        apikey = self.apikey 
        secretkey = self.secretkey
        password = self.password 
        now = int(time.time() * 1000)
        str_to_sign = str(now) + "GET" + basepoint
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
    create_header = {
        "perp" : {
            "depth" : lambda limit, symbol : {
                        "jsonrpc": "2.0", "id": generate_random_integer(10), 
                        "method": "public/get_order_book",
                        "params": { 
                            "depth": limit,     # 1000. the call will adjust automatically
                            "instrument_name": symbol # BTC-PERPETUAL
                            }
                        }
                },
        "option" : {
            "summary" : lambda kind, currency : {
                        "jsonrpc": "2.0", "id": generate_random_integer(10), 
                        "method": "public/get_book_summary_by_currency",
                        "params": { 
                                "currency": currency,  # BTC
                                "kind": kind           # option
                                }
                        }
                }
        }

    @classmethod
    def buildRequest(cls, instType:str, objective:str, maximum_retries:int=10, books_dercemet:int=100, **kwargs)->dict: 
        """
            instType : derivative, option
            objective :  depth, oi
            **kwargs : limit, symbol for  depth
                        currency, kind for oi
        """
        params = dict(kwargs)

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


    {   # Can only be called with websockets
        "type" : "api",
        "id" : "deribit_option_btc_OI",
        "exchange":"deribit", 
        "insType":"option", 
        "obj":"OI", 
        "instrument":"btcusd", 
        "updateSpeed":1800,
        "url" : "wss://test.deribit.com/ws/api/v2",  
        "msg" : {
            "jsonrpc": "2.0", "id": generate_random_integer(10), 
            "method": "public/get_book_summary_by_currency",
            "params": { 
                "currency": "BTC", 
                "kind": "option"
                }
            }
    },

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

