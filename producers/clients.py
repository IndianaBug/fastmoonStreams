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
from utilis import generate_random_integer, generate_random_id, unnest_list
from functools import partial
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

from exchangeinfo import binanceInfo, gateioInfo
from producers.clientpoints.binance import *
from producers.clientpoints.bybit import *
from producers.clientpoints.okx import *
from producers.clientpoints.coinbase import *
from producers.clientpoints.deribit import *
from producers.clientpoints.kucoin import *
from producers.clientpoints.htx import *
from producers.clientpoints.bitget import *
from producers.clientpoints.gateio import *
from producers.clientpoints.mexc import *
from producers.clientpoints.bingx import *

# TODO
# Fix the orders of the wscall for both binance and Bybit xD
# Add get all available ws methods and api methods per exchange
# add deribitcoinbase heartbeats

class CommunicationsManager:

    @classmethod
    def make_request(cls, connection_data : dict):
        if "maximum_retries"  not in connection_data:
            raise ValueError("maximum_retries are not in connection data")
        for index, _ in enumerate(range(connection_data.get("maximum_retries"))):
            response = requests.get(connection_data.get("url"), params=connection_data.get("params"), headers=connection_data.get("headers"))
            if response.status_code == 200:
                return response.json() 
            try:
                if response.get('code', None) in connection_data.get("repeat_code"):
                    connection_data["params"]["limit"] = connection_data["params"]["limit"] - connection_data.get("books_decrement")
                    time.sleep(1)
                if index == len(connection_data.get("maximum_retries")):
                    print(response.status_code)
            except:
                pass
    
    @classmethod
    def make_request_v2(cls, connection_data:dict):
        url = connection_data.get("url")
        headers = connection_data.get("headers")
        payload = connection_data.get("payload")
        response = requests.request("GET", url, headers=headers, data=payload)
        return response.json() 

    @classmethod
    def make_httpRequest(cls, connection_data):
        conn = http.client.HTTPSConnection(connection_data.get("endpoint"))
        basepoint = "?".join([connection_data.get("basepoint"), urllib.parse.urlencode(connection_data.get("params"))])
        conn.request(
            "GET", 
            basepoint, 
            connection_data.get("payload"), 
            connection_data.get("headers"),
            )
        res = conn.getresponse()
        response = json.loads(res.read())
        return response
        
    @classmethod
    async def make_aiohttpRequest(cls, connection_data):
        async with aiohttp.ClientSession() as session:
            async with session.get(connection_data["url"], headers=connection_data["headers"], params=connection_data["params"]) as response:
                response =  await response.text()
                return response
            
    @classmethod
    async def make_aiohttpRequest_v2(cls, connection_data):
        connection_data["headers"] = {str(key): str(value) for key, value in connection_data["headers"].items()}
        async with aiohttp.ClientSession() as session:
            async with session.get(connection_data["url"], headers=connection_data["headers"], params=connection_data["params"]) as response:
                response =  await response.text()
                return response

    @classmethod
    def make_wsRequest_http(cls, connection_data):
        print(connection_data.get("headers"))
        async def wsClient(connection_data):
            async with websockets.connect(connection_data.get("endpoint"),  ssl=ssl_context) as websocket:
                await websocket.send(json.dumps(connection_data.get("headers")))
                response = await websocket.recv()
                return response
        loop = asyncio.get_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(wsClient(connection_data))
        finally:
            loop.close()
        return response

    async def make_wsRequest(connection_data):
        async with websockets.connect(connection_data.get("endpoint"),  ssl=ssl_context) as websocket:
            await websocket.send(json.dumps(connection_data.get("headers")))
            response = await websocket.recv()
            return response 

class binance(CommunicationsManager, binanceInfo):
    """
        Abstraction for binance API calls for depth, funding, oi, tta, ttp and gta
    """
    binance_repeat_response_codes = binance_repeat_response_codes
    binance_api_endpoints = binance_api_endpoints
    binance_api_basepoints = binance_api_basepoints
    binance_api_params_map = binance_api_params_map
    binance_ws_endpoints = binance_ws_endpoints
    binance_future_contract_types = binance_future_contract_types
    binance_ws_payload_map = binance_ws_payload_map
    

    def __init__(self):
        pass

    @classmethod
    def binance_buildRequest(cls, instType:str, objective:str, symbol:str, specialParam=None, special_method=None, 
                             maximum_retries:int=10, books_dercemet:int=500, **kwargs)->dict: 
        """
            insType : spot, perpetual, future, option, oisum
            objective : depth, funding, oi, tta, ttp, gta
            maximum_retries : if the request was unsuccessufl because of the length
            books_decremet : length of the books to decrease for the next request
            special_method : oioption, oifutureperp, posfutureperp, fundfutureperp
        """ 
        symbol_name = binance_get_symbol_name(symbol)
        marginType = binance_get_marginType(instType, symbol)
        params =  binance_api_params_map.get(instType).get(marginType).get(objective)(symbol) if marginType != None else binance_api_params_map.get(instType).get(objective)(symbol)
        endpoint = binance_api_endpoints.get(instType).get(marginType) if marginType != None else binance_api_endpoints.get(instType)
        basepoint = binance_api_basepoints.get(instType).get(marginType).get(objective) if marginType != None else binance_api_basepoints.get(instType).get(objective)
        url = f"{endpoint}{basepoint}"
        headers = {}
        payload = ""
        if specialParam is not None:
            params["expiration"] = specialParam
        return {
            "url" : url, 
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrument" : symbol_name, 
            "insType" : instType, 
            "exchange" : "binance", 
            "repeat_code" : cls.binance_repeat_response_codes,
            "maximum_retries" : maximum_retries, 
            "books_dercemet" : books_dercemet,
            "marginType" : marginType,
            "payload" : payload,
            "special_method" : special_method
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
    def binance_get_option_expiries(cls, symbol):
        """
            Looks for unexpired onption
        """
        data = cls.binance_info("option").get("optionSymbols")
        symbols = [x["symbol"] for x in data if symbol.upper() in x["symbol"].upper() and  datetime.fromtimestamp(int(x["expiryDate"]) / 1000) > datetime.now()]
        expirations = list(set([x.split("-")[1] for x in symbols]))
        return expirations

    @classmethod
    def binance_perpfut_instruments(cls, underlying_instrument):
        all_info = []
        for instType in ["perpetual.LinearPerpetual", "perpetual.InversePerpetual"]:
            symbols = binance.binance_info(instType)
            all_info.append([x.get("symbol") for x in symbols if underlying_instrument in x.get("symbol") and "USD" in  x.get("symbol")])
        all_info = unnest_list(all_info)
        return all_info 

    @classmethod
    async def binance_build_oifutureperp_method(cls, underlying_asset):
        """
            BTC, ETH ...
        """
        symbols =  cls.binance_perpfut_instruments(underlying_asset)
        full = []
        for symbol in symbols:
            instType = "future" if bool(re.search(r'\d', symbol.split("_")[-1])) else "perpetual"
            data = await cls.binance_aiohttpFetch(instType, "oi", symbol=symbol, special_method="oifutureperp")
            full.append(data)
        return full
    
    @classmethod
    async def binance_build_fundfutureperp_method(cls, underlying_asset):
        """
            BTC, ETH ...
        """
        symbols =  cls.binance_perpfut_instruments(underlying_asset)
        full = []
        for symbol in symbols:
            instType = "future" if bool(re.search(r'\d', symbol.split("_")[-1])) else "perpetual"
            if not bool(re.search(r'\d', symbol.split("_")[-1])):
                data = await cls.binance_aiohttpFetch(instType, "funding", symbol=symbol, special_method="fundfutureperp")
                full.append(data)
        return full

    @classmethod
    async def binance_build_posfutureperp_method(cls, underlying_instrument, latency=1):
        """
            BTC, ETH ...
            latency : seconds to wait before api call
        """
        symbols = binance.binance_info("perpetual.LinearPerpetual")
        symbols = [x.get("symbol") for x in symbols if underlying_instrument in x.get("symbol") and "USD" in  x.get("symbol")]
        full = {}
        for symbol in symbols:
            instType = "future" if bool(re.search(r'\d', symbol.split("_")[-1])) else "perpetual"
            for objective in ["tta", "ttp", "gta"]:
                marginType = binance_instType_help(symbol)
                symbol = symbol if marginType == "Linear" else symbol.replace("_", "").replace("PERP", "")
                data = await cls.binance_aiohttpFetch(instType, objective, symbol=symbol, special_method="posfutureperp")
                full[f"{symbol}_{objective}"] = data
                time.sleep(latency)
        coinm_symbol = underlying_instrument+"USD"
        data = await cls.binance_aiohttpFetch(instType, objective, symbol=coinm_symbol, special_method="posfutureperp")
        full[coinm_symbol+"coinmAgg"] = data
        return full

    @classmethod
    async def binance_build_oioption_method(cls, symbol):
        """
            BTC, ETH ...
        """
        expiries =  cls.binance_get_option_expiries(symbol)
        full = []
        for expiration in expiries:
            data = await cls.binance_aiohttpFetch("option", "oi", symbol=symbol, specialParam=expiration,  special_method="oioption")
            full.append(data)
        return unnest_list(full)

    @classmethod
    def binance_build_api_connectionData(cls, insType:str, objective:str, symbol:str,  pullTimeout:int, special_method=None, specialParam=None, **kwargs):
        """
            insType : deptj, funding, oi, tta, ttp, gta
            **kwargs, symbol limit, period. Order doesnt matter
            result = d['aiohttpMethod'](**kwargs)
            pullTimeout : how many seconds to wait before you make another call
        """
        call = partial(cls.binance_aiohttpFetch, insType=insType, objective=objective, symbol=symbol)
        if special_method == "oioption":
            call = partial(cls.binance_build_oioption_method, symbol)
        if special_method == "oifutureperp":
            call = partial(cls.binance_build_oifutureperp_method, symbol)
        if special_method == "posfutureperp":
            call = partial(cls.binance_build_posfutureperp_method, symbol)
        connectionData = cls.binance_buildRequest(insType, objective, symbol, specialParam, special_method, **kwargs)
        data =  {
                "type" : "api",
                "id_ws" : f"binance_api_{insType}_{objective}_{connectionData.get('instrument')}",
                "exchange":"binance", 
                "instrument": connectionData.get("instrument"),
                "instType": insType,
                "objective": objective, 
                "pullTimeout" : pullTimeout,
                "apicallData" : connectionData,
                "aiohttpMethod" : call, 
                "marginType" : connectionData.get("marginType"),
                "is_special" : special_method,
                }
        
        return data
    
    @classmethod
    def binance_build_ws_message(cls, insType, objective, symbol):
        payload = binance_ws_payload_map.get(insType).get(objective)(symbol)
        message = {
            "method": "SUBSCRIBE", 
            "params": [payload], 
            "id": generate_random_integer(10)
        }
        return message

    @classmethod
    def binance_build_ws_perpfutureTrade(cls, instType, underlyingInstrument):
        symbols = cls.binance_perpfut_instruments(underlyingInstrument)
        message = {
            "method": "SUBSCRIBE", 
            "params": [], 
            "id": generate_random_integer(10)
        }
        for symbol in symbols:
            if "DOMU" not in symbol:
                trueInstType, marginType = binance_get_futperphelp(symbol)
                if instType in marginType:
                    m = cls.binance_build_ws_message(trueInstType, "trades", symbol)
                    message["params"].append(m.get("params")[0])
        return message
    
    @classmethod
    def binance_build_ws_connectionData(cls, instType:str, objective:str, symbol:str, needSnap=False, snaplimit=999,  special=None, **kwargs):
        """
            instType : spot, future, perpetual, option
                        Linear, Inverse for special methods
            needSnap and snap limit: you need to fetch the full order book, use these
            Example of snaping complete books snapshot : connectionData.get("sbmethod")(dic.get("instType"), connectionData.get("objective"), **connectionData.get("sbPar"))
            special streams : perpfutureTrade
        """        
        symbol_name = binance_get_symbol_name(symbol)
        marginType = binance_get_marginType(instType, symbol)
        endpoint = binance_ws_endpoints.get(instType).get(marginType) if marginType != None else binance_ws_endpoints.get(instType)

        if special == None:
            message = cls.binance_build_ws_message(instType, objective, symbol)
            url = "" 
        if special == "perpfutureTrade":
            message = cls.binance_build_ws_perpfutureTrade(instType, symbol) 

            
        connection_data =     {
                                "type" : "ws",
                                "id_ws" : f"binance_ws_{instType}_{objective}_{symbol_name}",
                                "exchange":"binance", 
                                "instrument": symbol_name,
                                "instType": instType,
                                "objective":objective, 
                                "updateSpeed" : None,
                                "url" : endpoint,
                                "msg" : message,
                                "1stBooksSnapMethod" : None,
                                "marginType" : marginType
                            }
        
        if needSnap is True:
            connection_data["id_api"] = f"binance_api_{instType}_{objective}_{symbol_name}",
            connection_data["1stBooksSnapMethod"] = partial(cls.binance_fetch, instType, objective, symbol)
        return connection_data

class bybit(CommunicationsManager):
    # bybit_api_endpoint = bybit_api_endpoint
    # bybit_api_basepoints = bybit_api_basepoint
    # bybit_ws_endpoints = bybit_ws_endpoints
    # bybit_stream_keys = bybit_stream_keys
    # bybit_repeat_response_code = -1130
    # bybit_api_category_map = bybit_api_category_map

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
            "books_dercemet" : books_dercemet,
            "marginType" : marginCoin
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
        message, insType, standart_objective_name = cls.bybit_build_ws_method(insType, **params)
        # Find marginType
        marginType=""
        if insType == "perpetual":
            marginType = "LinearPerpetual" if "USDT" in  params["symbol"].upper() else "InversePerpetual"
        if insType == "future":
            marginType = "LinearFuture" if "USDT" not in  params["symbol"].upper() else "InverseFuture"
        
        try:
            endpoint = cls.bybit_ws_endpoints.get(insType).get(marginType)
        except:
            endpoint = cls.bybit_ws_endpoints.get(insType)

        
        connection_data =     {
                                "type" : "ws",
                                "id_ws" : f"bybit_ws_{insType}_{standart_objective_name}_{params['symbol'].lower()}",
                                "exchange":"bybit", 
                                "instrument": params['symbol'].lower(),
                                "instType": insType,
                                "objective":standart_objective_name, 
                                "updateSpeed" : None,
                                "url" : endpoint,
                                "msg" : message,
                                "sbmethod" : None
                            }
        
        if needSnap is True:
            connection_data["id_api"] = f"bybit_api_{insType}_{standart_objective_name}_{params['symbol'].lower()}",
            connection_data["sbmethod"] = cls.bybit_fetch 
            if "symbol" in params:
                connection_data["sbPar"] = {
                    "symbol": params['symbol'].upper(), 
                    "limit" : int(snaplimit)
                }
            else:
                connection_data["sbPar"] = {
                    "baseCoin": params['baseCoin'].upper(), 
                    "limit" : int(snaplimit)
                }

        return connection_data
        
class okx(CommunicationsManager):
    """
        OKX apis and websockets wrapper
    """
    okx_repeat_response_code = okx_repeat_response_code
    okx_api_endpoint = okx_api_endpoint
    okx_api_instType_map = okx_api_instType_map
    okx_api_basepoints = okx_api_basepoints
    okx_ws_endpoint = okx_ws_endpoint
    okx_stream_keys = okx_stream_keys

    @classmethod
    def okx_buildRequest(cls, insType:str, objective:str, maximum_retries:int=10, books_dercemet:int=100, **kwargs)->dict: 
        """
            objective :  in the okx_api_basepoint
            # insType ---  the same as instType for previous modules. OKX contains arg instType threfore needs to be renamed
        """
        params = dict(**kwargs)
        symbol_name = okx_get_symbol_name(params)
        # endpoint
        endpoint = cls.okx_api_endpoint
        basepoint = cls.okx_api_basepoints.get(objective)
        url = endpoint + basepoint
        headers = {}
        # Margin Type / even htough unnecessary
        marginType = ""
        if insType!="spot":
            marginType = f"Linear{insType.capitalize()}" if "USDT" in symbol_name else f"Inverse{insType.capitalize()}"
        return {
            "url" : url, 
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrumentName" : symbol_name.lower(), 
            "insTypeName" : insType.lower(), 
            "exchange" : "okx", 
            "repeat_code" : cls.okx_repeat_response_code,
            "maximum_retries" : maximum_retries, 
            "books_dercemet" : books_dercemet,
            "marginType" : marginType,
            }

    @classmethod
    def okx_fetch(cls, *args, **kwargs):
        connection_data = cls.okx_buildRequest(*args, **kwargs)
        response = cls.make_request(connection_data)
        return response

    @classmethod
    async def okx_aiohttpFetch(cls, *args, **kwargs):
        connection_data = cls.okx_buildRequest(*args, **kwargs)
        response = await cls.make_aiohttpRequest(connection_data)
        return response
    
    @classmethod
    def okx_build_ws_method(cls, insType, **kwargs):
        """
            objective : depth, trades, liquidations, oi, funding
        """
        params = dict(kwargs)
        standart_objective_name = params["objective"]
        params["objective"] = cls.okx_stream_keys.get(params["objective"])
        message =  {
            "op": "subscribe", 
            "args": [{'channel': params.get("objective"), 'instId': params.get("symbol")}
            ]
            }

        return message, insType, standart_objective_name   

    @classmethod
    def okx_build_ws_connectionData(cls, insType, needSnap=False, snaplimit=1000, **kwargs):
        """
            You do not need to fetch ordeBook with okx websockets, it's done upon connection
            insType : perpetual, option, spot, future
        """
        params = dict(kwargs)
        message, insType, standart_objective_name = cls.okx_build_ws_method(insType, **params)
        symbol_name = okx_get_symbol_name(params)
        endpoint = okx_ws_endpoint    
        connection_data =     {
                                "type" : "ws",
                                "id_ws" : f"okx_ws_{insType}_{standart_objective_name}_{symbol_name}",
                                "exchange":"okx", 
                                "instrument": symbol_name,
                                "instType": insType,
                                "objective":standart_objective_name, 
                                "updateSpeed" : None,
                                "url" : endpoint,
                                "msg" : message,
                                "sbmethod" : None
                            }
        return connection_data

    @classmethod
    def okx_build_api_connectionData(cls, insType:str, objective:str, pullTimeout:int, **kwargs):
        """
            insType : perpetual, spot, future, option
            objective : oi, gta
            **kwargs - those in okx ducumentations
            pullTimeout : how many seconds to wait before you make another call
            How to call : result = d['aiohttpMethod'](**kwargs)
        """
        connectionData = cls.okx_buildRequest(insType, objective, **kwargs)
        params = dict(**kwargs)
        symbol_name = okx_get_symbol_name(params)
            
        data =  {
                "type" : "api",
                "id_ws" : f"okx_api_{insType}_{objective}_{symbol_name}",
                "exchange":"okx", 
                "instrument": symbol_name,
                "instType": insType,
                "objective": objective, 
                "pullTimeout" : pullTimeout,
                "connectionData" : connectionData,
                "aiohttpMethod" : partial(cls.okx_aiohttpFetch, insType=insType, objective=objective),
                "params" : dict(**kwargs)
                }
        
        return data

class coinbase(CommunicationsManager):
    """
        Abstraction of bybit api calls
    """

    def __init__ (self, api_coinbase, secret_coinbase):
        self.api_coinbase = api_coinbase
        self.secret_coinbase = secret_coinbase
        self.coinbase_repeat_response_code = coinbase_repeat_response_code
        self.coinbase_api_product_type_map = coinbase_api_product_type_map
        self.coinbase_api_endpoint = coinbase_api_endpoint
        self.coinbase_api_basepoints = coinbase_api_basepoints
        self.coinbase_ws_endpoint = coinbase_ws_endpoint
        self.coinbase_stream_keys = coinbase_stream_keys

    def coinbase_buildRequest(self, instType:str, objective:str, maximum_retries:int=10, books_dercemet:int=100, **kwargs)->dict: 
        """
            do not pass argument product_type
            omit maximum_retries and books_dercemet as coinbase handles it for you :)
            instType : spot, perpetual
        """
        params = dict(kwargs)
        symbol = coinbase_get_symbol_name(params)
        product_type = self.coinbase_api_product_type_map.get(instType)
        print(product_type)
        params["product_type"] = product_type
        endpoint = self.coinbase_api_endpoint
        basepoint = self.coinbase_api_basepoints.get(objective)
        url = endpoint+basepoint
        payload = ''
        headers = self.coinbase_build_headers(basepoint)
        print(basepoint)
        return {
            "url" : url,
            "endpoint" : endpoint, 
            "basepoint" : basepoint,
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrumentName" : symbol,
            "insTypeName" : instType, 
            "exchange" : "coinbase", 
            "repeat_code" : self.coinbase_repeat_response_code,
            "maximum_retries" : maximum_retries, 
            "books_dercemet" : books_dercemet,
            "payload" : payload
            }
    
    def coinbase_build_headers(self, basepoint):
        key_name       =  self.api_coinbase
        key_secret     =  self.secret_coinbase
        request_method = "GET"
        request_host   = self.coinbase_api_endpoint
        request_path   = basepoint
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

    def coinbase_fetch(self, *args, **kwargs):
        connection_data = self.coinbase_buildRequest(*args, **kwargs)
        response = CommunicationsManager.make_httpRequest(connection_data)
        return response
    
    def coinbase_aiohttpFetch(self, *args, **kwargs):
        connection_data = self.coinbase_buildRequest(*args, **kwargs)
        response = CommunicationsManager.make_aiohttpRequest_v2(connection_data)
        return response
    
    def build_jwt(self):
        key_name = self.api_coinbase
        key_secret = self.secret_coinbase
        service_name = "public_websocket_api"
        private_key_bytes = key_secret.encode('utf-8')
        private_key = serialization.load_pem_private_key(private_key_bytes, password=None)
        jwt_payload = {
            'sub': key_name,
            'iss': "coinbase-cloud",
            'nbf': int(time.time()),
            'exp': int(time.time()) + 60,
            'aud': [service_name],
        }
        jwt_token = jwt.encode(
            jwt_payload,
            private_key,
            algorithm='ES256',
            headers={'kid': key_name, 'nonce': secrets.token_hex()},
        )
        return jwt_token

    def coinbase_build_ws_method(self, instType, **kwargs):
        """
            objective : depth, trades, liquidations, oi, funding
        """
        params = dict(kwargs)
        standart_objective_name = params["objective"]
        params["objective"] = self.coinbase_stream_keys.get(params["objective"])
        message =  {
                "type": "subscribe",
                "product_ids": [params["product_id"]],
                "channel": params["objective"],
                "jwt": self.build_jwt(),
                "timestamp": int(time.time())
            }     

        return message, instType, standart_objective_name   

    def coinbase_build_ws_connectionData(self, instType, needSnap=False, snaplimit=1000, **kwargs):
        """
            insType : spot, future
            snapLimit. Coinbase manages it for you :)
            for books, needSnap should be = True
            **kwargs : only product_id, instrument type is handled automatically
        """
        params = dict(kwargs)
        message, instType, standart_objective_name = self.coinbase_build_ws_method(instType, **params)
        symbol_name = coinbase_get_symbol_name(params)
        endpoint = okx_ws_endpoint    
        connection_data =     {
                                "type" : "ws",
                                "id_ws" : f"coinbase_ws_{instType}_{standart_objective_name}_{symbol_name}",
                                "exchange":"coinbase", 
                                "instrument": symbol_name,
                                "instType": instType,
                                "objective":standart_objective_name, 
                                "updateSpeed" : None,
                                "url" : endpoint,
                                "msg" : message,
                                "sbmethod" : None
                            }
        if needSnap is True:
            connection_data["id_api"] = f"coinbase_api_{instType}_{standart_objective_name}_{symbol_name}",
            connection_data["sbmethod"] = self.coinbase_fetch 
            connection_data["sbPar"] = {
                    "product_id": params['product_id'], 
                        }
        return connection_data

    def coinbase_build_api_connectionData(self, instType:str, objective:str, pullTimeout:int, **kwargs):
        """
            insType : perpetual, spot, future, option
            objective : oi, gta
            **kwargs - those in okx ducumentations
            pullTimeout : how many seconds to wait before you make another call
            How to call : result = d['aiohttpMethod'](**kwargs)
            books don't work with aiohttp, only with http request method
        """
        connectionData = self.coinbase_buildRequest(instType, objective, **kwargs)
        params = dict(**kwargs)
        symbol_name = coinbase_get_symbol_name(params)
            
        data =  {
                "type" : "api",
                "id_ws" : f"coinbase_api_{instType}_{objective}_{symbol_name}",
                "exchange":"coinbase", 
                "instrument": symbol_name,
                "instType": instType,
                "objective": objective, 
                "pullTimeout" : pullTimeout,
                "connectionData" : connectionData,
                "aiohttpMethod" : partial(self.coinbase_aiohttpFetch, instType=instType, objective=objective),
                "params" : dict(**kwargs)
                }
        
        return data

class kucoin(CommunicationsManager):
    """
        Abstraction of kucoin api calls
    """

    def __init__ (self, api_kucoin, secret_kucoin, pass_kucoin):
        self.kucoin_repeat_response_code = kucoin_repeat_response_code
        self.api_kucoin = api_kucoin
        self.secret_kucoin = secret_kucoin
        self.pass_kucoin = pass_kucoin
        self.kucoin_api_endpoints = kucoin_api_endpoints
        self.kucoin_api_basepoints = kucoin_api_basepoints
        self.kucoin_stream_keys = kucoin_stream_keys
        self.kucoin_ws_endpoint = kucoin_ws_endpoint


    def kucoin_buildRequest(self, instType:str, objective:str, maximum_retries:int=10, books_dercemet:int=100, **kwargs)->dict: 
        """
            instType : spot, perpetual
            objective :  depth, oifunding
            omit maximum_retries and books_dercemet, kucoin handles it for you
            **kwargs : request parameters, check kucoin API docs
        """
        params = dict(kwargs)
        symbol_name = kucoin_get_symbol_name(params)
        endpoint = self.kucoin_api_endpoints.get(instType)
        basepoint = self.kucoin_api_basepoints.get(instType).get(objective)

        # Unstandarized api 
        if objective == "oifunding":
            symbol = params.pop("symbol")
            basepoint = f"{basepoint}{symbol}"
        
        payload = ''
        headers = self.kucoin_build_headers(basepoint, params)
        return {
            "url" : endpoint + basepoint,
            "endpoint" : endpoint, 
            "basepoint" : basepoint,
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrumentName" : symbol_name,
            "insTypeName" : instType, 
            "exchange" : "kucoin", 
            "repeat_code" : self.kucoin_repeat_response_code,
            "maximum_retries" : maximum_retries, 
            "books_dercemet" : books_dercemet,
            "payload" : payload
            }
    
    def kucoin_build_ws_method(self, instType, **kwargs):
        """
            objective : depth, trades, liquidations, oi, funding
        """
        params = dict(kwargs)
        standart_objective_name = params["objective"]
        topic = self.kucoin_stream_keys.get(instType).get(standart_objective_name)
        symbol = params.get("symbol")
        message =  {
                "id": generate_random_integer(10),   
                "type": "subscribe",
                "topic": f"{topic}{symbol}",
                "response": True
                }

        return message, instType, standart_objective_name   
    
    def kucoin_parse_basepoint_params(self, basepoint, params):
        return "?".join([basepoint, urllib.parse.urlencode(params) if params else ""])

    def kucoin_build_headers(self, basepoint, params):
        basepoint_headers = self.kucoin_parse_basepoint_params(basepoint, params)
        apikey = self.api_kucoin 
        secretkey = self.secret_kucoin
        password = self.pass_kucoin 
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

    def build_kucoin_ws_endpoint(self):
        """
            Returns kucoin token and endpoint
        """
        kucoin_api = self.kucoin_ws_endpoint
        response = requests.post(kucoin_api)
        kucoin_token = response.json().get("data").get("token")
        kucoin_endpoint = response.json().get("data").get("instanceServers")[0].get("endpoint")
        kucoin_connectId = generate_random_id(20)
        return f"{kucoin_endpoint}?token={kucoin_token}&[connectId={kucoin_connectId}]"

    def kucoin_fetch(self, *args, **kwargs):
        connection_data = self.kucoin_buildRequest(*args, **kwargs)
        response = CommunicationsManager.make_request(connection_data)
        return response
    
    async def kucoin_aiohttpFetch(self, *args, **kwargs):
        connection_data = self.kucoin_buildRequest(*args, **kwargs)
        response = await self.make_aiohttpRequest_v2(connection_data)
        return response

    def kucoin_build_ws_connectionData(self, instType, needSnap=False, snaplimit=1000, **kwargs):
        """
            insType : spot, perpetual
            needSnap = True for books
            omit snap limit
            for books, needSnap should be = True
            **kwargs : only product_id, instrument type is handled automatically
        """
        params = dict(kwargs)
        message, instType, standart_objective_name = self.kucoin_build_ws_method(instType, **params)
        symbol_name = kucoin_get_symbol_name(params)
        endpoint = self.build_kucoin_ws_endpoint()    
        connection_data =     {
                                "type" : "ws",
                                "id_ws" : f"kucoin_ws_{instType}_{standart_objective_name}_{symbol_name}",
                                "exchange":"kucoin", 
                                "instrument": symbol_name,
                                "instType": instType,
                                "objective":standart_objective_name, 
                                "updateSpeed" : None,
                                "url" : endpoint,
                                "msg" : message,
                                "sbmethod" : None
                            }
        if needSnap is True:
            connection_data["id_api"] = f"kucoin_api_{instType}_{standart_objective_name}_{symbol_name}",
            connection_data["sbmethod"] = self.kucoin_fetch 
            connection_data["sbPar"] = {
                    "symbol": params['symbol'], 
                        }
        return connection_data

    def kucoin_build_api_connectionData(self, instType:str, objective:str, pullTimeout:int, **kwargs):
        """
            insType : perpetual, spot, future, option
            objective : oi, gta
            **kwargs - those in okx ducumentations
            pullTimeout : how many seconds to wait before you make another call
            How to call : result = d['aiohttpMethod'](**kwargs)
            books don't work with aiohttp, only with http request method
        """
        connectionData = self.kucoin_buildRequest(instType, objective, **kwargs)
        params = dict(**kwargs)
        symbol_name = kucoin_get_symbol_name(params)
            
        data =  {
                "type" : "api",
                "id_ws" : f"kucoin_api_{instType}_{objective}_{symbol_name}",
                "exchange":"kucoin", 
                "instrument": symbol_name,
                "instType": instType,
                "objective": objective, 
                "pullTimeout" : pullTimeout,
                "connectionData" : connectionData,
                "aiohttpMethod" : partial(self.kucoin_aiohttpFetch, instType=instType, objective=objective),
                "params" : dict(**kwargs)
                }
        
        return data
    
class bingx(CommunicationsManager):

    def __init__ (self, api_bingx="", secret_bingx=""):
        self.api_bingx = api_bingx
        self.secret_bingx = secret_bingx
        self.bingx_api_endpoint = bingx_api_endpoint
        self.bingx_api_basepoints = bingx_api_basepoints
        self.bingx_ws_endpoints = bingx_ws_endpoints
        self.bingx_stream_keys = bingx_stream_keys
        self.bingx_repeat_response_code = bingx_repeat_response_code


    def bingx_buildRequest(self, instType:str, objective:str, 
                     possible_limits:list=[1000, 500, 100, 50, 20, 10, 5], books_dercemet:int=100, **kwargs)->dict: 
        """
            instType : spot, derivate
            objective :  depth, funding, oi
            Maxium retries of an API with different parameters in case API call is impossible. Useful when you cant catch the limit
            books_dercemet : the derement of books length in case of api call being unsuccessful. If applicable
            **kwargs : request parameters like symbol
        """
        params = dict(kwargs)
        symbol_name = bingx_get_symbol_name(params)
        endpoint = self.bingx_api_endpoint
        basepoint = self.bingx_api_basepoints.get(instType).get(objective)
        payload = {}
        url, headers = self.bingx_get_url_headers(endpoint, basepoint, params, self.api_bingx, self.secret_bingx)
        return {
            "url" : url,
            "endpoint" : endpoint, 
            "basepoint" : url,
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrumentName" : symbol_name,
            "insTypeName" : instType, 
            "exchange" : "bingx", 
            "repeat_code" : self.bingx_repeat_response_code,
            "maximum_retries" : 1, 
            "books_dercemet" : books_dercemet,
            "payload" : payload,
            "possible_limits" : possible_limits
            }

    def bingx_get_url_headers(self, endpoint, basepoint, params, api, secret):
        parsed_params = self.bingx_parseParam(params)
        url = "%s%s?%s&signature=%s" % (endpoint, basepoint, parsed_params, self.bingx_get_sign(secret, parsed_params))
        headers = {
            'X-BX-APIKEY': api,
        }
        return url, headers

    def bingx_parseParam(self, params):
        sortedKeys = sorted(params)
        paramsStr = "&".join(["%s=%s" % (x, params[x]) for x in sortedKeys])
        if paramsStr != "": 
            return paramsStr+"&timestamp="+str(int(time.time() * 1000))
        else:
            return paramsStr+"timestamp="+str(int(time.time() * 1000))
    
    def bingx_get_sign(self, api_secret, payload):
        signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
        return signature

    def bingx_fetch(self, *args, **kwargs):
        connection_data = self.bingx_buildRequest(*args, **kwargs)
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

    async def bingx_aiohttpFetch(self, *args, **kwargs):
        connection_data = self.bingx_buildRequest(*args, **kwargs)
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
            return await CommunicationsManager.make_aiohttpRequest(connection_data)

    def bingx_build_api_connectionData(self, instType:str, objective:str, pullTimeout:int, **kwargs):
        """
            insType : perpetual, spot, future, option
            objective : oi, gta
            **kwargs - those in okx ducumentations
            pullTimeout : how many seconds to wait before you make another call
            How to call : result = d['aiohttpMethod'](**kwargs)
            books don't work with aiohttp, only with http request method
        """
        connectionData = self.bingx_buildRequest(instType, objective, **kwargs)
        params = dict(**kwargs)
        symbol_name = bingx_get_symbol_name(params)
            
        data =  {
                "type" : "api",
                "id_ws" : f"bingx_api_{instType}_{objective}_{symbol_name}",
                "exchange":"bingx", 
                "instrument": symbol_name,
                "instType": instType,
                "objective": objective, 
                "pullTimeout" : pullTimeout,
                "connectionData" : connectionData,
                "aiohttpMethod" : partial(self.bingx_aiohttpFetch, instType=instType, objective=objective),
                "params" : dict(**kwargs)
                }
        
        return data

    def bingx_build_ws_method(self, instType, **kwargs):
        """
            objective : depth, trades, liquidations, oi, funding
        """
        params = dict(kwargs)
        standart_objective_name = params["objective"]
        topic = self.bingx_stream_keys.get(standart_objective_name)
        symbol = params.get("symbol")
        pullSpeed = "" if "pullSpeed" not in params else f"@{params['pullSpeed']}"
        message =  {
                "id" : generate_random_id(20),
                "reqType": "sub",
                "dataType":f"{symbol}@{topic}{pullSpeed}"
                }

        return message, instType, standart_objective_name   
    
    def bingx_build_ws_connectionData(self, instType, needSnap=False, snaplimit=1000, **kwargs):
        """
            insType : spot, perpetual
            omit snap limit, needSnap
            **kwargs : symbol, objective, pullSpeed
        """
        params = dict(kwargs)
        message, instType, standart_objective_name = self.bingx_build_ws_method(instType, **params)
        symbol_name = bingx_get_symbol_name(params)
        endpoint = self.bingx_ws_endpoints.get(instType)  
        connection_data =     {
                                "type" : "ws",
                                "id_ws" : f"bingx_ws_{instType}_{standart_objective_name}_{symbol_name}",
                                "exchange":"bingx", 
                                "instrument": symbol_name,
                                "instType": instType,
                                "objective":standart_objective_name, 
                                "updateSpeed" : None,
                                "url" : endpoint,
                                "msg" : message,
                                "sbmethod" : None
                            }
        return connection_data

class bitget(CommunicationsManager):
    """
        Abstraction of bybit api calls
    """
    bitget_repeat_response_code = bitget_repeat_response_code
    bitget_api_endpoint = bitget_api_endpoint
    bitget_productType_map = bitget_productType_map
    bitget_api_basepoints = bitget_api_basepoints
    bitget_ws_endpoint = bitget_ws_endpoint
    bitget_stream_keys = bitget_stream_keys


    @classmethod
    def bitget_buildRequest(cls, instType:str, objective:str, maximum_retries:int=10, books_dercemet:int=100, **kwargs)->dict: 
        """
            objective :  depth, trades. oifunding
            **kwargs : request parameters. Verify with bitget api
        """
        params = dict(kwargs)
        # marginType, marginCoin mapping
        instrument, symbol_name, marginType, marginCoin, productType = bitget_get_variables(params, instType)
        if instType != "spot":
            params["productType"] = productType
        #  url
        endpoint = cls.bitget_api_endpoint
        basepoint = cls.bitget_api_basepoints.get(instType).get(objective)
        url = endpoint + basepoint
        headers = {}
        return {
            "url" : url,
            "basepoint" : basepoint,  
            "endpoint" : endpoint,  
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrumentName" : symbol_name, 
            "insTypeName" : instType, 
            "exchange" : "bitget", 
            "repeat_code" : cls.bitget_repeat_response_code,
            "maximum_retries" : maximum_retries, 
            "books_dercemet" : books_dercemet,
            "payload" : "",
            "marginType" : marginType,
            "marginCoin" : marginCoin
            }

    @classmethod
    def bitget_fetch(cls, *args, **kwargs):
        connection_data = cls.bitget_buildRequest(*args, **kwargs)
        response = cls.make_request(connection_data)
        return response

    @classmethod
    async def bitget_aiohttpFetch(cls, *args, **kwargs):
        connection_data = cls.bitget_buildRequest(*args, **kwargs)
        response = await cls.make_aiohttpRequest(connection_data)
        return response

    @classmethod
    def bitget_build_api_connectionData(cls, instType:str, objective:str, pullTimeout:int, **kwargs):
        """
            insType : perpetual, spot
            objective : depth
            **kwargs - those in okx ducumentations
            pullTimeout : how many seconds to wait before you make another call
            How to call : result = d['aiohttpMethod'](**kwargs)
            books don't work with aiohttp, only with http request method
        """
        connectionData = cls.bitget_buildRequest(instType, objective, **kwargs)
        params = dict(**kwargs)
        symbol_name = bitget_get_symbol_name(params)
            
        data =  {
                "type" : "api",
                "id_api" : f"bitget_api_{instType}_{objective}_{symbol_name}",
                "exchange":"bitget", 
                "instrument": symbol_name,
                "instType": instType,
                "objective": objective, 
                "pullTimeout" : pullTimeout,
                "connectionData" : connectionData,
                "aiohttpMethod" : partial(cls.bitget_aiohttpFetch, instType=instType, objective=objective),
                "params" : dict(**kwargs)
                }
        
        return data

    @classmethod
    def bitget_build_ws_method(cls, instType, **kwargs):
        """
            objective : depth, trades, liquidations, oi, funding
        """
        params = dict(kwargs)
        standart_objective_name = params["objective"]
        topic = cls.bitget_stream_keys.get(standart_objective_name)
        symbol = params.get("symbol")
        bitgetInstType = get_bitget_instType(params, instType)
        message =  {
                "op": "subscribe",
                "args": [
                    {
                        "instType": bitgetInstType,
                        "channel": topic,
                        "instId": symbol,
                    }
                ] 
        }

        return message, instType, standart_objective_name   

    @classmethod    
    def bitget_build_ws_connectionData(cls, instType, needSnap=True, snaplimit=None, **kwargs):
        """
            insType : spot, perpetual
            omit snap limit, needSnap
            **kwargs : symbol, objective, pullSpeed (if applicable) Inspect bitget API docs
        """
        params = dict(kwargs)
        message, instType, standart_objective_name = cls.bitget_build_ws_method(instType, **params)
        symbol_name = bitget_get_symbol_name(params)
        endpoint = cls.bitget_ws_endpoint
        connection_data =     {
                                "type" : "ws",
                                "id_ws" : f"bitget_ws_{instType}_{standart_objective_name}_{symbol_name}",
                                "exchange":"bitget", 
                                "instrument": symbol_name,
                                "instType": instType,
                                "objective":standart_objective_name, 
                                "updateSpeed" : None,
                                "url" : endpoint,
                                "msg" : message,
                                "sbmethod" : None,
                                "marginCoin" : message.get("args")[0].get("instType"),
                                "marginType" : "InversePerpetual" if "COIN" in message.get("args")[0].get("instType") else "LinearPerpetual"
                            }
        if needSnap is True:
            connection_data["id_api"] = f"bitget_api_{instType}_{standart_objective_name}_{symbol_name}"
            connection_data["sbmethod"] = cls.bitget_fetch 
            connection_data["sbPar"] = {
                    "symbol": params['symbol'], 
                        }
            if "snaplimit" != None:
                connection_data["snaplimit"] = snaplimit
        return connection_data

class deribit(CommunicationsManager):
    """
        Abstraction of bybit api calls
    """
    deribit_repeat_response_code = deribit_repeat_response_code
    deribit_endpoint = deribit_endpoint
    deribit_marginCoins = deribit_marginCoins
    deribit_methods = deribit_methods
    deribit_stream_keys = deribit_stream_keys
    deribit_instType_keys = deribit_instType_keys

    @classmethod
    def deribit_buildRequest(cls, instType:str, objective:str, maximum_retries:int=10, books_dercemet:int=100, **kwargs)->dict: 
        """
            instType : spot, perpetual, future, option
            objective : depth, oi. Please check available methods by exchange
            **kwargs : see the deribit api docs for params. They are identical
            ** you may use limit instead of depth argument if you need to snap orderbooks
            omit maximum_retries and books_dercemet as deribit handles this for you

        """
        params = dict(**kwargs)
        symbol_name = deribit_get_symbol_name(params)
        headers = cls.deribit_build_api_headers(instType, objective, **kwargs)
        endpoint = cls.deribit_endpoint
        return {
            "endpoint" : endpoint,  
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrumentName" : symbol_name,
            "insTypeName" : instType,
            "exchange" : "deribit", 
            "repeat_code" : cls.deribit_repeat_response_code,
            "maximum_retries" : maximum_retries, 
            "books_dercemet" : books_dercemet,
            "payload" : "",
            }

    @classmethod
    def deribit_fetch(cls, *args, **kwargs):
        connection_data = cls.deribit_buildRequest(*args, **kwargs)
        response = cls.make_wsRequest_http(connection_data)
        return response

    @classmethod
    async def deribit_aiohttpFetch(cls, *args, **kwargs):
        connection_data = cls.deribit_buildRequest(*args, **kwargs)
        response = await cls.make_wsRequest(connection_data)
        return response
    
    @classmethod
    def deribit_build_api_headers(cls, instType, objective, **kwargs):
        method = cls.deribit_methods.get(objective)
        params = dict(**kwargs)
        if method != "ws":
            if "limit" in params:
                params["depth"] = params.pop("limit")
            if "symbol" in params:
                params["instrument_name"] = params.pop("symbol")
            if "instrument_name" in params and params["instrument_name"] in cls.deribit_marginCoins:
                params["currency"] = params.pop("instrument_name")
            if "currrency" in params:
                params["kind"] = cls.deribit_instType_keys.get(instType)
        api_headers = {
                "jsonrpc": "2.0", 
                "id": generate_random_integer(10),
                "method": method,
                "params": params
            }
        return api_headers
    
    @classmethod
    def deribit_build_ws_headers(cls, instType, objective, **kwargs):
        # standart_objective = cls.deribit_methods.get(objective)
        method="public/subscribe"
        params = dict(**kwargs)
        obj = cls.deribit_stream_keys.get(objective)
        s = params.get("symbol")
        ps = "" if "pullSpeed" not in params else params["pullSpeed"]
        params = {
            "channels" : [f"{obj}.{s}.{ps}"] if ps != "" else [f"{obj}.{s}"]
        }
        api_headers = {
                    "jsonrpc": "2.0", 
                    "id": generate_random_integer(10),
                    "method": method,
                    "params": params
        }
        return api_headers

    @classmethod
    def deribit_build_api_connectionData(cls, instType:str, objective:str, pullTimeout:int, **kwargs):
        """
            insType : perpetual, spot, future, option
            objective : oifunding, depth
            **kwargs - those in deribit ducumentations
            pullTimeout : how many seconds to wait before you make another call
            How to call : result = d['aiohttpMethod'](**kwargs)
            books don't work with aiohttp, only with http request method
        """
        connectionData = cls.deribit_buildRequest(instType, objective, **kwargs)
        params = dict(**kwargs)
        symbol_name = kucoin_get_symbol_name(params)
            
        data =  {
                "type" : "api",
                "id_ws" : f"kucoin_api_{instType}_{objective}_{symbol_name}",
                "exchange":"kucoin", 
                "instrument": symbol_name,
                "instType": instType,
                "objective": objective, 
                "pullTimeout" : pullTimeout,
                "connectionData" : connectionData,
                "aiohttpMethod" : partial(cls.deribit_aiohttpFetch, instType=instType, objective=objective),
                "params" : dict(**kwargs)
                }
        
        return data

    @classmethod
    def deribit_build_ws_connectionData(cls, instType, needSnap=True, snaplimit=1000, **kwargs):
        """
            insType : spot, perpetual
            needSnap = True for books
            for books, needSnap should be = True if you for depth websocket
            **kwargs : symbol, objective, pullSpeed (if applicable)
        """
        params = dict(kwargs)
        symbol = params["symbol"]
        standart_objective_name = params.pop("objective")
        message = cls.deribit_build_ws_headers(instType, standart_objective_name, **params)
        symbol_name = deribit_get_symbol_name(params)
        endpoint = cls.deribit_endpoint 
        connection_data =     {
                                "type" : "ws",
                                "id_ws" : f"deribit_ws_{instType}_{standart_objective_name}_{symbol_name}",
                                "exchange":"deribit", 
                                "instrument": symbol_name,
                                "instType": instType,
                                "objective":standart_objective_name, 
                                "updateSpeed" : None,
                                "url" : endpoint,
                                "msg" : message,
                                "sbmethod" : None
                            }
        if needSnap is True:
            connection_data["id_api"] = f"deribit_api_{instType}_{standart_objective_name}_{symbol_name}",
            connection_data["sbmethod"] = cls.deribit_fetch 
            connection_data["sbPar"] = {
                    "instType" : instType,
                    "objective" : standart_objective_name,
                    "symbol": symbol, 
                        }
        return connection_data

class htx(CommunicationsManager):
    """
        Abstraction of bybit api calls
    """
    htx_repeat_response_code = htx_repeat_response_code
    htx_api_endpoints = htx_api_endpoints
    htx_ws_endpoints = htx_ws_endpoints
    htx_api_basepoints = htx_api_basepoints
    htx_ws_stream_map = htx_ws_stream_map
    htx_InverseFuture_quarters_map = htx_InverseFuture_quarters_map


    @classmethod
    def htx_buildRequest(cls, instType:str, objective:str, symbol:str, futuresTimeHorizeon:int=None, maximum_retries:int=10, books_dercemet:int=100, **kwargs)->dict: 
        """
            available objectives :  depth, oi, funding, tta, ttp, liquidations
            symbol is the one fetched from info
        """
        symbol_name = htx_symbol_name(symbol)
        marginType = htx_get_marginType(symbol)
        params = htx_parse_params(objective, instType, marginType, symbol, futuresTimeHorizeon)
        endpoint = cls.htx_api_endpoints.get(instType)
        try:
            basepoint = cls.htx_api_basepoints.get(instType).get(marginType).get(objective)
        except:
            basepoint = cls.htx_api_basepoints.get(instType).get(objective)
        url = endpoint + basepoint
        headers = {}
        return {
            "url" : url,
            "basepoint" : basepoint,  
            "endpoint" : endpoint,  
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrumentName" : symbol_name, 
            "insTypeName" : instType, 
            "exchange" : "htx", 
            "repeat_code" : cls.htx_repeat_response_code,
            "maximum_retries" : maximum_retries, 
            "books_dercemet" : books_dercemet,
            "payload" : "",
            "marginType" : marginType,
            }

    @classmethod
    def htx_fetch(cls, *args, **kwargs):
        connection_data = cls.htx_buildRequest(*args, **kwargs)
        response = cls.make_request(connection_data)
        return response

    @classmethod
    async def htx_aiohttpFetch(cls, *args, **kwargs):
        connection_data = cls.htx_buildRequest(*args, **kwargs)
        response = await cls.make_aiohttpRequest(connection_data)
        return response

    @classmethod
    async def htx_aiohttpFetch_futureDepth(cls):
        data = {}
        for t in range(4):
            connection_data = cls.htx_buildRequest(instType="future", objective="depth", symbol="BTC", futuresTimeHorizeon=t)
            response = await cls.make_aiohttpRequest(connection_data)
            data[t] = response
        return data

    @classmethod
    async def htx_aiohttpFetch_futureTrades(cls):
        data = {}
        for t in range(4):
            connection_data = cls.htx_buildRequest(instType="future", objective="trades", symbol="BTC", futuresTimeHorizeon=t)
            response = await cls.make_aiohttpRequest(connection_data)
            data[t] = response
        return data

    @classmethod
    async def htx_aiohttpFetch_futureOI(cls):
        data = {}
        for t in range(4):
            connection_data = cls.htx_buildRequest(instType="future", objective="oi", symbol="BTC", futuresTimeHorizeon=t)
            response = await cls.make_aiohttpRequest(connection_data)
            data[t] = response
        return data

    @classmethod
    def htx_build_api_connectionData(cls, instType:str, objective:str, symbol:str, pullTimeout:int, special=None, **kwargs):
        """
            insType : perpetual, spot, future
            objective : depth, oi, tta, ttp
            symbol : from htx symbols
            pullTimeout : how many seconds to wait before you make another call
            special : futureDepth, futureOI
        """
        connectionData = cls.htx_buildRequest(instType, objective, symbol, **kwargs)
        symbol_name = htx_symbol_name(symbol)
        
        if special == "futuredepth":
            call = partial(cls.htx_aiohttpFetch_futureOI)
        if special == "futureoi":
            call = partial(cls.htx_aiohttpFetch_futureOI)
        else:
            call = partial(cls.htx_aiohttpFetch, instType=instType, objective=objective, symbol=symbol)

        data =  {
                "type" : "api",
                "id_api" : f"htx_api_{instType}_{objective}_{symbol_name}",
                "exchange":"htx", 
                "instrument": symbol_name,
                "instType": instType,
                "objective": objective, 
                "pullTimeout" : pullTimeout,
                "connectionData" : connectionData,
                "aiohttpMethod" : call,
                }
        
        return data

    @classmethod
    def htx_parse_ws_objective(cls, instType, objective, symbol):
        """
            objectives : trades, depth, liquidations, funding
        """
        parsed_objective = cls.htx_ws_stream_map.get(objective).split(".")
        parsed_objective[1] = symbol
        parsed_objective = ".".join(parsed_objective)
        if instType == "spot" and objective=="depth":
            msg = {
                "sub": f"market.{symbol}.depth.size_20.high_freq",
                "data_type":"incremental",
                "id": generate_random_integer(10)
                }
        else:
            topic = htx_ws_stream_map.get(objective).split(".")
            topic[1] = symbol
            msg = {
                "sub": parsed_objective,
                "id": generate_random_integer(10)
                }
        return msg

    @classmethod
    def htx_build_ws_method(cls, instType, objective, symbol, **kwargs):
        """
            objectives : trades, depth ,liquidations, funding
            instType : spot, future, perpetual
            symbol : the one from htx info
        """
        message = cls.htx_parse_ws_objective(instType, objective, symbol)
        marginType = htx_get_marginType(symbol)
        url = htx_get_ws_url(instType, objective, marginType)

        return message, instType, marginType, url, symbol

    @classmethod    
    def htx_build_ws_connectionData(cls, instType, objective, symbol, needSnap=True, snaplimit=None, **kwargs):
        """
            objectives : trades, depth ,liquidations, funding
            instType : spot, future, perpetual
            symbol : the one from htx info
            needSnap = True for books, you need to take the first snapshot.
            do not use snaplimit more than 100
        """
        message, instType, marginType, url, symbol = cls.htx_build_ws_method(instType, objective, symbol)
        symbol_name = htx_symbol_name(symbol)
        connection_data =     {
                                "type" : "ws",
                                "id_ws" : f"htx_ws_{instType}_{objective}_{symbol_name}",
                                "exchange":"htx", 
                                "instrument": symbol_name,
                                "instType": instType,
                                "objective":objective, 
                                "updateSpeed" : None,
                                "address" : url,
                                "msg" : message,
                                "kickoffMethod" : None,
                                "marginType" : marginType,
                                "marginCoin" : "any" if "usdt" not in symbol_name and instType != "spot" else "usdt"
                            }
        if needSnap is True:
            connection_data["id_api"] = f"htx_api_{instType}_{objective}_{symbol_name}"
            connection_data["kickoffMethod"] = partial(cls.htx_fetch, instType, objective, symbol) 
        return connection_data

class mexc(CommunicationsManager):
    """
        Abstraction of bybit api calls
    """
    mexc_repeat_response_code = mexc_repeat_response_code
    mexc_api_endpoints = mexc_api_endpoints
    mexc_ws_endpoints = mexc_ws_endpoints
    mexc_api_basepoints = mexc_api_basepoints
    mexc_ws_stream_map = mexc_ws_stream_map


    @classmethod
    def mexc_buildRequest(cls, instType:str, objective:str, symbol:str, maximum_retries:int=10, books_dercemet:int=100, **kwargs)->dict: 
        """
            available objectives :  depth
            symbol is the one fetched from info
            omit maximum_retries and books_decrement
        """
        symbol_name = mexc_get_symbol_name(symbol)
        params = mexc_api_parseParams(instType, objective, symbol)
        endpoint = cls.mexc_api_endpoints.get(instType)
        basepoint = cls.mexc_api_basepoints.get(instType).get(objective)
        url = endpoint + basepoint
        headers = {}
        return {
            "url" : url,
            "basepoint" : basepoint,  
            "endpoint" : endpoint,  
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrument" : symbol_name, 
            "insType" : instType, 
            "exchange" : "mexc", 
            "repeat_code" : cls.mexc_repeat_response_code,
            "maximum_retries" : maximum_retries, 
            "books_dercemet" : books_dercemet,
            "payload" : "",
            "marginType" : None if instType == "spot" else "usdt",
            }

    @classmethod
    def mexc_fetch(cls, *args, **kwargs):
        connection_data = cls.mexc_buildRequest(*args, **kwargs)
        response = cls.make_request(connection_data)
        return response

    @classmethod
    async def mexc_aiohttpFetch(cls, *args, **kwargs):
        connection_data = cls.mexc_buildRequest(*args, **kwargs)
        response = await cls.make_aiohttpRequest(connection_data)
        return response

    @classmethod
    def mexc_build_api_connectionData(cls, instType:str, objective:str, symbol:str, pullTimeout:int, special=None, **kwargs):
        """
            insType : perpetual, spot
            objective : depth
            symbol : from mexc symbols
            pullTimeout : how many seconds to wait before you make another call
            special : No special methods for mexc
        """
        connectionData = cls.mexc_buildRequest(instType, objective, symbol, **kwargs)
        symbol_name = mexc_get_symbol_name(symbol)
        call = partial(cls.mexc_aiohttpFetch, instType=instType, objective=objective, symbol=symbol)
        data =  {
                "type" : "api",
                "id_api" : f"mexc_api_{instType}_{objective}_{symbol_name}",
                "exchange":"mexc", 
                "instrument": symbol_name,
                "instType": instType,
                "objective": objective, 
                "pullTimeout" : pullTimeout,
                "connectionData" : connectionData,
                "aiohttpMethod" : call,
                }
        
        return data

    @classmethod
    def mexc_build_ws_msg(cls, instType, objective, symbol):
        """
            objectives : trades, depth, liquidations, funding
        """
        obj = cls.mexc_ws_stream_map.get(objective) if objective!="trades" else cls.mexc_ws_stream_map.get(objective).get(instType)
        if instType == "spot":
                if obj == "depth":
                    obj = f"increase.{obj}"
                msg = {
                    "method": "SUBSCRIPTION",
                    "params": [
                        f"spot@public.{obj}.v3.api@{symbol}"
                    ]
                }
        if instType == "perpetual":
                msg = {
                "method": f"sub.{obj}",
                "param":{
                    "symbol": symbol
                }
            }
        return msg

    @classmethod    
    def mexc_build_ws_connectionData(cls, instType, objective, symbol, needSnap=True, snaplimit=None, **kwargs):
        """
            objectives : trades, oifunding, depth
            instType : spot, perpetual
            symbol : the one from mexc info
            needSnap must be true for depth
        """
        message = cls.mexc_build_ws_msg(instType, objective, symbol)
        symbol_name = mexc_get_symbol_name(symbol)
        url = cls.mexc_ws_endpoints.get(instType)
        connection_data =     {
                                "type" : "ws",
                                "id_ws" : f"mexc_ws_{instType}_{objective}_{symbol_name}",
                                "exchange":"mexc", 
                                "instrument": symbol_name,
                                "instType": instType,
                                "objective":objective, 
                                "updateSpeed" : None,
                                "address" : url,
                                "msg" : message,
                                "kickoffMethod" : None,
                                "marginType" : None if instType == "spot" else "usdt",
                                "marginCoin" : "any" if "usdt" not in symbol_name and instType != "spot" else "usdt"
                            }
        if needSnap is True:
            connection_data["id_api"] = f"mexc_api_{instType}_{objective}_{symbol_name}"
            connection_data["kickoffMethod"] = partial(cls.mexc_fetch, instType, objective, symbol) 
        return connection_data

class gateio(CommunicationsManager, gateioInfo):
    """
        Abstraction of bybit api calls
    """
    gateio_repeat_response_code = gateio_repeat_response_code
    gateio_api_endpoint = gateio_api_endpoint
    gateio_api_headers = gateio_api_headers
    gateio_basepoints = gateio_basepoints
    gateio_basepoints_standard_params = gateio_basepoints_standard_params
    gateio_ws_endpoints = gateio_ws_endpoints
    gateio_ws_channel_map = gateio_ws_channel_map
    gateio_ws_payload_map = gateio_ws_payload_map

    @classmethod
    def gateio_get_active_option_instruments(cls, underlying):
        symbols = gateioInfo.gateio_info("option")
        symbols = [x["name"] for x in symbols if underlying in x["underlying"] and x["is_active"] == True]
        return symbols

    @classmethod
    def gateio_build_ws_message_all_Options(cls, objective, underlying):
        symbols = cls.gateio_get_active_option_instruments(underlying)
        channel = gateio_ws_channel_map.get("option").get(objective)
        if objective == "depth":
            payload = [[symbol, "1000", "20"] for symbol in symbols]
        else:
            payload = [[symbol] for symbol in symbols]
        msg = {
            "time": int(time.time()),
            "channel": channel,
            "event": "subscribe",  
            "payload": unnest_list(payload)
            }
        return msg

    @classmethod
    def gateio_buildRequest(cls, instType:str, objective:str, symbol:str, maximum_retries:int=10, books_dercemet:int=100, snapLength=20, **kwargs)->dict: 
        """
            available objectives :  depth, trades, funding, oi (containts tta), liquidations 
            symbol is the one fetched from info
        """
        symbol_name = gateio_get_symbolname(symbol)
        marginType = gateio_get_marginType(instType, symbol)
        basepoint = gateio_get_basepoint(instType, objective, marginType, interval=snapLength)
        params = gateio_get_api_standard_params(instType, objective)(symbol, snapLength)
        headers = cls.gateio_api_headers
        endpoint = cls.gateio_api_endpoint
        url = endpoint + basepoint
        return {
            "url" : url,
            "basepoint" : basepoint,  
            "endpoint" : endpoint,  
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrument" : symbol_name, 
            "insType" : instType, 
            "exchange" : "gateio", 
            "repeat_code" : cls.mexc_repeat_response_code,
            "maximum_retries" : maximum_retries, 
            "books_dercemet" : books_dercemet,
            "payload" : "",
            "marginType" : marginType
            }

    @classmethod
    def gateio_fetch(cls, *args, **kwargs):
        connection_data = cls.gateio_buildRequest(*args, **kwargs)
        response = cls.make_request(connection_data)
        return response

    @classmethod
    async def gateio_aiohttpFetch(cls, *args, **kwargs):
        connection_data = cls.gateio_buildRequest(*args, **kwargs)
        response = await cls.make_aiohttpRequest(connection_data)
        return response

    @classmethod
    def gateio_build_api_connectionData(cls, instType:str, objective:str, symbol:str, pullTimeout:int, special=None, **kwargs):
        """
            available objectives :  depth, trades, funding, oi (containts tta), liquidations 
            symbol is the one fetched from info
            pullTimeout : how many seconds to wait before you make another call
            special : not for now
        """
        connectionData = cls.gateio_buildRequest(instType, objective, symbol, pullTimeout, **kwargs)
        symbol_name = gateio_get_symbolname(symbol)
        call = partial(cls.gateio_aiohttpFetch, instType=instType, objective=objective, symbol=symbol)
        data =  {
                "type" : "api",
                "id_api" : f"gateio_api_{instType}_{objective}_{symbol_name}",
                "exchange":"gateio", 
                "instrument": symbol_name,
                "instType": instType,
                "objective": objective, 
                "pullTimeout" : pullTimeout,
                "connectionData" : connectionData,
                "aiohttpMethod" : call,
                }
        
        return data

    @classmethod    
    def gateio_build_ws_connectionData(cls, instType, objective, symbol, needSnap=True, snaplimit=None, **kwargs):
        """
            objectives : trades, oifunding, depth
            instType : spot, perpetual
            symbol : the one from mexc info
            needSnap must be true for depth
        """
        marginType = gateio_get_marginType(instType, symbol)
        url = gateio_get_ws_url(instType, objective, marginType, symbol)
        message = gateio_build_ws_message(instType, objective, symbol)
        symbol_name = gateio_get_symbolname(symbol)
        connection_data =     {
                                "type" : "ws",
                                "id_ws" : f"gateio_ws_{instType}_{objective}_{symbol_name}",
                                "exchange":"gateio", 
                                "instrument": symbol_name,
                                "instType": instType,
                                "objective":objective, 
                                "updateSpeed" : None,
                                "address" : url,
                                "msg" : message,
                                "kickoffMethod" : None,
                                "marginType" : marginType,
                                "marginCoin" : "btc" if marginType == "InversePerpetual" else "usdt",
                            }
        if needSnap is True:
            connection_data["id_api"] = f"gateio_api_{instType}_{objective}_{symbol_name}"
            connection_data["kickoffMethod"] = partial(cls.gateio_fetch, instType, objective, symbol)
        if instType == "option":
            connection_data["get_option_instruments_Method"] = partial(cls.gateio_get_active_option_instruments(cls, symbol)) 
        return connection_data



class clientTest(binance, bybit, bitget, deribit, okx, htx, mexc, gateio):
    
    @classmethod
    def test_deribit_apiData(cls, **kwargs):
        # a = cls.deribit_fetch("option", "oifunding", symbol="BTC")
        # print(a)
        async def example():
            d = cls.deribit_build_api_connectionData("option", "depth", 100, symbol="BTC-PERPETUAL", limit=1000)
            result = await d['aiohttpMethod'](**d["params"])
            # a = await cls.deribit_aiohttpFetch("option", "oifunding", symbol="BTC", limit=1000) # works even with unnecessary arguments
            print(result)

        asyncio.run(example())

    @classmethod
    def test_deribit_wsData(cls, **kwargs):
        #async def example():
        d = cls.deribit_build_ws_connectionData("option", symbol="BTC", objective="oifunding", limit=1000)
        result =  d['sbmethod'](**d["sbPar"])
        print(result)
        #asyncio.run(example())

    @classmethod
    def test_htx_api(cls):
        print(cls.htx_fetch(instType="perpetual", objective="tta", symbol="BTC-USD"))

    @classmethod
    def test_htx_ws(cls):
        ht = cls.htx_build_api_connectionData("perpetual", "tta", "BTC-USD", 10)
        async def example():
            d = await ht["aiohttpMethod"]()
            print(d)
        asyncio.run(example())
    
    @classmethod
    def test_ws(cls):
        connData = htx.htx_build_ws_connectionData("perpetual", "depth", "BTC-USD")
        print(connData.get("kickoffMethod")())
        print(connData)

    @classmethod
    def test(cls):
        async def example():
            d = await cls.htx_aiohttpFetch_futureTrades()
            print(d)
        asyncio.run(example())

    @classmethod
    def test_mexc_ws(cls):
        connData = cls.mexc_build_ws_connectionData("spot", "depth", "BTCUSDT")
        print(connData["kickoffMethod"]())

    @classmethod
    def gate_test_api(cls):
        async def example():
            connData =  cls.gateio_build_api_connectionData("perpetual", "funding", "BTC_USDT", 100)
            r = await connData["aiohttpMethod"]()
            print(r)
        asyncio.run(example())

    @classmethod
    def gate_test_ws(cls):
        connData =  cls.gateio_build_ws_connectionData("option", "trades", "BTC_USDT")
        print(connData["kickoffMethod"]())
    #     asyncio.run(example())

    @classmethod
    def gate_option_msg(cls):
        print(cls.gateio_build_ws_message_all_Options("depth", "BTC_USDT"))

    @classmethod
    def binance_instruments(cls):
        async def example():
            data =  await cls.binance_build_fundfutureperp_method("BTC")
            print(data)
        asyncio.run(example())
        
    @classmethod
    def binance_ws(cls):
        data = cls.binance_build_ws_connectionData("perpetual", "trades", "BTCUSDT") #, special="perpfutureTrade")
        print(data)
        # print(data["1stBooksSnapMethod"]())
clientTest.binance_instruments()








