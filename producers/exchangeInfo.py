import requests
import aiohttp
import http
import asyncio
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





class requestHandler():

    @classmethod
    def simple_request(cls, url):
        r = requests.get(url)
        print(r.status_code)
        r = r.json()
        return r

    @classmethod
    def request_with_headers(cls, url, headers, payload=""):
        r = requests.get(url, headers=headers, payload=payload)
        print(r.status_code)
        r = r.json()
        return r

    @classmethod
    def request_full(cls, url, headers, params, payload=""):
        r = requests.get(url, headers=headers, params=params)
        print(r.status_code)
        r = r.json()
        return r
    
    @classmethod
    def http_call(cls, endpoint, basepoint, payload, headers):
        conn = http.client.HTTPSConnection(endpoint)
        conn.request("GET", basepoint, payload, headers)
        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))
    
class bybitInfo(requestHandler):
    bybit_info_url = {
                        "spot" : "https://api.bybit.com/v5/market/instruments-info?category=spot",
                        "perpetual" : {
                            "LinearPerpetual" : "https://api.bybit.com/v5/market/instruments-info?category=linear",
                            "InverseFutures" : "https://api.bybit.com/v5/market/instruments-info?category=inverse"
                        },
                        "future" : {
                            "LinearPerpetual" : "https://api.bybit.com/v5/market/instruments-info?category=linear",
                            "InverseFutures" : "https://api.bybit.com/v5/market/instruments-info?category=inverse"
                        },
                        "option" : "https://api.bybit.com/v5/market/instruments-info?category=option"
                    }
    bybit_call_example = {
                "spot" : "BTCUSDT",
                "perpetual" : {
                    "LinearPerpetual" : "BTCUSDT",
                    "LinearFutures" : "BTCUSD",
                },
                "future" : {
                    "InverseFutures" : "BTCUSD",
                    "InverseFutures" : "ETHUSDH24",
                },
                "option" : "ETH-3JAN23-1250-P"
            }

    @classmethod
    def symbols_by_instType(cls, isntType):
        """ 
            spot, perpetual, future, option
        """
        urls = cls.bybit_info_url.get(isntType)
        if isinstance(urls, dict):
            symbols_by_type = {}
            for productType, url in urls.items():
                data = cls.simple_request(url).get("result").get("list")
                symbols = [d.get("symbol")  for d in data if d.get("contractType") == productType]
                symbols_by_type[productType] = symbols
                time.sleep(1)
            return symbols_by_type
        else:
            data = cls.simple_request(urls).get("result").get("list")
            symbols = [d.get("symbol")  for d in data]
            return symbols
    
    @classmethod
    def symbols(cls) -> dict:
        """
            spot, perpetual, future, option
        """
        di = {

        }
        for isntType in cls.bybit_info_url.keys():
            data = cls.symbols_by_instType(isntType)
            di[isntType] = data
        return di


    # exchange_infos = {
    # "binance" : {
    #     "spot" : "https://api.binance.com/api/v1/exchangeInfo",
    #     "linear" : "https://fapi.binance.com/fapi/v1/exchangeInfo",
    #     "inverse" : "https://dapi.binance.com/dapi/v1/exchangeInfo",
    #     "option" : "https://eapi.binance.com/eapi/v1/exchangeInfo"
    # },

class binanceInfo(requestHandler):
    binance_info_url = {
                        "spot" : "https://api.binance.com/api/v3/exchangeInfo",
                        "perpetual" : {
                            "LinearPerpetual" : "https://fapi.binance.com/fapi/v1/exchangeInfo",
                            "InverseFutures" : "https://dapi.binance.com/dapi/v1/exchangeInfo"
                        },
                        "future" : {
                            "LinearPerpetual" : "https://fapi.binance.com/fapi/v1/exchangeInfo",
                            "InverseFutures" : "https://dapi.binance.com/dapi/v1/exchangeInfo"
                        },
                        "option" : "https://eapi.binance.com/eapi/v3/exchangeInfo"
                    }
    binance_call_example = {
                "spot" : "BTCUSDT",
                "perpetual" : {
                    "LinearPerpetual" : "BTCUSDT",
                    "InversePerpetual" : "BTCUSD",
                },
                "future" : {
                    "LinearFuture" : "BTCUSD",
                    "InverseFuture" : "ETHUSDH24",
                },
                "option" : "ETH-3JAN23-1250-P"
            }
    contract_typess = {
        "perpetual" : ['PERPETUAL', 'PERPETUAL DELIVERING'],
        "future" : ['CURRENT_QUARTER', 'NEXT_QUARTER']
    }

    @classmethod
    def contract_types(cls, isntType):
        urls = cls.binance_info_url.get(isntType)
        if isinstance(urls, dict):
            symbols_by_type = {}
            for productType, url in urls.items():
                data = cls.simple_request(url).get("symbols")
                symbols = set([d.get("contractType")  for d in data])
                symbols_by_type[productType] = symbols
                time.sleep(1)
            return symbols_by_type
        else:
            print("Options and spot have no different coin Margins")
    
    @classmethod
    def all_contract_type(cls):
        di = {}
        for isntType in cls.binance_info_url.keys():
            data = cls.contract_types(isntType)
            di[isntType] = data
        return di
    
    @classmethod
    def symbols_by_instType(cls, isntType):
        """ 
            spot, perpetual, future, option
        """
        urls = cls.binance_info_url.get(isntType)
        if isinstance(urls, dict):
            symbols_by_type = {}
            for productType, url in urls.items():
                data = cls.simple_request(url).get("symbols")
                symbols = [d.get("symbol")  for d in data if d.get("contractType") in cls.contract_typess.get(isntType)]
                symbols_by_type[productType] = symbols
                time.sleep(1)
            return symbols_by_type
        else:
            data = cls.simple_request(urls).get("symbols")
            symbols = [d.get("symbol")  for d in data]
            return symbols
    
    @classmethod
    def symbols(cls) -> dict:
        """
            spot, perpetual, future, option
        """
        di = {}
        for isntType in cls.binance_info_url.keys():
            data = cls.symbols_by_instType(isntType)
            di[isntType] = data
        return di

class okxInfo(requestHandler):

    okx_info_url = {  
        "spot" : "https://www.okx.com/api/v5/public/instruments?instType=SPOT",
        "perpetual" : "https://www.okx.com/api/v5/public/instruments?instType=SWAP",
        "futures" : "https://www.okx.com/api/v5/public/instruments?instType=FUTURES",
        "option" : "https://www.okx.com/api/v5/public/instruments?instType=OPTION&instFamily=BTC-USD",
    }
    okx_call_example = {
                "spot" : "BTCUSDT",
                "perpetual" : {
                    "LinearPerpetual" : 'BTC-USDT-SWAP',
                    "InverseFutures" : 'BTC-USD-SWAP',
                },
                "future" : {
                    "LinearPerpetual" : "BTC-USD-240315",
                    "InverseFutures" : "BTC-USD-240315",
                },
                "option" : "BTC-USD-241227-30000-P"
            }

    @classmethod
    def symbols_by_instType(cls, isntType):
        """ 
            spot, perpetual, future, option
        """
        urls = cls.okx_info_url.get(isntType)
        data = cls.simple_request(urls).get("data")
        symbols = [d["instId"] for d in data]
        return symbols
    
    @classmethod
    def symbols(cls) -> dict:
        """
            spot, perpetual, future, option
        """
        di = {

        }
        for isntType in cls.okx_info_url.keys():
            data = cls.symbols_by_instType(isntType)
            di[isntType] = data
        return di

class kucoinInfo(requestHandler):
    endpoints = {  
        "spot" : "https://api.kucoin.com",   
        "perpetual" : "https://api-futures.kucoin.com",  
    }
    basepoints = {  
        "spot" : "/api/v2/symbols",    
        "perpetual" : "/api/v1/contracts/active",  
    }
    params = {}
    kucoin_call_example = {
                "spot" : "BTC-USDT",
                "perpetual" : "XBTUSDTM"
            }

    @classmethod
    def symbols_by_instType(cls, isntType):
        """ 
            spot, perpetual, future, option
        """
        endpoint = cls.endpoints.get(isntType)
        basepoint = cls.basepoints.get(isntType)
        url = endpoint + basepoint
        r = cls.simple_request(url)
        data = r.get("data")
        symbols = [d["symbol"] for d in data]
        return symbols
    
    @classmethod
    def symbols(cls) -> dict:
        """
            spot, perpetual, future, option
        """
        di = {

        }
        for isntType in cls.kucoin_call_example.keys():
            data = cls.symbols_by_instType(isntType)
            di[isntType] = data
        return di


def iterate_dict(d):
    v = []
    if isinstance(d, dict):
        for key, value in d.items():
            if isinstance(value, dict):
                iterate_dict(value)
                v.extend(iterate_dict(value))
            else:
                v.append(value)
    else:
        v.append(d)
    return v


def unnest_list(lst):
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(unnest_list(item))
        else:
            result.append(item)
    return result

def recursive_dict_access(dictionary, keys):
    if "." in keys:
        keys = keys.split(".")
    else:
        pass
    key = keys[0]
    if key in dictionary:
        if isinstance(dictionary[key], dict):
            return recursive_dict_access(dictionary[key], keys[1:])
        else:
            return dictionary[key]    
    else:
        return None

class bitgetInfo(requestHandler):

    bitget_info_url = {  
        "spot" : "https://api.bitget.com/api/v2/spot/public/symbols",
        "perpetual" : {
            "LinearPerpetual" : {
                "usdt" : "https://api.bitget.com/api/v2/mix/market/tickers?productType=USDT-FUTURES",
                "usdc" : "https://api.bitget.com/api/v2/mix/market/tickers?productType=USDC-FUTURES",
            },
            "InversePerpetual" : "https://api.bitget.com/api/v2/mix/market/tickers?productType=COIN-FUTURES"
        } 
    }
    bitget_call_example = {
                "spot" : "BTCUSDT",
                "perpetual" : {
                    "LinearPerpetual" : ['BTCUSDT', "BTCPERP"],
                    "InverseFutures" : 'BTCUSD',
                },
            }

    @classmethod
    def bitget_symbols_by_instType(cls, instType):
        """ 
            spot, perpetual
        """
        links = iterate_dict(cls.bitget_info_url.get(instType))
        d = []
        for url in links:
            data = cls.simple_request(url).get("data")
            symbols = [d["symbol"] for d in data]
            d.append(symbols)
        return unnest_list(d)
    
    @classmethod
    def bitget_symbols(cls) -> dict:
        """
            spot, perpetual, future, option
        """
        di = {
        }
        for isntType in cls.bitget_info_url.keys():
            data = cls.bitget_symbols_by_instType(isntType)
            di[isntType] = data
        return di
    
    @classmethod
    def info_bitget(cls, instType):
        """
            Check the bitget_info_url
            Ex:
            instType = "perpetual.LinearPerpetual.usdt
        """
        keys = instType.split(".")
        link = recursive_dict_access(cls.bitget_info_url, keys)
        return cls.simple_request(link).get("data")


class bingxInfo(requestHandler):

    bingx_endpoint = "https://open-api.bingx.com"
    bings_basepoints = {
        "spot" : "/openApi/spot/v1/common/symbols",
        "perpetual" : "/openApi/swap/v2/quote/contracts"
    }
    bingx_call_example = {
        "spot" : "REVV-USDT",
        "perpetual" : "BTC-USDT"
            }
    @classmethod
    def demo(cls, endpoint, basepoint):
        payload = {}
        method = "GET"
        paramsMap = {}
        paramsStr = cls.parseParam(paramsMap)
        return cls.send_request(endpoint, method, basepoint, paramsStr, payload)
    @classmethod
    def get_sign(cls, api_secret, payload):
        signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
        return signature
    @classmethod
    def send_request(cls, endpoint, method, basepoint, urlpa, payload):
        url = "%s%s?%s&signature=%s" % (endpoint, basepoint, urlpa, cls.get_sign("", urlpa))
        headers = {
            'X-BX-APIKEY': endpoint,
        }
        response = requests.request(method, url, headers=headers, data=payload)
        return response.text
    @classmethod
    def parseParam(cls, paramsMap):
        sortedKeys = sorted(paramsMap)
        paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
        if paramsStr != "": 
            return paramsStr+"&timestamp="+str(int(time.time() * 1000))
        else:
            return paramsStr+"timestamp="+str(int(time.time() * 1000))


    @classmethod
    def bingx_symbols_by_instType(cls, instType):
        """ 
            spot, perpetua
        """
        data = json.loads(cls.demo(cls.bingx_endpoint, cls.bings_basepoints.get(instType)))
        try:
            symbols =  data.get("data").get("symbols")
        except:
            symbols =  data.get("data")
        return [s["symbol"] for s in symbols]
    
    @classmethod
    def bingx_symbols(cls) -> dict:
        """
            spot, perpetual, future, option
        """
        di = {}
        for isntType in cls.bings_basepoints.keys():
            data = cls.bingx_symbols_by_instType(isntType)
            di[isntType] = data
        return di
    
    @classmethod
    def info_bingex(cls, instType):
        """
            "spot" "perp"
        """
        data = json.loads(cls.demo(cls.bingx_endpoint, cls.bings_basepoints.get(instType)))
        return data


class mexcInfo(requestHandler):

    mexc_urls = {
        "spot" : "https://api.mexc.com/api/v3/exchangeInfo",
        "perpetual" : "https://contract.mexc.com/api/v1/contract/detail"
    }
    maxc_call_example = {
        "spot" : "PERCUSDT",
        "perpetual" : "BTC_USDT"
            }

    @classmethod
    def mexc_symbols_by_instType(cls, instType):
        """ 
            spot, perpetua
        """
        symbols = cls.simple_request(cls.mexc_urls.get(instType))
        try:
            symbols = symbols["symbols"]
        except:
            symbols = symbols["data"]
        return [s["symbol"] for s in symbols]
    
    @classmethod
    def mexc_symbols(cls) -> dict:
        """
            spot, perpetual, future, option
        """
        di = {}
        for isntType in cls.mexc_urls.keys():
            data = cls.mexc_symbols_by_instType(isntType)
            di[isntType] = data
        return di
    
    @classmethod
    def info_mexc(cls, instType):
        """
            "spot" "perp"
        """
        data = cls.simple_request(cls.mexc_urls.get(instType))
        return data


class deribitInfo(requestHandler):

    url = "https://test.deribit.com/api/v2/public/get_instruments"
    params = {"currency": "", "kind" : ""}
    headers = {"Content-Type": "application/json"}
    currecies = ["BTC", "ETH", "USDC", "USDT", "EURR"]

    @classmethod
    def deribit_symbols_by_instType(cls, instType):
        """ 
            perpetual, spot, future, option
        """
        if instType == "perpetual":
            instTypeC = "future"
        else:
            instTypeC = instType
        allsymbols = []
        for currency in cls.currecies:
            cls.params["currency"] = currency
            cls.params["kind"] = instTypeC
            data = cls.request_full(url=cls.url, headers=cls.headers, params=cls.params).get("result")
            symbols = [s["instrument_name"] for s in data]
            allsymbols.append(symbols)
        allsymbols = unnest_list(allsymbols)
        if instType == "perpetual":
            allsymbols = [x for x in allsymbols if "PERPETUAL" in x]
        if instType == "future":
            allsymbols = [x for x in allsymbols if "PERPETUAL" not in x]
        return allsymbols

    
    @classmethod
    def deribit_symbols(cls) -> dict:
        """
            spot, perpetual, future, option
        """
        di = {}
        for isntType in ["spot", "perpetual", "future", "option"]:
            data = cls.deribit_symbols_by_instType(isntType)
            di[isntType] = data
        return di
    
    @classmethod
    def info_deribit(cls, instType):
        """
            kind : spot, future, option
            currency : ["BTC", "ETH", "USDC", "USDT", "EURR"]
            so instType = spot.BTC, or option.ETH  .....

        """
        cls.params["kind"], cls.params["currency"] = instType.split(".")
        data = cls.request_full(url=cls.url, headers=cls.headers, params=cls.params).get("result")
        return data


class coinbaseInfo(requestHandler):
    
    def __init__(self, api, secret):
        self.api = api
        self.secret = secret
        self.payload = ''
        self.endpoint = "api.coinbase.com"
        self.basepoint = "/api/v3/brokerage/products"

    def info_coinbase(self):
        """
            spot, future
        """
        headers = self.build_headers()
        return self.http_call(self.endpoint, self.basepoint, self.payload, headers)

    def build_headers(self):
        key_name       =  self.api
        key_secret     =  self.secret
        request_method = "GET"
        request_host   = "api.coinbase.com"
        request_path   = "/api/v3/brokerage/products"
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
        headers = {
                    "Authorization": f"Bearer {jwt_token}",
                    'Content-Type': 'application/json'
                }
        return headers



class htxInfo(requestHandler):
    pass

class gateioInfo(requestHandler):
    pass

coinbaseSecret = '-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIDOVctxJpAI/hHtbUN9VrHej4bWPRuT9um9FoBlTgiyaoAoGCCqGSM49\nAwEHoUQDQgAEJt8JWIh8CHm045POImBF0ZvVuX5FbQjIDhIT82hE5r1+vb8cSQ3M\nfEjriBy1/ZD3EywPNxyGe6nO/Wsq0M8hXQ==\n-----END EC PRIVATE KEY-----\n'
coinbaseAPI = 'organizations/b6a02fc1-cbb0-4658-8bb2-702437518d70/apiKeys/697a8516-f2e2-4ec9-a593-464338d96f21'

cbase = coinbaseInfo(coinbaseAPI, coinbaseSecret)
print(cbase.info_coinbase())







# def build_jwt():
#     key_name       =  coinbaseAPI
#     key_secret     =  coinbaseSecret
#     request_method = "GET"
#     request_host   = "api.coinbase.com"
#     request_path   = "/api/v3/brokerage/products"
#     service_name   = "retail_rest_api_proxy"
#     private_key_bytes = key_secret.encode('utf-8')
#     private_key = serialization.load_pem_private_key(private_key_bytes, password=None)
#     uri = f"{request_method} {request_host}{request_path}"
#     jwt_payload = {
#         'sub': key_name,
#         'iss': "coinbase-cloud",
#         'nbf': int(time.time()),
#         'exp': int(time.time()) + 120,
#         'aud': [service_name],
#         'uri': uri,
#     }
#     jwt_token = jwt.encode(
#         jwt_payload,
#         private_key,
#         algorithm='ES256',
#         headers={'kid': key_name, 'nonce': secrets.token_hex()},
#     )
#     return jwt_token

# payload = ''
# headers = {
#     "Authorization": f"Bearer {build_jwt()}",
#     'Content-Type': 'application/json'
# }

# import http.client
# import json

# conn = http.client.HTTPSConnection("api.coinbase.com")
# conn.request("GET", "/api/v3/brokerage/products?product_type=SPOT", payload, headers)
# res = conn.getresponse()
# data = res.read()
# #data = json.loads(data)
# data