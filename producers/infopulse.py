import requests
import aiohttp
import http
import time
import rapidjson as json
import re
from cryptography.hazmat.primitives import serialization
import jwt
import secrets
import hmac
from hashlib import sha256 
from utilis import iterate_dict, unnest_list, recursive_dict_access
import re
import rapidjson as json
import aiohttp.streams
import ijson
import io
from datetime import datetime

class requestHandler():

    @classmethod
    def simple_request(cls, url):
        r = requests.get(url)
        r = json.loads(r)
        return r

    @classmethod
    def request_with_headers(cls, url, headers, payload=""):
        r = requests.get(url, headers=headers, payload=payload)
        r = json.loads(r)
        return r

    @classmethod
    def request_full(cls, url, headers, params, payload=""):
        r = requests.get(url, headers=headers, params=params)
        r = json.loads(r)
        return r

    @classmethod
    async def simple_request_async(cls, url, json_parser:callable=None):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()  
                response = await response.text()
                return response

    @classmethod
    async def request_with_headers_async(cls, url, headers, payload=""):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, data=payload) as response:
                response.raise_for_status()
                return await response

    @classmethod
    async def request_full_async(cls, url, headers, params, payload=""):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, data=payload) as response:
                response.raise_for_status()
                return await response


    @classmethod
    def http_call(cls, endpoint, basepoint, payload, headers):
        conn = http.client.HTTPSConnection(endpoint)
        conn.request("GET", basepoint, payload, headers)
        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")
    
class bybitInfo(requestHandler):
    bybit_info_url = {
                        "spot" : "https://api.bybit.com/v5/market/instruments-info?category=spot",
                        "perpetual" : {
                            "LinearPerpetual" : "https://api.bybit.com/v5/market/instruments-info?category=linear",
                            "InversePerpetual" : "https://api.bybit.com/v5/market/instruments-info?category=inverse"
                        },
                        "future" : {
                            "LinearFuture" : "https://api.bybit.com/v5/market/instruments-info?category=linear",
                            "InverseFuture" : "https://api.bybit.com/v5/market/instruments-info?category=inverse"
                        },
                        "option" : "https://api.bybit.com/v5/market/instruments-info?category=option"
                    }
        
    @classmethod
    def bybit_symbols_by_instType(cls, instType):
        """ 
            spot, perpetual
        """
        links = iterate_dict(cls.bybit_info_url.get(instType))
        d = []
        for url in links:
            data = cls.simple_request(url).get("result").get("list")
            symbols = [d["symbol"] for d in data]
            if instType == "future":
                symbols = [d for d in symbols if "-" in d]
            if instType == "perpetual":
                symbols = [d for d in symbols if "-" not in d]
            d.append(symbols)
        return unnest_list(d)

    @classmethod
    def bybit_symbols(cls) -> dict:
        """
            spot, perpetual, future, option
        """
        di = {

        }
        for isntType in cls.bybit_info_url.keys():
            data = cls.bybit_symbols_by_instType(isntType)
            di[isntType] = data
        return di
    
    @classmethod
    def bybit_info(cls, instType):
        """
            ex: perpetual.LinearPerpetual
        """
        url = recursive_dict_access(cls.bybit_info_url, instType)
        info = cls.simple_request(url)
        return info.get("result").get("list")
    
    @classmethod
    async def bybit_symbols_by_instType_async(cls, instType):
        """ 
            spot, perpetual
        """
        links = iterate_dict(cls.bybit_info_url.get(instType))
        d = []
        for url in links:
            data = await cls.simple_request_async(url)
            data = data.get("result").get("list")
            symbols = [d["symbol"] for d in data]
            if instType == "future":
                symbols = [d for d in symbols if "-" in d]
            if instType == "perpetual":
                symbols = [d for d in symbols if "-" not in d]
            d.append(symbols)
        return unnest_list(d)

    @classmethod
    async def bybit_symbols_async(cls) -> dict:
        """
            spot, perpetual, future, option
        """
        di = {

        }
        for isntType in cls.bybit_info_url.keys():
            data = await cls.bybit_symbols_by_instType_async(isntType)
            di[isntType] = data
        return di
    
    @classmethod
    async def bybit_info_async(cls, instType):
        """
            ex: perpetual.LinearPerpetual
        """
        url = recursive_dict_access(cls.bybit_info_url, instType)
        info = await cls.simple_request_async(url)
        return info.get("result").get("list")
    
class binanceInfo(requestHandler):
    binance_info_url = {
                        "spot" : "https://api.binance.com/api/v3/exchangeInfo",
                        "perpetual" : {
                            "LinearPerpetual" : "https://fapi.binance.com/fapi/v1/exchangeInfo",
                            "InversePerpetual" : "https://dapi.binance.com/dapi/v1/exchangeInfo"
                        },
                        "future" : {
                            "LinearFuture" : "https://fapi.binance.com/fapi/v1/exchangeInfo",
                            "InverseFuture" : "https://dapi.binance.com/dapi/v1/exchangeInfo"
                        },
                        "option" : "https://eapi.binance.com/eapi/v1/exchangeInfo"
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

    binance_future_types = ['CURRENT_QUARTER', 'NEXT_QUARTER']
    binance_perpetual_types = ["PERPETUAL"]
    
    @classmethod
    def binance_symbols_by_instType(cls, instType):
        """ 
            spot, perpetual, future, option
        """
        links = iterate_dict(cls.binance_info_url.get(instType))
        d = []
        for url in links:
            try:
                data = cls.simple_request(url).get("symbols")
                symbols = [d["symbol"] for d in data]
                d.append(symbols)
            except:
                data = cls.simple_request(url)
                symbols = [d["symbol"] for d in data["optionSymbols"]]
                d.append(symbols)
        d = unnest_list(d)
        if instType == "future":
            d = [symbol for symbol in d if re.search(r'_[0-9]+', symbol)]
        if instType == "perpetual":
            d = [symbol for symbol in d if not re.search(r'_[0-9]+', symbol)]
        return d
    
    @classmethod
    def binance_symbols(cls) -> dict:
        """
            spot, perpetual, future, option
        """
        di = {}
        for isntType in cls.binance_info_url.keys():
            data = cls.binance_symbols_by_instType(isntType)
            di[isntType] = data
        return di
    
    @classmethod
    def binance_info(cls, instType):
        """
            ex: perpetual.LinearPerpetual
        """
        url = recursive_dict_access(cls.binance_info_url, instType)
        info = cls.simple_request(url)
        if instType != "option":
            return info.get("symbols")
        else:
            return info


    @classmethod
    async def binance_get_inverse_instruments_by_underlying(cls, underlying_asset):
        symbols = []
        data = await cls.binance_info_async("perpetual.InversePerpetual")
        for prefix, event, value in ijson.parse(data):
            if prefix == 'symbols.item.symbol' and underlying_asset in value:
                symbols.append(value)
        return symbols

    @classmethod
    async def binance_get_linear_instruments_by_underlying(cls, underlying_asset):
        symbols = []
        data = await cls.binance_info_async("perpetual.LinearPerpetual")
        for prefix, event, value in ijson.parse(data):
            if prefix == 'symbols.item.symbol' and underlying_asset in value:
                symbols.append(value)
        return symbols
    
    @classmethod
    async def binance_info_async(cls, instType):
        """
            ex: perpetual.LinearPerpetual
        """
        url = recursive_dict_access(cls.binance_info_url, instType)
        info = await cls.simple_request_async(url)
        return info


class okxInfo(requestHandler):

    okx_info_url = {  
        "spot" : "https://www.okx.com/api/v5/public/instruments?instType=SPOT",
        "perpetual" : "https://www.okx.com/api/v5/public/instruments?instType=SWAP",
        "future" : "https://www.okx.com/api/v5/public/instruments?instType=FUTURES",
        "option" : "https://www.okx.com/api/v5/public/instruments?instType=OPTION",
    }
    @classmethod
    def okx_symbols_by_instType(cls, isntType, instFamily="BTC-USD"):
        """ 
            spot, perpetual, future, option
            &instFamily=BTC-USD
        """
        urls = cls.okx_info_url.get(isntType) if isntType != "option" else f"{cls.okx_info_url.get(isntType)}&instFamily={instFamily}"
        data = cls.simple_request(urls).get("data")
        symbols = [d["instId"] for d in data]
        return symbols
    
    @classmethod
    def okx_symbols(cls) -> dict:
        """
            spot, perpetual, future, option
        """
        di = {

        }
        for isntType in cls.okx_info_url.keys():
            data = cls.okx_symbols_by_instType(isntType)
            di[isntType] = data
        return di

    @classmethod
    def okx_info(cls, instType):
        """
            ex: spot, perpetual, option, future
        """
        info = cls.simple_request(cls.okx_info_url.get(instType))
        return info.get("data")

    @classmethod
    async def okx_symbols_by_instType_async(cls, isntType, instFamily="BTC-USD"):
        """ 
            spot, perpetual, future, option
            &instFamily=BTC-USD
        """
        urls = cls.okx_info_url.get(isntType) if isntType != "option" else f"{cls.okx_info_url.get(isntType)}&instFamily={instFamily}"
        data = await cls.simple_request_async(urls)
        data = data.get("data")
        symbols = [d["instId"] for d in data]
        return symbols
    
    @classmethod
    async def okx_symbols_async(cls) -> dict:
        """
            spot, perpetual, future, option
        """
        di = {

        }
        for isntType in cls.okx_info_url.keys():
            data = await cls.okx_symbols_by_instType_async(isntType)
            di[isntType] = data
        return di

    @classmethod
    async def okx_info_async(cls, instType):
        """
            ex: spot, perpetual, option, future
        """
        rd = cls.okx_info_url.get(instType)
        info = await cls.simple_request_async(rd)
        return info.get("data")

class kucoinInfo(requestHandler):
    kucoin_endpoints = {  
        "spot" : "https://api.kucoin.com",   
        "perpetual" : "https://api-futures.kucoin.com",  
    }
    kucoin_basepoints = {  
        "spot" : "/api/v2/symbols",    
        "perpetual" : "/api/v1/contracts/active",  
    }
    kucoin_params = {}
    kucoin_call_example = {
                "spot" : "BTC-USDT",
                "perpetual" : "XBTUSDTM"
            }

    @classmethod
    def kucoin_symbols_by_instType(cls, isntType):
        """ 
            spot, perpetual, future, option
        """
        endpoint = cls.kucoin_endpoints.get(isntType)
        basepoint = cls.kucoin_basepoints.get(isntType)
        url = endpoint + basepoint
        r = cls.simple_request(url)
        data = r.get("data")
        symbols = [d["symbol"] for d in data]
        return symbols
    
    @classmethod
    def kucoin_symbols(cls) -> dict:
        """
            spot, perpetual
        """
        di = {}
        for isntType in cls.kucoin_call_example.keys():
            data = cls.kucoin_symbols_by_instType(isntType)
            di[isntType] = data
        return di

    @classmethod
    def kucoin_info(cls, instType):
        """
            ex: spot, perpetual
        """
        endpoint = cls.kucoin_endpoints.get(instType)
        basepoint = cls.kucoin_basepoints.get(instType)
        url = endpoint + basepoint
        info = cls.simple_request(url)
        return info.get("data")

    @classmethod
    async def kucoin_symbols_by_instType_async(cls, isntType):
        """ 
            spot, perpetual, future, option
        """
        endpoint = cls.kucoin_endpoints.get(isntType)
        basepoint = cls.kucoin_basepoints.get(isntType)
        url = endpoint + basepoint
        r = await cls.simple_request_async(url)
        data = r.get("data")
        symbols = [d["symbol"] for d in data]
        return symbols
    
    @classmethod
    async def kucoin_symbols_async(cls) -> dict:
        """
            spot, perpetual
        """
        di = {}
        for isntType in cls.kucoin_call_example.keys():
            data = await cls.kucoin_symbols_by_instType_async(isntType)
            di[isntType] = data
        return di

    @classmethod
    async def kucoin_info_async(cls, instType):
        """
            ex: spot, perpetual
        """
        endpoint = cls.kucoin_endpoints.get(instType)
        basepoint = cls.kucoin_basepoints.get(instType)
        url = endpoint + basepoint
        info = await cls.simple_request_async(url)
        return info.get("data")
   
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
                    "InversePerpetual" : 'BTCUSD',
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
    def bitget_info(cls, instType):
        """
            Check the bitget_info_url
            Ex:
            instType = "perpetual.LinearPerpetual.usdt
        """
        keys = instType.split(".")
        link = recursive_dict_access(cls.bitget_info_url, keys)
        return cls.simple_request(link).get("data")

    @classmethod
    async def bitget_symbols_by_instType_async(cls, instType):
        """ 
            spot, perpetual
        """
        links = iterate_dict(cls.bitget_info_url.get(instType))
        d = []
        for url in links:
            data = await cls.simple_request_async(url)
            data = data.get("data")
            symbols = [d["symbol"] for d in data]
            d.append(symbols)
        return unnest_list(d)
    
    @classmethod
    async def bitget_symbols_async(cls) -> dict:
        """
            spot, perpetual, future, option
        """
        di = {
        }
        for isntType in cls.bitget_info_url.keys():
            data = await cls.bitget_symbols_by_instType_async(isntType)
            di[isntType] = data
        return di
    
    @classmethod
    async def bitget_info_async(cls, instType):
        """
            Check the bitget_info_url
            Ex:
            instType = "perpetual.LinearPerpetual.usdt
        """
        keys = instType.split(".")
        link = recursive_dict_access(cls.bitget_info_url, keys)
        data = await cls.simple_request_async(link)
        return data.get("data")

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
    def bingx_info(cls, instType):
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
    def mexc_info(cls, instType):
        """
            "spot" "perp"
        """
        data = cls.simple_request(cls.mexc_urls.get(instType))
        try:
            data = data["symbols"]
        except:
            data = data["data"]
        return data

    @classmethod
    async def mexc_symbols_by_instType_async(cls, instType):
        """ 
            spot, perpetua
        """
        rurl = cls.mexc_urls.get(instType)
        symbols = await cls.simple_request_async(rurl)
        try:
            symbols = symbols["symbols"]
        except:
            symbols = symbols["data"]
        return [s["symbol"] for s in symbols]
    
    @classmethod
    async def mexc_symbols_async(cls) -> dict:
        """
            spot, perpetual, future, option
        """
        di = {}
        for isntType in cls.mexc_urls.keys():
            data = await cls.mexc_symbols_by_instType_async(isntType)
            di[isntType] = data
        return di
    
    @classmethod
    async def mexc_info_async(cls, instType):
        """
            "spot" "perp"
        """
        rurl = cls.mexc_urls.get(instType)
        data = await cls.simple_request_async(rurl)
        try:
            data = data["symbols"]
        except:
            data = data["data"]
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
    def deribit_info(cls, instType):
        """
            kind : spot, future, option
            currency : ["BTC", "ETH", "USDC", "USDT", "EURR"]
            so instType = spot.BTC, or option.ETH  .....

        """
        cls.params["kind"], cls.params["currency"] = instType.split(".")
        data = cls.request_full(url=cls.url, headers=cls.headers, params=cls.params).get("result")
        return data

    @classmethod
    async def deribit_symbols_by_instType_async(cls, instType):
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
            data = await cls.request_full_async(url=cls.url, headers=cls.headers, params=cls.params)
            data = data.get("result")
            symbols = [s["instrument_name"] for s in data]
            allsymbols.append(symbols)
        allsymbols = unnest_list(allsymbols)
        if instType == "perpetual":
            allsymbols = [x for x in allsymbols if "PERPETUAL" in x]
        if instType == "future":
            allsymbols = [x for x in allsymbols if "PERPETUAL" not in x]
        return allsymbols

    
    @classmethod
    async def deribit_symbols_async(cls) -> dict:
        """
            spot, perpetual, future, option
        """
        di = {}
        for isntType in ["spot", "perpetual", "future", "option"]:
            data = await cls.deribit_symbols_by_instType_async(isntType)
            di[isntType] = data
        return di
    
    @classmethod
    async def deribit_info_async(cls, instType):
        """
            kind : spot, future, option
            currency : ["BTC", "ETH", "USDC", "USDT", "EURR"]
            so instType = spot.BTC, or option.ETH  .....

        """
        cls.params["kind"], cls.params["currency"] = instType.split(".")
        data = await cls.request_full_async(url=cls.url, headers=cls.headers, params=cls.params)
        data = data.get("result")
        return data

class coinbaseInfo(requestHandler):
    
    def __init__(self, api, secret):
        self.coinbase_api = api
        self.coinbase_secret = secret
        self.coinbase_payload = ''
        self.coinbase_endpoint = "api.coinbase.com"
        self.coinbase_basepoints = {
        "spot" : "/api/v3/brokerage/products?product_type=SPOT",
        "future" : "/api/v3/brokerage/products?product_type=FUTURE"
                            }

    def coinbase_symbols_by_instType(self, instType):
        """
            spot, future
        """
        info = self.coinbase_info(instType)
        prdocut_ids = list(set([x["display_name"] for x in info]))
        return prdocut_ids

    def coinbase_productids_by_instType(self, instType):
        """
            future
        """
        info = self.coinbase_info(instType)
        return {x:y for x, y in zip([x["display_name"] for x in info], [x["product_id"] for x in info])}

    def coinbase_symbols(self):
        """
            spot, future
        """
        d= {}
        for key in self.coinbase_basepoints:
            symbols = self.coinbase_symbols_by_instType(key)
            d[key] = symbols
        return d

    def coinbase_info(self, instType):
        """
            spot, future
        """
        headers = self.build_headers()
        return self.http_call(self.coinbase_endpoint, self.coinbase_basepoints.get(instType), self.coinbase_payload, headers).get("products")
    


    def build_headers(self):
        key_name       =  self.coinbase_api
        key_secret     =  self.coinbase_secret
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
    htx_endpoints = {
        "spot" : "https://api.huobi.pro",
        "perpetual" : {
            "LinearPerpetual" : "https://api.hbdm.com",
            "InversePerpetual" : "https://api.hbdm.com"
        },
        "future" : {
            "InverseFuture" : "https://api.hbdm.com",
        }

    }
    htx_basepoints = {
        "spot" : "/v1/settings/common/market-symbols",
        "perpetual" : {
            "LinearPerpetual" : "/linear-swap-api/v1/swap_contract_info",
            "InversePerpetual" : "/swap-api/v1/swap_contract_info"

        },
        "future" : {
            "InverseFuture" : "/api/v1/contract_contract_info",
        }
    }
    htx_call_example = {
        "spot" : "btcusdt",
        "perpetual" : "LTC-USD, LTC-USDT",
        "future" : "TRX240329" # Which is bitcoin
        }
    
    @classmethod
    def htx_symbols_by_instType(cls, instType):
        """
            spot, future
        """
        basepoint = iterate_dict(cls.htx_endpoints.get(instType))
        endpoint = iterate_dict(cls.htx_basepoints.get(instType))
        links = [f"{y}{x}" for x, y in zip(endpoint, basepoint)]
        d = []
        for url in links:
            data = cls.simple_request(url).get("data")
            try:
                symbols = [d["contract_code"] for d in data]
            except:
                symbols = [d["symbol"] for d in data]
            d.append(symbols)
        return unnest_list(d)
    
    @classmethod
    def htx_symbols(cls):
        """
            spot, future
        """
        d= {}
        for key in cls.htx_endpoints:
            symbols = cls.htx_symbols_by_instType(key)
            d[key] = symbols
        return d
    
    @classmethod
    def htx_info(cls, instType):
        """
            perpetual.LinearPerpetual, ....
        """
        endpoint = recursive_dict_access(cls.htx_endpoints, instType)
        basepoint = recursive_dict_access(cls.htx_basepoints, instType)
        url = f"{endpoint}{basepoint}"
        return cls.simple_request(url).get("data")

    @classmethod
    async def htx_symbols_by_instType_async(cls, instType):
        """
            spot, future
        """
        basepoint = iterate_dict(cls.htx_endpoints.get(instType))
        endpoint = iterate_dict(cls.htx_basepoints.get(instType))
        links = [f"{y}{x}" for x, y in zip(endpoint, basepoint)]
        d = []
        for url in links:
            data = await cls.simple_request_async(url)
            data = data.get("data")
            try:
                symbols = [d["contract_code"] for d in data]
            except:
                symbols = [d["symbol"] for d in data]
            d.append(symbols)
        return unnest_list(d)
    
    @classmethod
    async def htx_symbols_async(cls):
        """
            spot, future
        """
        d= {}
        for key in cls.htx_endpoints:
            symbols = await cls.htx_symbols_by_instType_async(key)
            d[key] = symbols
        return d
    
    @classmethod
    async def htx_info_async(cls, instType):
        """
            perpetual.LinearPerpetual, ....
        """
        endpoint = recursive_dict_access(cls.htx_endpoints, instType)
        basepoint = recursive_dict_access(cls.htx_basepoints, instType)
        url = f"{endpoint}{basepoint}"
        data = await cls.simple_request_async(url)
        data = data.get("data")
        return data

class gateioInfo(requestHandler):
    gateio_endpointtt = "https://api.gateio.ws"
    gateio_headerssss = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    gateio_basepointsss = {
        "spot" : "/api/v4/spot/currency_pairs",
        "perpetual" : {
            "LinearPerpetual" : "/api/v4/futures/usdt/contracts",
            "InversePerpetual" : "/api/v4/futures/btc/contracts",
        },
        "future" : "/api/v4/delivery/usdt/contracts",
        "option" : "/api/v4/options/contracts", 
    }

    @classmethod
    def gateio_symbols_by_instType(cls, instType):
        """
            spot, future, perpetual, option
        """
        if instType in ["spot", "future"]:
            info = cls.gateio_info(instType)
            key = "id" if instType=="spot" else "name"
            prdocut_ids = list(set([x[key] for x in info]))
            return prdocut_ids
        if instType == "perpetual":
            links = iterate_dict(cls.gateio_basepointsss.get(instType))
            d = []
            for basepoint in links:
                data = cls.request_full(cls.gateio_endpointtt+basepoint, headers=cls.gateio_headerssss, params={})
                prdocut_ids = list(set([x["name"] for x in data]))
                d.append(prdocut_ids)
            return unnest_list(d)
        if instType == "option":
            underlyings = cls.gateio_option_underlying_assets()
            d = []
            for underlying in underlyings:
                data = cls.request_full(cls.gateio_endpointtt+cls.gateio_basepointsss.get("option"), headers=cls.gateio_headerssss, params={"underlying" : underlying})
                d.append(list(set([x["name"] for x in data])))
            return unnest_list(d) 


    @classmethod
    def gateio_symbols(cls):
        """
            spot, option, perpetual, future
        """
        d= {}
        for key in cls.gateio_basepointsss:
            symbols = cls.gateio_symbols_by_instType(key)
            d[key] = symbols
        return d

    @classmethod
    def gateio_option_underlying_assets(cls):
         data = cls.request_full(url=f"{cls.gateio_endpointtt}/api/v4/options/underlyings", headers=cls.gateio_headerssss, params={})
         return [x["name"] for x in data]
    
    @classmethod
    def gateio_info(cls, instType):
        """
            ex. perpetual.LinearPerpetual
        """
        if instType != "option":
            basepoint = recursive_dict_access(cls.gateio_basepointsss, instType)
            url = f"{cls.gateio_endpointtt}{basepoint}"
            info = cls.simple_request(url)
            return info
        else:
            underlyings = cls.gateio_option_underlying_assets()
            d = []
            for underlying in underlyings:
                data = cls.request_full(cls.gateio_endpointtt+cls.gateio_basepointsss.get("option"), headers=cls.gateio_headerssss, params={"underlying" : underlying})
                d.append(data)
            return unnest_list(d) 


    @classmethod
    async def gateio_symbols_by_instType_async(cls, instType):
        """
            spot, future, perpetual, option
        """
        if instType in ["spot", "future"]:
            info = await cls.gateio_info_async(instType)
            key = "id" if instType=="spot" else "name"
            prdocut_ids = list(set([x[key] for x in info]))
            return prdocut_ids
        if instType == "perpetual":
            links = iterate_dict(cls.gateio_basepointsss.get(instType))
            d = []
            for basepoint in links:
                data = await cls.request_full_async(cls.gateio_endpointtt+basepoint, headers=cls.gateio_headerssss, params={})
                prdocut_ids = list(set([x["name"] for x in data]))
                d.append(prdocut_ids)
            return unnest_list(d)
        if instType == "option":
            underlyings = await cls.gateio_option_underlying_assets_async()
            d = []
            for underlying in underlyings:
                data = await cls.request_full_async(cls.gateio_endpointtt+cls.gateio_basepointsss.get("option"), headers=cls.gateio_headerssss, params={"underlying" : underlying})
                d.append(list(set([x["name"] for x in data])))
            return unnest_list(d) 


    @classmethod
    async def gateio_symbols_async(cls):
        """
            spot, option, perpetual, future
        """
        d= {}
        for key in cls.gateio_basepointsss:
            symbols = await cls.gateio_symbols_by_instType_async(key)
            d[key] = symbols
        return d

    @classmethod
    async def gateio_option_underlying_assets_async(cls):
         data = await cls.request_full_async(url=f"{cls.gateio_endpointtt}/api/v4/options/underlyings", headers=cls.gateio_headerssss, params={})
         return [x["name"] for x in data]
    
    @classmethod
    async def gateio_info_async(cls, instType):
        """
            ex. perpetual.LinearPerpetual
        """
        if instType != "option":
            basepoint = recursive_dict_access(cls.gateio_basepointsss, instType)
            url = f"{cls.gateio_endpointtt}{basepoint}"
            info = await cls.simple_request_async(url)
            return info
        else:
            underlyings = cls.gateio_option_underlying_assets()
            d = []
            for underlying in underlyings:
                data = await cls.request_full_async(cls.gateio_endpointtt+cls.gateio_basepointsss.get("option"), headers=cls.gateio_headerssss, params={"underlying" : underlying})
                d.append(data)
            return unnest_list(d) 
        