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

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from config import crypto_panic_token, coinbaseAPI, coinbaseSecret, kucoinAPI, kucoinPass, kucoinSecret


# Notes:
# To initialize binance, coinbase orderbooks, you should first make an API call and then push updates of orderbooks
# Okx has only 1 liquidation channel for all liquidations stream /// u need to filter if liquidations belon only to BTC
# bybit stream OI+funding rate in a single websocket


def get_dict_by_key_value(lst, key, value):
    for d in lst:
        if d.get(key) == value:
            return d
    return None

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

async def websocket_fetcher(link, headers):
    async with websockets.connect(link,  ssl=ssl_context) as websocket:
        await websocket.send(json.dumps(headers))
        response = await websocket.recv()
        return response

def bingx_AaWSnap(APIURL, path, paramsMap):
    APIKEY = ""
    SECRETKEY = ""
    def demo():
        payload = {}
        method = "GET"
        paramsStr = parseParam(paramsMap)
        return send_request(method, path, paramsStr, payload)

    def get_sign(api_secret, payload):
        signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
        return signature


    def send_request(method, path, urlpa, payload):
        url = "%s%s?%s&signature=%s" % (APIURL, path, urlpa, get_sign(SECRETKEY, urlpa))
        headers = {
            'X-BX-APIKEY': APIKEY,
        }
        response = requests.request(method, url, headers=headers, data=payload)
        return response.json()

    def parseParam(paramsMap):
        sortedKeys = sorted(paramsMap)
        paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
        if paramsStr != "": 
            return paramsStr+"&timestamp="+str(int(time.time() * 1000))
        else:
            return paramsStr+"timestamp="+str(int(time.time() * 1000))
    return demo()


def generate_random_id(length):
    characters = string.ascii_letters + string.digits
    random_id = ''.join(random.choice(characters) for i in range(length))
    return random_id

def generate_random_integer(n):
    if n <= 0:
        raise ValueError("Length should be a positive integer")
    lower_bound = 10 ** (n - 1)
    upper_bound = (10 ** n) - 1
    random_integer = random.randint(lower_bound, upper_bound)
    return random_integer

def build_jwt_websockets():
    key_name = coinbaseAPI
    key_secret = coinbaseSecret
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


def build_jwt_api():
    key_name       = coinbaseAPI
    key_secret     = coinbaseSecret
    request_method = "GET"
    request_host   = "api.coinbase.com"
    request_path   = "/api/v3/brokerage/product_book"
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

def build_kucoin_headers_spot():
    api_secret = kucoinSecret
    api_key = kucoinAPI
    api_passphrase = kucoinPass
    now = int(time.time() * 1000)
    str_to_sign = str(now) + "GET" + "/api/v3/market/orderbook/level2?symbol=BTC-USDT"
    signature = base64.b64encode(hmac.new(api_secret.encode("utf-8"), str_to_sign.encode("utf-8"), hashlib.sha256).digest())
    headers = {
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": str(now),
        "KC-API-KEY": api_key,
        "KC-API-PASSPHRASE": api_passphrase,
    }
    return headers

def build_kucoin_headers_futures():
    api_secret = kucoinSecret
    api_key = kucoinAPI
    api_passphrase = kucoinPass
    now = int(time.time() * 1000)
    str_to_sign = str(now) + "GET" + "api/v1/level2/snapshot?symbol=XBTUSDTM"
    signature = base64.b64encode(hmac.new(api_secret.encode("utf-8"), str_to_sign.encode("utf-8"), hashlib.sha256).digest())
    headers = {
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": str(now),
        "KC-API-KEY": api_key,
        "KC-API-PASSPHRASE": api_passphrase,
    }
    return headers

def build_kucoin_wsendpoint():
    """
        Returns kucoin token and endpoint
    """
    kucoin_api = "https://api.kucoin.com/api/v1/bullet-public"
    response = requests.post(kucoin_api)
    kucoin_token = response.json().get("data").get("token")
    kucoin_endpoint = response.json().get("data").get("instanceServers")[0].get("endpoint")
    kucoin_connectId = generate_random_id(20)
    return f"{kucoin_endpoint}?token={kucoin_token}&[connectId={kucoin_connectId}]"


def retrieve_dictionary_by2_values(list_of_dicts, key1, value1, key2, value2):
    for dictionary in list_of_dicts:
        if key1 in dictionary and key2 in dictionary:
            if dictionary[key1] == value1 and dictionary[key2] == value2:
                return dictionary
    return None  
