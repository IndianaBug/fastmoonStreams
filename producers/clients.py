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
from typing import List, Union
from utilis import filter_nested_dict

from exchangeinfo import *
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

    @classmethod
    async def make_wsRequest(cls, connection_data):
        async with websockets.connect(connection_data.get("endpoint"),  ssl=ssl_context) as websocket:
            await websocket.send(json.dumps(connection_data.get("headers")))
            response = await websocket.recv()
            return response 

    @classmethod
    def http_call(cls, endpoint, basepoint, payload, headers):
        conn = http.client.HTTPSConnection(endpoint)
        conn.request("GET", basepoint, payload, headers)
        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))

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
            special_methods : oioption oifutureperp posfutureperp
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
                "id_api" : f"binance_api_{insType}_{objective}_{connectionData.get('instrument')}",
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
    def binance_build_bulk_ws_message(cls, insTypes, objectives, symbols):
        message = {
            "method": "SUBSCRIBE", 
            "params": [], 
            "id": generate_random_integer(10)
        }
        print(insTypes, objectives, symbols)
        for i, o, s in zip(insTypes, objectives, symbols):
            payload = binance_ws_payload_map.get(i).get(o)(s)
            message["params"].append(payload)
        return message
 
    @classmethod
    def binance_build_ws_connectionData(cls, instTypes:list, objectives:list, symbols:list, needSnap=False, snaplimit=999,  **kwargs):
        """
            instType : spot, future, perpetual, option
                        Linear, Inverse for special methods
            needSnap and snap limit: you need to fetch the full order book, use these
            Example of snaping complete books snapshot : connectionData.get("sbmethod")(dic.get("instType"), connectionData.get("objective"), **connectionData.get("sbPar"))
        """       
        sss = [] 
        for ss in symbols:
            symbol_name = binance_get_symbol_name(ss)
            sss.append(symbol_name)
        marginType = binance_get_marginType(instTypes[0], symbols[0])
        endpoint = binance_ws_endpoints.get(instTypes[0]).get(marginType) if marginType != None else binance_ws_endpoints.get(instTypes[0])
        message = cls.binance_build_bulk_ws_message(instTypes, objectives, symbols)

            
        connection_data =     {
                                "type" : "ws",
                                "id_ws" : f"binance_ws_{'_'.join(instTypes)}_{'_'.join(objectives)}_{'_'.join(sss)}",
                                "exchange":"binance", 
                                "instrument": symbol_name,
                                "instType": '_'.join(instTypes),
                                "objective":'_'.join(objectives), 
                                "updateSpeed" : None,
                                "url" : endpoint,
                                "msg" : message,
                                "1stBooksSnapMethod" : None,
                                "marginType" : marginType
                            }
        
        if needSnap is True:
            connection_data["id_api"] = f"binance_api_{instTypes[0]}_{objectives[0]}_{sss[0]}",
            connection_data["1stBooksSnapMethod"] = partial(cls.binance_fetch, instTypes[0], objectives[0], symbols[0])
        return connection_data

class bybit(CommunicationsManager, bybitInfo):
    bybit_api_endpoint = bybit_api_endpoint
    bybit_api_category_map = bybit_api_category_map
    bybit_api_basepoints = bybit_api_basepoints
    bybit_api_params_map = bybit_api_params_map
    bybit_ws_endpoints = bybit_ws_endpoints
    bybit_ws_payload_map = bybit_ws_payload_map
    bybit_repeat_response_code = bybit_repeat_response_code

    @classmethod
    def bybit_buildRequest(cls, instType:str, objective:str, symbol:str, maximum_retries:int=10, books_dercemet:int=100, special_method=None, **kwargs)->dict: 
        """ 
            instType : "perpetual", "spot", "option", "future"
            objective : depth, gta, funding, oioption, oi
            Maxium retries of an API with different parameters in case API call is impossible. Useful when you cant catch the limit
            books_dercemet : the derement of books length in case of api call being unsuccessful. If applicable
            special_method: oifutureperp, posfutureperp, fundfutureperp
            **kwargs : request parameters
        """
        symbol_name = bybit_get_instrument_name(symbol)
        marginType = bybit_get_marginType(instType, symbol)
        category = bybit_api_category_map.get(instType).get(marginType) if marginType is not None else bybit_api_category_map.get(instType)
        params = bybit_api_params_map.get(instType).get(objective)(category, symbol) 
        endpoint = cls.bybit_api_endpoint
        basepoint = cls.bybit_api_basepoints.get(objective)
        url = f"{endpoint}{basepoint}"
        headers = {}
        return {
            "url" : url, 
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrument" : symbol_name,
            "insType" : instType,
            "exchange" : "bybit", 
            "repeat_code" : cls.bybit_repeat_response_code,
            "maximum_retries" : maximum_retries, 
            "books_dercemet" : books_dercemet,
            "marginType" : marginType,
            "special_method" : special_method,
            "payload" : ""
            }

    @classmethod
    def bybit_fetch(cls, *args, **kwargs):
        connection_data = cls.bybit_buildRequest(*args, **kwargs)
        response = cls.make_request(connection_data)
        return response

    @classmethod
    async def bybit_aiohttpFetch(cls, *args, **kwargs):
        connection_data = cls.bybit_buildRequest(*args, **kwargs)
        response = await cls.make_aiohttpRequest_v2(connection_data)
        return response

    @classmethod
    def bybit_build_api_connectionData(cls, instType:str, objective:str, symbol:str, pullTimeout:int, special_method:str=None,  **kwargs):
        """
            insType : depth, gta
            result = d['aiohttpMethod']()
            pullTimeout : how many seconds to wait before you make another call
        """
        instrument = bybit_get_instrument_name(symbol)
        # connectionData = cls.bybit_buildRequest(instType, objective, symbol, special_method, **kwargs)
        if special_method == "oifutureperp":
            call = partial(cls.bybit_build_oifutureperp_method, symbol)
        if special_method == "posfutureperp":
            call = partial(cls.bybit_build_posfutureperp_method, symbol)
        if special_method == "fundfutureperp":
            call = partial(cls.bybit_build_fundfutureperp_method, symbol)
        if special_method == None:
            call = partial(cls.bybit_aiohttpFetch, instType=instType, objective=objective, symbol=symbol)        
        data =  {
                "type" : "api",
                "id_api" : f"bybit_api_{instType}_{objective}_{instrument}",
                "exchange":"bybit", 
                "instrument": instrument,
                "instType": instType,
                "objective": objective, 
                "pullTimeout" : pullTimeout,
                # "connectionData" : connectionData,
                "aiohttpMethod" :call,
                }
        
        return data
    
    @classmethod
    def bybit_get_instruments_by_marginType(cls, instType, underlying_asset):
        info = cls.bybit_info(f"future.{instType}Future")
        symbols = [symbol["symbol"] for symbol in info if instType in symbol["contractType"] and underlying_asset in symbol["symbol"]]
        return symbols

    # oifutureperp, posfutureperp, fundfutureperp

    @classmethod
    async def bybit_build_oifutureperp_method(cls, underlying_asset):
        """
        "Linear", "Inverse"
        """
        full = {}
        symbols = cls.bybit_get_instruments_by_marginType("Linear", underlying_asset)
        for symbol in symbols:
            instType = "future" if "-" in symbol else "perpetual"
            data = await cls.bybit_aiohttpFetch(instType, "oi", symbol=symbol, special_method="oifutureperp")
            full[symbol] = data
        symbols = cls.bybit_get_instruments_by_marginType("Inverse", underlying_asset)
        for symbol in symbols:
            instType = "future" if "-" in symbol else "perpetual"
            data = await cls.bybit_aiohttpFetch(instType, "oi", symbol=symbol, special_method="oifutureperp")
            full[symbol] = data
        return full
        

    @classmethod
    async def bybit_build_posfutureperp_method(cls, underlying_asset):
        """
        "Linear", "Inverse"
        """
        full = {}
        symbols = cls.bybit_get_instruments_by_marginType("Linear", underlying_asset)
        for symbol in symbols:
            instType = "future" if "-" in symbol else "perpetual"
            data = await cls.bybit_aiohttpFetch(instType, "gta", symbol=symbol, special_method="posfutureperp")
            full[symbol] = data
        symbols = cls.bybit_get_instruments_by_marginType("Inverse", underlying_asset)
        for symbol in symbols:
            instType = "future" if "-" in symbol else "perpetual"
            data = await cls.bybit_aiohttpFetch(instType, "gta", symbol=symbol, special_method="posfutureperp")
            full[symbol] = data
        return full

    @classmethod
    async def bybit_build_fundfutureperp_method(cls, underlying_asset):
        """
        "Linear", "Inverse"
        """
        full = {}
        symbols = cls.bybit_get_instruments_by_marginType("Linear", underlying_asset)
        for symbol in symbols:
            instType = "future" if "-" in symbol else "perpetual"
            if instType == "perpetual":
                data = await cls.bybit_aiohttpFetch(instType, "funding", symbol=symbol, special_method="fundfutureperp")
                full[symbol] = data
        symbols = cls.bybit_get_instruments_by_marginType("Inverse", underlying_asset)
        for symbol in symbols:
            instType = "future" if "-" in symbol else "perpetual"
            if instType == "perpetual":
                data = await cls.bybit_aiohttpFetch(instType, "funding", symbol=symbol, special_method="fundfutureperp")
                full[symbol] = data
        return full

    @classmethod
    def bybit_build_ws_message(cls, symbol, instType, objective):
        arg = bybit_ws_payload_map.get(instType).get(objective)(symbol)
        msg = {
            "req_id": generate_random_id(10), 
            "op": "subscribe",
            "args": [arg]
        }
        return msg

    @classmethod
    def bybit_build_bulk_ws_message(cls, instTypes, objectives, symbols):
        msg = {
            "req_id": generate_random_id(10), 
            "op": "subscribe",
            "args": []
        }
        for s, i, obj in zip(symbols, instTypes, objectives):
            arg = bybit_ws_payload_map.get(i).get(obj)(s)
            msg["args"].append(arg)
        return msg



    @classmethod
    def bybit_build_ws_connectionData(cls, instTypes, objectives, symbols, needSnap=False, snaplimit=1000, special_method=None, **kwargs):
        """
            insType : spot, perpetual, future, option, Linear, Inverse (for special methods)
            needSnap and snap limit: you need to fetch the full order book, use these
            special_method : perpfutureTrades, perpfutureLiquidations
        """
        symbol_names = [bybit_get_instrument_name(symbol) for symbol in symbols]
        marginType = bybit_get_marginType(instTypes[0], symbols[0])
        url = bybit_ws_endpoints.get(instTypes[0]).get(marginType) if marginType != None else bybit_ws_endpoints.get(instTypes[0])
        msg = cls.bybit_build_bulk_ws_message(instTypes, objectives, symbols)

        connection_data =     {
                                "type" : "ws",
                                "id_ws" : f"bybit_ws_{instTypes[0]}_{objectives[0]}_{symbol_names[0]}",
                                "exchange":"bybit", 
                                "instrument": "".join(symbol_names),
                                "instType": "".join(instTypes),
                                "objective":"".join(objectives), 
                                "updateSpeed" : None,
                                "url" : url,
                                "msg" : msg,
                                "1stBooksSnapMethod" : None,
                                "marginType" : marginType
                            }
        
        if needSnap is True:
            connection_data["id_api"] = f"bybit_api_{instTypes[0]}_{objectives[0]}_{symbol_names[0]}",
            connection_data["1stBooksSnapMethod"] = partial(cls.bybit_fetch, instType=instTypes[0], objective=objectives[0], symbol=symbols[0])
        return connection_data
        
class okx(CommunicationsManager, okxInfo):
    """
        OKX apis and websockets wrapper
    """
    okx_repeat_response_code = okx_repeat_response_code
    okx_api_endpoint = okx_api_endpoint
    okx_api_instType_map = okx_api_instType_map
    okx_api_basepoints = okx_api_basepoints
    okx_api_params_map = okx_api_params_map
    okx_ws_endpoint = okx_ws_endpoint
    okx_ws_objective_map = okx_ws_objective_map

    @classmethod
    def okx_buildRequest(cls, instType:str, objective:str, symbol:str, maximum_retries:int=10, books_dercemet:int=100, **kwargs)->dict: 
        """
            objective :  gta oifutperp oioption funding depth, 
            instType is symbolic
        """
        symbol_name = okx_get_instrument_name(symbol)
        endpoint = cls.okx_api_endpoint
        basepoint = cls.okx_api_basepoints.get(objective)
        url = f"{endpoint}{basepoint}"
        instTypeOKX = okx_api_instType_map.get(instType)
        params = cls.okx_api_params_map.get(objective)(symbol) if objective != "oi" else cls.okx_api_params_map.get(objective)(instTypeOKX, symbol)
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
            "exchange" : "okx", 
            "repeat_code" : cls.okx_repeat_response_code,
            "maximum_retries" : maximum_retries, 
            "books_dercemet" : books_dercemet,
            "marginType" : "any",
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
    async def okx_build_fundfutureperp_method(cls, underlying_symbol):
        symbols = [x for x in info.okx_symbols_by_instType("perpetual") if underlying_symbol in x]
        data = {}
        for symbol in symbols:
            response = await cls.okx_aiohttpFetch("perpetual", "funding", symbol)
            data["symbol"] = response
        return data
    
    @classmethod
    async def okx_build_oifutureperp_method(cls, underlying_symbol):
        marginCoinsF = [x for x in cls.okx_symbols_by_instType("future") if underlying_symbol in x]
        marginCoinsF = list(set([x.split("-")[1] for x in marginCoins]))
        marginCoinsP = [x for x in cls.okx_symbols_by_instType("perpetual") if underlying_symbol in x]
        marginCoinsP = list(set([x.split("-")[1] for x in marginCoins]))
        data = []
        for marginCoin in marginCoinsF:
            futures = await cls.okx_aiohttpFetch("future", "oi", f"{underlying_symbol}-{marginCoin}")
            data.append(futures)
        for marginCoin in marginCoinsP:
            perp = await cls.okx_aiohttpFetch("perpetual", "oi", f"{underlying_symbol}-{marginCoin}")
            data.append(perp)
        return data

    @classmethod
    async def okx_build_oioption_method(cls, underlying_symbol):
        marginCoinsF = [x for x in cls.okx_symbols_by_instType("option") if underlying_symbol in x]
        marginCoinsF = list(set([x.split("-")[1] for x in marginCoins]))
        data = []
        for marginCoin in marginCoinsF:
            futures = await cls.okx_aiohttpFetch("option", "oi", f"{underlying_symbol}-{marginCoin}")
            data.append(futures)
        return data

    @classmethod
    def okx_build_api_connectionData(cls, instType:str, objective:str, symbol:str, pullTimeout:int, special_method:str=None, **kwargs):
        """
            objective :  gta oi oioption funding depth
            instType is symbolic
            special_method : fundfutureperp
        """
        connectionData = cls.okx_buildRequest(instType, objective, symbol, **kwargs)
        if special_method == None:
            call = partial(cls.okx_aiohttpFetch, instType=instType, objective=objective, symbol=symbol)
        if special_method == "fundfutureperp":
            call = partial(cls.okx_build_fundfutureperp_method, underlying_symbol=symbol)
        if special_method == "oifutureperp":
            call = partial(cls.okx_build_oifutureperp_method, underlying_symbol=symbol)
        data =  {
                "type" : "api",
                "id_api" : f"okx_api_{instType}_{objective}_{connectionData.get('instrument')}",
                "exchange":"okx", 
                "instrument": connectionData.get('instrument'),
                "instType": instType,
                "objective": objective, 
                "pullTimeout" : pullTimeout,
                "connectionData" : connectionData,
                "aiohttpMethod" : call,
                }
        
        return data

    
    @classmethod
    def okx_build_ws_message(cls, objective, instType=None, instFamily=None, symbol=None):
        msg = {
                "op": "subscribe",
                "args": [{
                    "channel": objective,
                }]
            }
        if instType != None:
            parsef_instType = okx_api_instType_map.get(instType)
            msg["args"][0]["instType"] = parsef_instType
        if instFamily != None:
            msg["args"][0]["instFamily"] = instFamily
        if symbol != None:
            msg["args"][0]["instId"] = symbol
        return msg

    @classmethod
    def okx_build_bulk_ws_message(cls, objectives, instTypes, instFamilys, symbols):
        msg = {
                "op": "subscribe",
                "args": []
            }
        for o, it, iff, s in zip(objectives, instTypes, instFamilys, symbols):
            parsed_objective = okx_ws_objective_map.get(o)
            m = cls.okx_build_ws_message(parsed_objective, it, iff, s)
            msg["args"].append(m.get("args")[0])
        return msg

    @classmethod
    def okx_build_ws_connectionData(cls, instTypes, objectives, symbols, needSnap=False, snaplimit=1000, **kwargs):
        """
            You do not need to fetch ordeBook with okx websockets, it's done upon connection
            objective : liquidations trades depth oi funding optionTrades
            "though websockket of depth fetches first snapshot, its better to manually fetch the firstDEpth
        """
        symbol_names = [okx_get_instrument_name(symbol) for symbol in symbols]
        endpoint = cls.okx_ws_endpoint
        
        parsed_instTypes = []
        parsed_instFamilys = []
        parsed_symbols = []
        
        for i, o, s in zip(instTypes, objectives, symbols):
            if o == "liquidations":
                parsed_instTypes.append(i)
                parsed_instFamilys.append(None)
                parsed_symbols.append(None)
            if o == "optionTrades":
                parsed_instTypes.append(i)
                parsed_instFamilys.append(s)
                parsed_symbols.append(None)
            else:
                parsed_instTypes.append(None)
                parsed_instFamilys.append(None)
                parsed_symbols.append(s)
        
        message = cls.okx_build_bulk_ws_message(objectives, parsed_instTypes, parsed_instFamilys, parsed_symbols)
                
            
        
        connection_data =     {
                                "type" : "ws",
                                "id_ws" : f"okx_ws_{instTypes[0]}_{objectives[0]}_{symbol_names[0]}",
                                "exchange":"okx", 
                                "instrument": "_".join(symbol_names),
                                "instType": "_".join(instTypes),
                                "objective":"_".join(objectives), 
                                "updateSpeed" : None,
                                "url" : endpoint,
                                "msg" : message,
                                "1stBooksSnapMethod" : None
                            }
        if needSnap == True:
            connection_data["1stBooksSnapMethod"] = partial(cls.okx_fetch, instType=instTypes[0], objective=objectives[0], symbol=symbols[0])
        return connection_data

class coinbase(CommunicationsManager):
    """
        Abstraction of bybit api calls
    """

    def __init__ (self, api_coinbase, secret_coinbase):
        self.api_coinbase = api_coinbase
        self.secret_coinbase = secret_coinbase
        self.coinbase_repeat_response_code = coinbase_repeat_response_code
        self.coinbase_api_product_types_map = coinbase_api_product_types_map
        self.coinbase_api_endpoint = coinbase_api_endpoint
        self.coinbase_api_basepoints = coinbase_api_basepoints
        self.coinbase_ws_endpoint = coinbase_ws_endpoint
        self.coinbase_stream_keys = coinbase_stream_keys
        self.coinbase_payload = ''

    def coinbase_buildRequest(self, instType:str, objective:str, symbol : str, maximum_retries:int=10, books_dercemet:int=100, **kwargs)->dict: 
        """
            do not pass argument product_type
            omit maximum_retries and books_dercemet as coinbase handles it for you :)
            instType : spot, perpetual
        """
        params = {}
        product_type = coinbase_api_product_types_mapv2.get(instType)
        params["product_type"] = product_type
        params["product_id"] = symbol
        symbol = coinbase_get_symbol_name(params["product_id"])
        endpoint = self.coinbase_api_endpoint
        basepoint = self.coinbase_api_basepoints.get(objective)
        url = endpoint+basepoint
        payload = ''
        headers = self.coinbase_build_headers(basepoint)
        return {
            "url" : url,
            "endpoint" : endpoint, 
            "basepoint" : basepoint,
            "objective" : objective,
            "params" : params, 
            "headers" : headers, 
            "instrumen" : symbol,
            "insType" : instType, 
            "exchange" : "coinbase", 
            "repeat_code" : self.coinbase_repeat_response_code,
            "maximum_retries" : maximum_retries, 
            "books_dercemet" : books_dercemet,
            "payload" : payload
            }

    def coinbase_build_api_connectionData(self, instType:str, objective:str, symbol:str, pullTimeout:int, **kwargs):
        """
            insType : perpetual, spot, future, option
            objective : oi, gta
            **kwargs - those in okx ducumentations
            pullTimeout : how many seconds to wait before you make another call
            How to call : result = d['aiohttpMethod'](**kwargs)
            books don't work with aiohttp, only with http request method
        """
        connectionData = self.coinbase_buildRequest(instType, objective, symbol, **kwargs)
        symbol_name = coinbase_get_symbol_name(connectionData["instrumen"])
        data =  {
                "type" : "api",
                "id_ws" : f"coinbase_api_{instType}_{objective}_{symbol_name}",
                "exchange":"coinbase", 
                "instrument": symbol_name,
                "instType": instType,
                "objective": objective, 
                "pullTimeout" : pullTimeout,
                "connectionData" : connectionData,
                "aiohttpMethod" : partial(self.coinbase_aiohttpFetch, instType=instType, symbol=symbol, objective=objective),
                }
        
        return data

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
        for key in self.coinbase_api_product_types_map.keys():
            symbols = self.coinbase_symbols_by_instType(key)
            d[key] = symbols
        return d

    def coinbase_info(self, instType):
        """
            spot, future
        """
        basepoint = f"{self.coinbase_api_basepoints.get('info')}?{self.coinbase_api_product_types_map.get(instType)}"
        headers = self.coinbase_build_headers(self.coinbase_api_basepoints.get('info'))
        return self.http_call(self.coinbase_api_endpoint, basepoint, self.coinbase_payload, headers).get("products")
    
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

    def coinbase_build_ws_method(self, instType, objective:str, symbol:str, **kwargs):
        """
            objective : trades, depth
        """
        params = {}
        params["product_id"] = symbol
        channel = self.coinbase_stream_keys.get(objective)
        message =  {
                "type": "subscribe",
                "product_ids": [params["product_id"]],
                "channel": channel,
                "jwt": self.build_jwt(),
                "timestamp": int(time.time())
            }     

        return message, instType, objective   

    def coinbase_build_ws_connectionData(self, instType, objective:str, symbol:str, needSnap=False, snaplimit=1000, **kwargs):
        """
            insType : spot, future
            snapLimit. Coinbase manages it for you :)
            for books, needSnap should be = True
            **kwargs : only product_id, instrument type is handled automatically
        """
        message, instType, objective = self.coinbase_build_ws_method(instType, objective, symbol)
        symbol_name = coinbase_get_symbol_name(symbol)
        endpoint = coinbase_ws_endpoint    
        connection_data =     {
                                "type" : "ws",
                                "id_ws" : f"coinbase_ws_{instType}_{objective}_{symbol_name}",
                                "exchange":"coinbase", 
                                "instrument": symbol_name,
                                "instType": instType,
                                "objective":objective, 
                                "updateSpeed" : None,
                                "url" : endpoint,
                                "msg" : message,
                                "1stBooksSnapMethod" : None
                            }
        if needSnap is True:
            connection_data["id_api"] = f"coinbase_api_{instType}_{objective}_{symbol_name}",
            connection_data["1stBooksSnapMethod"] = partial(self.coinbase_fetch, instType, objective, symbol)
        return connection_data

class kucoin(CommunicationsManager, kucoinInfo):
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


    def kucoin_buildRequest(self, instType:str, objective:str, symbol:str, maximum_retries:int=10, books_dercemet:int=100, **kwargs)->dict: 
        """
            instType : spot, perpetual
            objective :  depth, oifunding
            omit maximum_retries and books_dercemet, kucoin handles it for you
            **kwargs : request parameters, check kucoin API docs
        """
        params = {}
        params["symbol"] = symbol
        symbol_name = kucoin_get_symbol_name(params["symbol"])
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
            "instrument" : symbol_name,
            "insType" : instType, 
            "exchange" : "kucoin", 
            "repeat_code" : self.kucoin_repeat_response_code,
            "maximum_retries" : maximum_retries, 
            "books_dercemet" : books_dercemet,
            "payload" : payload
            }
    
    def kucoin_build_ws_method(self, instType, objective:str, symbol:str, **kwargs):
        """
            objective : depth, trades, liquidations, oi, funding
        """
        topic = self.kucoin_stream_keys.get(instType).get(objective)
        message =  {
                "id": generate_random_integer(10),   
                "type": "subscribe",
                "topic": f"{topic}{symbol}",
                "response": True
                }

        return message 
    
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

    def kucoin_build_ws_connectionData(self, instType, objective:str, symbol:str, needSnap=False, snaplimit=1000, **kwargs):
        """
            insType : spot, perpetual
            needSnap = True for books
            omit snap limit
            for books, needSnap should be = True
            **kwargs : only product_id, instrument type is handled automatically
        """
        symbol_name = kucoin_get_symbol_name(symbol)
        message  = self.kucoin_build_ws_method(instType, objective, symbol)
        symbol_name = kucoin_get_symbol_name(symbol)
        endpoint = self.build_kucoin_ws_endpoint()    
        connection_data =     {
                                "type" : "ws",
                                "id_ws" : f"kucoin_ws_{instType}_{objective}_{symbol_name}",
                                "exchange":"kucoin", 
                                "instrument": symbol_name,
                                "instType": instType,
                                "objective":objective, 
                                "updateSpeed" : None,
                                "url" : endpoint,
                                "msg" : message,
                                "1stBooksSnapMethod" : None
                            }
        if needSnap is True:
            connection_data["id_api"] = f"kucoin_api_{instType}_{objective}_{symbol_name}",
            connection_data["1stBooksSnapMethod"] = partial(self.kucoin_fetch, instType, objective, symbol)
        return connection_data

    def kucoin_build_api_connectionData(self, instType:str, objective:str, symbol, pullTimeout:int, **kwargs):
        """
            insType : perpetual, spot, future, option
            objective : oi, gta
            **kwargs - those in okx ducumentations
            pullTimeout : how many seconds to wait before you make another call
            How to call : result = d['aiohttpMethod'](**kwargs)
            books don't work with aiohttp, only with http request method
        """
        connectionData = self.kucoin_buildRequest(instType, objective, symbol, **kwargs)
        symbol_name = kucoin_get_symbol_name(symbol)
            
        data =  {
                "type" : "api",
                "id_api" : f"kucoin_api_{instType}_{objective}_{symbol_name}",
                "exchange":"kucoin", 
                "instrument": symbol_name,
                "instType": instType,
                "objective": objective, 
                "pullTimeout" : pullTimeout,
                "connectionData" : connectionData,
                "aiohttpMethod" : partial(self.kucoin_aiohttpFetch, instType=instType, objective=objective, symbol=symbol),
                }
        
        return data
    
class bingx(CommunicationsManager, bingxInfo):

    def __init__ (self, api_bingx="", secret_bingx=""):
        self.api_bingx = api_bingx
        self.secret_bingx = secret_bingx
        self.bingx_api_endpoint = bingx_api_endpoint
        self.bingx_api_basepoints = bingx_api_basepoints
        self.bingx_ws_endpoints = bingx_ws_endpoints
        self.bingx_stream_keys = bingx_stream_keys
        self.bingx_repeat_response_code = bingx_repeat_response_code


    def bingx_buildRequest(self, instType:str, objective:str, symbol:str,
                     possible_limits:list=[1000, 500, 100, 50, 20, 10, 5], books_dercemet:int=100, **kwargs)->dict: 
        """
            instType : spot, perpetual
            objective :  depth, funding, oi
            Maxium retries of an API with different parameters in case API call is impossible. Useful when you cant catch the limit
            books_dercemet : the derement of books length in case of api call being unsuccessful. If applicable
            **kwargs : request parameters like symbol
        """
        params = bingx_pi_param_map.get(objective)(symbol)
        symbol_name = bingx_get_symbol_name(symbol)
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
            "instrument" : symbol_name,
            "insType" : instType, 
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

    def bingx_build_api_connectionData(self, instType:str, objective:str, symbol:str, pullTimeout:int, **kwargs):
        """
            insType : perpetual, spot, future, option
            objective : oi, gta
            **kwargs - those in okx ducumentations
            pullTimeout : how many seconds to wait before you make another call
            How to call : result = d['aiohttpMethod'](**kwargs)
            books don't work with aiohttp, only with http request method
        """
        connectionData = self.bingx_buildRequest(instType, objective, symbol)
        symbol_name = bingx_get_symbol_name(symbol)
            
        data =  {
                "type" : "api",
                "id_api" : f"bingx_api_{instType}_{objective}_{symbol_name}",
                "exchange":"bingx", 
                "instrument": symbol_name,
                "instType": instType,
                "objective": objective, 
                "pullTimeout" : pullTimeout,
                "connectionData" : connectionData,
                "aiohttpMethod" : partial(self.bingx_aiohttpFetch, instType=instType, objective=objective, symbol=symbol),
                }
        
        return data

    def build_bingx_ws_message(self, instType, objective, symbol):
        channel = bingx_stream_keys.get(instType).get(objective)
        msg =  {"id":generate_random_id(20),
                "reqType": "sub",
                "dataType":f"{symbol}@{channel}"} 
        return msg
    
    def bingx_build_ws_connectionData(self, instType, objective, symbol, needSnap=False, snaplimit=1000, **kwargs):
        """
            insType : spot, perpetual
            omit snap limit, needSnap
            **kwargs : symbol, objective, pullSpeed
        """
        message  = self.build_bingx_ws_message(instType, objective, symbol)
        symbol_name = bingx_get_symbol_name(symbol)
        endpoint = self.bingx_ws_endpoints.get(instType)  
        connection_data =     {
                                "type" : "ws",
                                "id_ws" : f"bingx_ws_{instType}_{objective}_{symbol_name}",
                                "exchange":"bingx", 
                                "instrument": symbol_name,
                                "instType": instType,
                                "objective":objective, 
                                "updateSpeed" : None,
                                "url" : endpoint,
                                "msg" : message,
                                "sbmethod" : None
                            }
        return connection_data

class bitget(CommunicationsManager, bitgetInfo):
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
    def bitget_buildRequest(cls, instType:str, objective:str, symbol:str, maximum_retries:int=10, books_dercemet:int=100, **kwargs)->dict: 
        """
            objective :  depth, oi, funding
        """
        symbol_name = bitget_get_symbol_name(symbol)
        marginType = bitget_get_marginType(symbol)
        marginCoin = bitget_get_marginCoin(symbol)
        productType = bitget_get_productType(instType, marginType, marginCoin)
        params = bitget_api_params_map.get(instType).get(objective)(symbol, productType)
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
            "instrument" : symbol_name, 
            "insType" : instType, 
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
    async def bitget_build_oifutureperp_method(cls, underlying_asset):
        """
            BTC, ETH ...
        """
        symbols =  [x for x in bitgetInfo.bitget_symbols_by_instType("perpetual") if underlying_asset in x]
        full = []
        for symbol in symbols:
            data = await cls.bitget_aiohttpFetch("perpetual", "oi", symbol=symbol, special_method="oifutureperp")
            full.append(data)
        return full
    
    @classmethod
    async def bitget_build_fundfutureperp_method(cls, underlying_asset):
        """
            BTC, ETH ...
        """
        symbols =  [x for x in bitgetInfo.bitget_symbols_by_instType("perpetual") if underlying_asset in x]
        full = []
        for symbol in symbols:
                data = await cls.bitget_aiohttpFetch("perpetual", "funding", symbol=symbol, special_method="fundfutureperp")
                full.append(data)
        return full


    @classmethod
    def bitget_build_api_connectionData(cls, instType:str, objective:str, symbol:str, pullTimeout:int, special_method=False, **kwargs):
        """
            insType : perpetual, spot
            objective : depth
            **kwargs - those in okx ducumentations
            pullTimeout : how many seconds to wait before you make another call
            How to call : result = d['aiohttpMethod'](**kwargs)
            books don't work with aiohttp, only with http request method
        """
        # connectionData = cls.bitget_buildRequest(instType, objective, symbol)
        if special_method == False:
            call =  partial(cls.bitget_aiohttpFetch, instType=instType, objective=objective, symbol=symbol)
        if  special_method == "fundfutureperp":   
            call = partial(cls.bitget_build_fundfutureperp_method, symbol)  
        if  special_method == "oifutureperp":   
            call = partial(cls.bitget_build_oifutureperp_method, symbol)  
        data =  {
                "type" : "api",
                "id_api" : f"bitget_api_{instType}_{objective}_{symbol}",
                "exchange":"bitget", 
                "instrument": symbol,
                "instType": instType,
                "objective": objective, 
                "pullTimeout" : pullTimeout,
                "aiohttpMethod" : call,
                "special_method" : special_method
                }
        
        return data

    @classmethod
    def bitget_build_ws_message(cls, objective, symbol, productType):
        msg = {
        "op": "subscribe",
        "args": [
            {
                "instType": productType,
                "channel": bitget_stream_keys.get(objective),
                "instId": symbol
                    }
                ]
            }
        return msg

    @classmethod
    def bitget_build_bulk_ws_message(cls,  objectives, symbols, productTypes):
        """
            marginType and marginCoin must be passed
        """
        full = {
        "op": "subscribe",
        "args": []
            }        
        for objective, symbol, productType in zip(objectives, symbols, productTypes):
            arg = cls.bitget_build_ws_message(objective, symbol, productType)["args"][0]
            full["args"].append(arg)
        return full
            
    
    @classmethod    
    def bitget_build_ws_connectionData(cls, instTypes:list, objectives:list, symbols:list, needSnap=False, snaplimit=None, **kwargs):
        """
            insType : spot, perpetual
            omit snap limit, needSnap
            **kwargs : symbol, objective, pullSpeed (if applicable) Inspect bitget API docs
        """
        productTypes = []
        marginCoins = []
        marginTypes = []
        for instType, objective, symbol in zip(instTypes, objectives, symbols):
            symbol_name = bitget_get_symbol_name(symbol)
            marginType = bitget_get_marginType(symbol)
            marginCoin = bitget_get_marginCoin(symbol)
            productType = bitget_get_productType(instType, marginType, marginCoin)
            productTypes.append(productType)
            marginCoins.append(marginCoin)
            marginTypes.append(marginType)
        message  = cls.bitget_build_bulk_ws_message(objectives, symbols, productTypes)
        endpoint = cls.bitget_ws_endpoint
        connection_data =     {
                                "type" : "ws",
                                "id_ws" : f"bitget_ws_{instType}_{'_'.join(objectives)}_{symbol_name}",
                                "exchange":"bitget", 
                                "instrument": '_'.join(symbols),
                                "instType": instType,
                                "objective":'_'.join(objectives), 
                                "updateSpeed" : None,
                                "url" : endpoint,
                                "msg" : message,
                                "1stBooksSnapMethod" : None,
                                "marginCoin" : '_'.join(marginCoins),
                                "marginType" : '_'.join(marginTypes),
                            }
        if needSnap is True:
            connection_data["id_api"] = f"bitget_api_{instType}_{objectives[0]}_{symbol_name}"
            connection_data["1stBooksSnapMethod"] = partial(cls.bitget_fetch, instTypes[0], objectives[0], symbols[0])
        return connection_data

class deribit(CommunicationsManager, deribitInfo):
    """
        Abstraction of bybit api calls
    """
    deribit_repeat_response_code = deribit_repeat_response_code
    deribit_endpoint = deribit_endpoint
    deribit_marginCoins = deribit_marginCoins
    deribit_jsonrpc_params_map = deribit_jsonrpc_params_map
    deribit_jsonrpc_channel_map = deribit_jsonrpc_channel_map
    deribit_instType_map = deribit_instType_map

    @classmethod
    def deribit_buildRequest(cls, instType:str, objective:str, symbol:str, maximum_retries:int=10, books_dercemet:int=100, **kwargs)->dict: 
        """
            instType : spot, perpetual, future, option
            objective : depth, oi. Please check available methods by exchange
            **kwargs : see the deribit api docs for params. They are identical
            ** you may use limit instead of depth argument if you need to snap orderbooks
            omit maximum_retries and books_dercemet as deribit handles this for you
        """
        symbol_name = deribit_get_symbol_name(symbol)
        kind = deribit_instType_map.get(instType)
        params = deribit_jsonrpc_params_map.get(objective)(symbol, kind)
        channel = deribit_jsonrpc_channel_map.get(objective)
        msg = cls.deribit_build_jsonrpc_msg(channel, params)
        endpoint = cls.deribit_endpoint
        return {
            "endpoint" : endpoint,  
            "objective" : objective,
            "params" : params, 
            "headers" : msg, 
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
        response = cls.make_wsRequest(connection_data)
        return response

    @classmethod
    async def deribit_aiohttpFetch(cls, *args, **kwargs):
        connection_data = cls.deribit_buildRequest(*args, **kwargs)
        response = await cls.make_wsRequest(connection_data)
        return response
    
    @classmethod
    def deribit_build_jsonrpc_msg(cls, channel, params):
        msg = {
                "jsonrpc": "2.0", 
                "id": generate_random_integer(10),
                "method": channel,
                "params": params
                }
        return msg

    @classmethod
    def deribit_build_bulk_jsonrpc_msg(cls, channel, paramss):
        full = {
                "jsonrpc": "2.0", 
                "id": generate_random_integer(10),
                "method": channel,
                "params": {"channels" : []}
        }
        if channel == "heartbeats":
            full = {
                    "jsonrpc": "2.0", 
                    "id": generate_random_integer(10),
                    "method": "/public/set_heartbeat",
                    "params": {"interval" : 5}
            }
        if channel != "heartbeats":
            for par in paramss:
                msg = cls.deribit_build_jsonrpc_msg(channel, par)
                full["params"]["channels"].append(msg["params"]["channels"])
        return full

    @classmethod
    def deribit_build_api_connectionData(cls, instType:str, objective:str, symbol:str, pullTimeout:int, **kwargs):
        """
            insType : perpetual, spot, future, option
            objective : oifunding, depth
            **kwargs - those in deribit ducumentations
            pullTimeout : how many seconds to wait before you make another call
        """
        symbol_name = kucoin_get_symbol_name(symbol) 
        data =  {
                "type" : "api",
                "id_api" : f"deribit_api_{instType}_{objective}_{symbol_name}",
                "exchange":"deribit", 
                "instrument": symbol_name,
                "instType": instType,
                "objective": objective, 
                "pullTimeout" : pullTimeout,
                "aiohttpMethod" : partial(cls.deribit_aiohttpFetch, instType=instType, objective=objective, symbol=symbol),
                }
        
        return data

    @classmethod
    def deribit_build_ws_connectionData(cls, instTypes:list, objectives:list, symbols:list, needSnap=False, snaplimit=1000, **kwargs):
        """
            insType : spot, perpetual
            needSnap = True for books
            for books, needSnap should be = True if you for depth websocket
            **kwargs : symbol, objective, pullSpeed (if applicable)
        """
        paramsss = []
        for i, k, s in zip(instTypes, objectives, symbols):
            symbol_name = deribit_get_symbol_name(s)
            kind = deribit_instType_map.get(i)
            params = deribit_ws_params_map.get(k)(s, kind)
            paramsss.append(params)
        channel = deribit_jsonrpc_channel_map.get("ws")
        msg = cls.deribit_build_bulk_jsonrpc_msg(channel, paramsss)
        connection_data =     {
                                "type" : "ws",
                                "id_ws" : f"deribit_ws_{'_'.join(instTypes)}_{'_'.join(objectives)}_{symbol_name}",
                                "exchange":"deribit", 
                                "instrument": symbol_name,
                                "instType": '_'.join(objectives),
                                "objective":'_'.join(objectives), 
                                "updateSpeed" : None,
                                "url" : deribit_endpoint,
                                "msg" : msg,
                                "1stBooksSnapMethod" : None
                            }
        if needSnap is True:
            connection_data["id_api"] = f"deribit_api_{'_'.join(instTypes)}_{'_'.join(objectives)}_{symbol_name}",
            connection_data["1stBooksSnapMethod"] = partial(cls.deribit_fetch, instTypes[0], objectives[0], symbols[0]) 
        return connection_data

class htx(CommunicationsManager, htxInfo):
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
            special : oifutureperp, depthfutureperp, tradesfutureperp
        """
        # connectionData = cls.htx_buildRequest(instType, objective, symbol, **kwargs)
        symbol_name = htx_symbol_name(symbol)
        
        if special == "depthfutureperp":
            call = partial(cls.htx_aiohttpFetch_futureDepth)
        if special == "oifutureperp":
            call = partial(cls.htx_aiohttpFetch_futureOI)
        if special == "tradesfutureperp":
            call = partial(cls.htx_aiohttpFetch_futureTrades)
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

class mexc(CommunicationsManager, mexcInfo):
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