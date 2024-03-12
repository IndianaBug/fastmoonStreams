import asyncio
import websockets
import json
import time
from urllib.parse import urlencode
import requests
import websockets
import ssl
from hashlib import sha256
import json
import jwt
from cryptography.hazmat.primitives import serialization
import secrets
import os
import sys
import hashlib
import hmac
import base64
import random
import string
import aiohttp
from utilis import generate_random_id



class pingspongs():
    """
        Handles pings pongs of websockets connections
    """

    def __init__ (self, intervals = {
        "binance" : 30,    # 1o minutes https://binance-docs.github.io/apidocs/spot/en/#rolling-window-price-change-statistics
        "bybit" : 20,        # 20 seconds https://bybit-exchange.github.io/docs/v5/ws/connect, https://bybit-exchange.github.io/docs/v5/ws/connect
        "okx" : 20,           # less than 30 seconds https://www.okx.com/docs-v5/en/#overview-websocket-overview
        "deribit" : 30,        # not less than 10 https://docs.deribit.com/#private-logout
        "kucoin" : 1,          # https://docs.deribit.com/#private-logout . The logic is differnt You have to answer to the websocket channel response /public/set_heartbeat
        "bitget" : 1,
        "bingx" : 1,
        "mexc" : 1, 
        "gateio" : 1,
        "htx" : 1,
        "coinbase" : None # Uses websocket heartbeat stream to keep the connection alive
    }) :
        """
            Intervals are in seconds
        """
        self.intervals = intervals
    

    async def binance_keep_alive(self, websocket :dict, data : dict=None):
        exchange = data.get("exchange", None)
        insType = data.get("exchange", None)
        instrument = data.get("instrument", None)
        while True:
            try:
                await websocket.pong()
                await asyncio.sleep(self.intervals.get("binance"))
            except websockets.exceptions.ConnectionClosed:
                if exchange != None:
                    print(f"Connection closed of {exchange}, {insType}, {instrument}. Stopping keep-alive.")
                else:
                    print(f"Connection closed of Binance stream. Stopping keep-alive.")

    async def bybit_keep_alive(self, websocket, conn_id=None, data=None):
        """
            The id of the websocket connection
            connection id is optional
        """
        exchange = data.get("exchange", None)
        insType = data.get("exchange", None)
        instrument = data.get("instrument", None)
        if conn_id != None:
            ping_dict = {"op": "ping"}
        else:
            ping_dict = {"req_id": conn_id, "op": "ping"}
        while True:
            try:
                await websocket.send(json.dumps(ping_dict))  
                await asyncio.sleep(self.intervals.get("bybit"))
            except websockets.exceptions.ConnectionClosed:
                if exchange != None:
                    print(f"Connection closed of {exchange}, {insType}, {instrument}. Stopping keep-alive.")
                else:
                    print(f"Connection closed of Bybit stream. Stopping keep-alive.")


    async def okx_keep_alive(self, websocket, data=None):
        exchange = data.get("exchange", None)
        insType = data.get("exchange", None)
        instrument = data.get("instrument", None)
        while True:
            try:
                await websocket.send('ping')
                await asyncio.sleep(self.intervals.get("okx"))
            except websockets.exceptions.ConnectionClosed:
                if exchange != None:
                    print(f"Connection closed of {exchange}, {insType}, {instrument}. Stopping keep-alive.")
                else:
                    print(f"Connection closed of OKX stream. Stopping keep-alive.")

    async def deribit_keep_alive(self, websocket, conn_id, data=None):
        """
            conn_id : The id that was sent in the request
        """
        exchange = data.get("exchange", None)
        insType = data.get("exchange", None)
        instrument = data.get("instrument", None)
        while True:
            try:
                await websocket.send(json.dumps({"jsonrpc":"2.0", "id": conn_id, "method": "/api/v2/public/test"}))
                await asyncio.sleep(self.intervals.get("deribit"))
            except websockets.exceptions.ConnectionClosed:
                if exchange != None:
                    print(f"Connection closed of {exchange}, {insType}, {instrument}. Stopping keep-alive.")
                else:
                    print(f"Connection closed of Deribit stream. Stopping keep-alive.")

    async def bitget_keep_alive(self, websocket, data=None):
        exchange = data.get("exchange", None)
        insType = data.get("exchange", None)
        instrument = data.get("instrument", None)
        while True:
            try:
                await websocket.send("ping")
                await asyncio.sleep(self.intervals.get("bitget"))
            except websockets.exceptions.ConnectionClosed:
                if exchange != None:
                    print(f"Connection closed of {exchange}, {insType}, {instrument}. Stopping keep-alive.")
                else:
                    print(f"Connection closed of Bitget stream. Stopping keep-alive.")

    async def bingx_keep_alive(self, websocket, data=None):
        exchange = data.get("exchange", None)
        insType = data.get("exchange", None)
        instrument = data.get("instrument", None)
        while True:
            try:
                await asyncio.sleep(self.intervals.get("bingx") )
                await websocket.send("Pong")  
            except websockets.exceptions.ConnectionClosed:
                if exchange != None:
                    print(f"Connection closed of {exchange}, {insType}, {instrument}. Stopping keep-alive.")
                else:
                    print(f"Connection closed of Bingx stream. Stopping keep-alive.")

    async def kucoin_keep_alive(self, websocket, conn_id, data=None):
        """
            conn_id : id of the deribit stream with which the websocket was initiated
        """
        exchange = data.get("exchange", None)
        insType = data.get("exchange", None)
        instrument = data.get("instrument", None)
        while True:
            try:
                await asyncio.sleep(self.intervals.get("kucoin"))
                await websocket.send(json.dumps({"type": "ping", "id":conn_id}))   
            except websockets.exceptions.ConnectionClosed:
                if exchange != None:
                    print(f"Connection closed of {exchange}, {insType}, {instrument}. Stopping keep-alive.")
                else:
                    print(f"Connection closed of Kucoin stream. Stopping keep-alive.")


    async def mexc_keep_alive(self, websocket, data=None):
        exchange = data.get("exchange", None)
        insType = data.get("exchange", None)
        instrument = data.get("instrument", None)
        while True:
            try:
                await websocket.send(json.dumps({"method": "PING"}))
                await asyncio.sleep(self.intervals.get("mexc"))
            except websockets.exceptions.ConnectionClosed:
                if exchange != None:
                    print(f"Connection closed of {exchange}, {insType}, {instrument}. Stopping keep-alive.")
                else:
                    print(f"Connection closed of MEXC stream. Stopping keep-alive.")

    async def gateio_keep_alive(self, websocket, data=None):
        exchange = data.get("exchange", None)
        insType = data.get("exchange", None)
        instrument = data.get("instrument", None)
        while True:
            try:
                await asyncio.sleep(self.intervals.get("gateio"))
                await websocket.send("ping")
            except websockets.exceptions.ConnectionClosed:
                if exchange != None:
                    print(f"Connection closed of {exchange}, {insType}, {instrument}. Stopping keep-alive.")
                else:
                    print(f"Connection closed of Gate.io stream. Stopping keep-alive.")


    async def htx_keep_alive(self, websocket, data=None):
        exchange = data.get("exchange", None)
        insType = data.get("exchange", None)
        instrument = data.get("instrument", None)
        while True:
            try:
                await asyncio.sleep(self.intervals.get("htx"))
                await websocket.send("ping")
            except websockets.exceptions.ConnectionClosed:
                if exchange != None:
                    print(f"Connection closed of {exchange}, {insType}, {instrument}. Stopping keep-alive.")
                else:
                    print(f"Connection closed of HTX stream. Stopping keep-alive.")


#### KEY MANAGER ###


class APIClient():
    """
        Abstracts the logic of API calls for coinbase, kucoin and bingx
    """

    def __init__(self, kucoinAPI, kucoinSecret, kucoinPass, coinbaseAPI, coinbaseSecret):
        self.kucoinAPI = kucoinAPI
        self.kucoinSecret = kucoinSecret
        self.kucoinPass = kucoinPass
        self.coinbaseAPI = coinbaseAPI
        self.coinbaseSecret = coinbaseSecret

    def coinbase_jwt_websockets(self):
        key_name = self.coinbaseAPI
        key_secret = self.coinbaseSecret
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
    

    def coinbase_jwt_api(self, type_="product_book"):
        key_name       = self.coinbaseAPI
        key_secret     = self.coinbaseSecret
        request_method = "GET"
        request_host   = "api.coinbase.com"
        request_path   = f"/api/v3/brokerage/{type_}"
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


    def kucoin_api_headers(self, endpoint):
        """
            "/api/v3/market/orderbook/level2?symbol=BTC-USDT"  ---- spot books
            "api/v1/level2/snapshot?symbol=XBTUSDTM"           ---- perpe books
            For more check kucoin API documentation
        """
        api_secret = self.kucoinSecret
        api_key = self.kucoinAPI
        api_passphrase = self.kucoinPass
        now = int(time.time() * 1000)
        str_to_sign = str(now) + "GET" + endpoint
        signature = base64.b64encode(hmac.new(api_secret.encode("utf-8"), str_to_sign.encode("utf-8"), hashlib.sha256).digest())
        headers = {
            "KC-API-SIGN": signature,
            "KC-API-TIMESTAMP": str(now),
            "KC-API-KEY": api_key,
            "KC-API-PASSPHRASE": api_passphrase,
        }
        return headers

    
    @classmethod
    def kucoin_ws_headers(cls):
        """
            Returns kucoin token and endpoint
        """
        endpoint = "https://api.kucoin.com/api/v1/bullet-public"
        response = requests.post(endpoint)
        kucoin_token = response.json().get("data").get("token")
        new_endpoint = response.json().get("data").get("instanceServers")[0].get("endpoint")
        kucoin_connectId = generate_random_id(20)
        return f"{new_endpoint}?token={kucoin_token}&[connectId={kucoin_connectId}]"
    
    @classmethod
    def bingx_requests(cls, endpoint, basepoint, params, APIKEY="", SECRETKEY=""):

        def demo():
            payload = {}
            method = "GET"
            paramsStr = parseParam(params)
            return send_request(method, basepoint, paramsStr, payload)

        def get_sign(api_secret, payload):
            signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
            return signature


        def send_request(method, basepoint, urlpa, payload):
            url = "%s%s?%s&signature=%s" % (endpoint, basepoint, urlpa, get_sign(SECRETKEY, urlpa))
            headers = {
                'X-BX-APIKEY': APIKEY,
            }
            response = requests.request(method, url, headers=headers, data=payload)
            return response.json()

        def parseParam(params):
            sortedKeys = sorted(params)
            paramsStr = "&".join(["%s=%s" % (x, params[x]) for x in sortedKeys])
            if paramsStr != "": 
                return paramsStr+"&timestamp="+str(int(time.time() * 1000))
            else:
                return paramsStr+"timestamp="+str(int(time.time() * 1000))
        return demo()
    
    @classmethod
    async def bingx_aiohttp_books(cls, APIURL, path, paramsMap, obj=None, maximum_retries=None):

        APIKEY = ""
        SECRETKEY = ""

        if obj == "depth":
            async def demo():
                p = [1000, 500, 100, 50, 20, 10, 5]
                for i, _ in enumerate(range(maximum_retries)):
                    paramsMap["limit"] = p[i]
                    payload = {}
                    method = "GET"
                    paramsStr = parseParam(paramsMap)
                    response = await send_request(method, path, paramsStr, payload)
                    response = json.loads(response)
                    if response["code"] == 0:
                        break
                    time.sleep(3)
                return response
        else:
            async def demo():
                payload = {}
                method = "GET"
                paramsStr = parseParam(paramsMap)
                return await json.loads(send_request(method, path, paramsStr, payload))  

        async def get_sign(api_secret, payload):
            signature = hmac.new(
                api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=hashlib.sha256
            ).hexdigest()
            return signature

        async def send_request(method, path, urlpa, payload):
            url = f"{APIURL}{path}?{urlpa}&signature={await get_sign(SECRETKEY, urlpa)}"

            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method, url, headers={"X-BX-APIKEY": APIKEY}, json=payload
                ) as response:
                    response.raise_for_status()  # Raise an exception for error responses
                    return await response.text()

        def parseParam(paramsMap):
            sortedKeys = sorted(paramsMap)
            paramsStr = "&".join([f"{x}={paramsMap[x]}" for x in sortedKeys])
            timestamp = str(int(time.time() * 1000))
            return f"{paramsStr}{'&' if paramsStr else ''}timestamp={timestamp}"

        return await demo()


### Books Fetcher ###
    
class booksFetcher():

    def __init__ (self, books_data, snaplength):
        pass



    def books_snapshot(self, id, snaplength, maximum_retries=10):
        """
            Get lates snapshot via API
        """
        stream_data = get_dict_by_key_value(AaWS, "id", id)
        url = stream_data.get("url")
        exchange = stream_data.get("exchange")
        instrument = stream_data.get("instrument")
        insType= stream_data.get("insType")

        if exchange == "binance":
            url = "&".join([url, f"limit={snaplength}"])
        if exchange == "gateio":
            url = "&".join([url, f"limit={300}"])
        if exchange == "coinbase":
            url_1 = stream_data["url_base"]
            url_2 = url
        if exchange in ["gateio",  "kucoin", "deribit"]:
            headers = stream_data['headers'] 
        
        if exchange in ['binance', 'bybit']:
            for _ in range(maximum_retries):
                response = requests.get(url)
                response = response.json()
                if 'code' in response:    
                    if response.get('code', None) == -1130:
                        snaplength = snaplength - 500
                        url = "&".join([url, f"limit={snaplength}"])
                else:
                    break


        if exchange == "coinbase":
            conn = http.client.HTTPSConnection(url_1)
            payload = ''
            headers = {
                "Authorization": f"Bearer {build_jwt_api()}",
                'Content-Type': 'application/json'
            }
            conn.request("GET", url_2, payload, headers)
            res = conn.getresponse()
            response = res.read()
            response = json.loads(response)

        if exchange == "kucoin":
            response = requests.get(url, headers=headers)
            response = response.json()

        if exchange == "gateio":
            response = requests.request('GET', url, headers=headers)
            response = response.json()
        
        if exchange in ["mexc", "bitget", "htx"]:
            response = requests.get(url)
            response = response.json()
        
        if exchange == "deribit":
            loop = asyncio.get_event_loop()
            asyncio.set_event_loop(loop)
            headers = stream_data.get("headers")
            try:
                response = loop.run_until_complete(websocket_fetcher(url, headers))
            finally:
                loop.close()

        if exchange == 'bingx':
            path = stream_data["path"]
            params = stream_data["params"]
            p = [5, 10, 20, 50, 100, 500, 1000]
            p.reverse()
            for i, _ in enumerate(range(maximum_retries)):
                params["limit"] = p[i]
                response = bingx_AaWSnap(url, path, params)
                if response["code"] == 0:
                    break

        data = {
            "exchange" : exchange,
            "instrument" : instrument,
            "insType" : insType,
            "response" : response 
        }
        return data
