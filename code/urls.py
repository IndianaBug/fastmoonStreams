import requests
import json
import time
import jwt
from cryptography.hazmat.primitives import serialization
import time
import secrets
from urllib.parse import urlencode
import os
import sys
import random
import hashlib
import hmac
import base64
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from config import crypto_panic_token, coinbaseAPI, coinbaseSecret, kucoinAPI, kucoinPass, kucoinSecret
import random
import string

# Notes:
# To initialize binance, coinbase orderbooks, you should first make an API call and then push updates of orderbooks
# Okx has only 1 liquidation channel for all liquidations stream /// u need to filter if liquidations belon only to BTC
# bybit stream OI+funding rate in a single websocket

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



APIS = [
    # updateSpeed in seconds

    # Binance APIs : https://binance-docs.github.io/apidocs/spot/en/#change-log
    #                 https://binance-docs.github.io/apidocs/futures/en/#change-log
    #                 https://binance-docs.github.io/apidocs/delivery/en/#change-log
    # OKEx APIs:     https://www.okx.com/docs-v5/en/?python#public-data-rest-api-get-instruments
    # Bybit APIs:    https://bybit-exchange.github.io/docs/v5/intro
    # Deribit APIs:  https://docs.deribit.com/#deribit-api-v2-1-1
    # Kucoin APIs :  https://www.kucoin.com/docs/rest/spot-trading/market-data/get-full-order-book-aggregated-

    ###
    # Depth
    ###
    {
        "id" : "binance_spot_btcusdt_depth",
        "exchange":"binance", 
        "instrument": "btcusdt", 
        "insType":"spot", 
        "obj":"depth", 
        "updateSpeed" : 1, 
        "url" : f"https://api.binance.com/api/v3/depth?symbol=BTCUSDT"
        },
    {
        "id" : "binance_spot_btcfdusd_depth",
        "exchange":"binance",
        "instrument": "btcfdusd", 
        "insType":"spot", 
        "obj":"depth", 
        "updateSpeed":1, 
        "url" : f"https://api.binance.com/api/v3/depth?symbol=BTCFDUSD"
    },
    {
        "id" : "binance_perpetual_btcusdt_depth",
        "exchange":"binance", 
        "instrument": "btcusdt",
        "insType":"perpetual", 
        "obj":"depth", 
        "updateSpeed":1,
        "url" : f"https://fapi.binance.com/fapi/v1/depth?symbol=BTCUSDT"
    },
    {
        "id" : "binance_perpetual_btcusd_depth",
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument": "btcusd", 
        "updateSpeed":1, 
        "url" : f"https://dapi.binance.com/dapi/v1/depth?symbol=BTCUSD_PERP"
    },
    {
        "id" : "bybit_spot_btcusdt_depth",
        "exchange":"bybit", 
        "insType":"spot", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1, 
        "url" : "https://api.bybit.com/v5/market/orderbook?category=spot&symbol=BTCUSDT&limit=200"
    },
    {
        "id" : "bybit_spot_btcusdc_depth",
        "exchange":"bybit", 
        "insType":"spot", 
        "obj":"depth", 
        "instrument": "btcusdc",
        "updateSpeed":1, 
        "url" : "https://api.bybit.com/v5/market/orderbook?category=spot&symbol=BTCUSDC&limit=200"
    },
    {
        "id" : "bybit_perpetual_btcusdt_depth",
        "exchange":"bybit", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1, 
        "url" : "https://api.bybit.com/v5/market/orderbook?category=linear&symbol=BTCUSDT&limit=200"
    },
    {
        "id" : "bybit_perpetual_btcusd_depth",
        "exchange":"bybit", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument": "btcusd",
        "updateSpeed":1, 
        "url" : "https://api.bybit.com/v5/market/orderbook?category=linear&symbol=BTCUSD&limit=200"
    },
    {
        "id" : "coinbase_spot_btcusd_depth",
        "exchange":"coinbase", 
        "insType":"spot", 
        "obj":"depth", 
        "instrument": "btcusd",
        "updateSpeed":1,
        "url_base" :  "api.coinbase.com",
        "url" : "/api/v3/brokerage/product_book?product_id=BTC-USD"
    },
    {
        "id" : "kucoin_spot_btcusdt_depth",
        "exchange":"kucoin", 
        "insType":"spot", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://api.kucoin.com/api/v3/market/orderbook/level2?symbol=BTC-USDT",
        "headers" : build_kucoin_headers_spot()         
    },
    {
        "id" : "kucoin_perpetual_btcusdt_depth",
        "exchange":"kucoin", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://api-futures.kucoin.com/api/v1/level2/snapshot?symbol=XBTUSDTM",
        "headers" : build_kucoin_headers_futures()         
    },
    {
        "id" : "gateio_spot_btcusdt_depth",
        "exchange":"gateio", 
        "insType":"spot", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://api.gateio.ws/api/v4/spot/order_book?currency_pair=BTC_USDT",
        "headers" : {'Accept': 'application/json', 'Content-Type': 'application/json'}          # requests.request('GET', url, headers=headers)
    },
    {
        "id" : "gateio_perpetual_btcusdt_depth",
        "exchange":"gateio", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://api.gateio.ws/api/v4/futures/usdt/order_book?contract=BTC_USDT",
        "headers" : {'Accept': 'application/json', 'Content-Type': 'application/json'}          
    },
    {
        "id" : "mexc_spot_btcusdt_depth",
        "exchange":"mexc", 
        "insType":"spot", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://api.mexc.com/api/v3/depth?symbol=BTCUSDT&limit=5000", # simple get request
    },
    {
        "id" : "mexc_perpetual_btcusdt_depth",
        "exchange":"mexc", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://contract.mexc.com/api/v1/contract/depth/BTC_USDT", # simple get request
    },
    {
        "id" : "bitget_spot_btcusdt_depth",
        "exchange":"bitget", 
        "insType":"spot", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://api.bitget.com/api/v2/spot/market/orderbook?symbol=BTCUSDT&type=step0&limit=150" , # simple get request
    },
    {
        "id" : "bitget_perpetual_btcusdt_depth",
        "exchange":"bitget", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://api.bitget.com/api/v2/mix/market/merge-depth?productType=usdt-futures&symbol=BTCUSDT&limit=1000", 
    },
    {
        "id" : "htx_spot_btcusdt_depth",
        "exchange":"htx", 
        "insType":"spot", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://api.huobi.pro/market/depth?symbol=btcusdt&depth=20&type=step0", 
    },
    {
        "id" : "htx_perpetual_btcusdt_depth",
        "exchange":"htx", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://api.hbdm.com/linear-swap-ex/market/depth?contract_code=BTC-USDT&type=step0", 
    },
    {   # Can only be called with websockets
        "id" : "deribit_perpetual_btcusd_depth",
        "exchange":"deribit", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument":"btcusd", 
        "updateSpeed": 1,
        "url" : "wss://test.deribit.com/ws/api/v2",  
        "headers" : {
            "jsonrpc": "2.0", "id": generate_random_integer(10), 
            "method": "public/get_order_book",
            "params": { 
                "depth": 1000, 
                "instrument_name": "BTC-PERPETUAL"
                }
            }
    },
    {
        "id" : "bingx_perpetual_btcusdt_depth",  
        "exchange":"bingx", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument":"btcusdt", 
        "updateSpeed": 1,
        "url" : "https://open-api.bingx.com",  
        "path" : "/openApi/swap/v2/quote/depth",
        "params" : {
                    "symbol": "BTC-USDT",
                    "limit": "1000"
                    }
    },
    {  
        "id" : "bingx_spot_btcusdt_depth",  
        "exchange":"bingx", 
        "insType":"spot", 
        "obj":"depth", 
        "instrument":"btcusdt", 
        "updateSpeed": 1,
        "url" : "https://open-api.bingx.com",  
        "path" : "/openApi/spot/v1/market/depth",
        "params" : {
                    "symbol": "BTC-USDT",
                    "limit": "1000"
                    }
    },
    ###
    # Funding rate
    ###
    {
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"fundingRate", 
        "instrument": "btcusd", 
        "updateSpeed": 10,  # 360 
        "url" : "https://dapi.binance.com/dapi/v1/fundingRate?symbol=BTCUSD_PERP&limit=1"
    },
    {
        "exchange":"binance",
        "insType":"perpetual", 
        "obj":"fundingRate",
        "instrument": "btcusdt", 
        "updateSpeed":10,  # 360 
        "url" : "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1"
    },
    ###
    # OI
    ###
    {
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"OI", 
        "instrument": "btcusdt", 
        "updateSpeed":3, 
        "url" : "https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT"
    },
    {
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"OI", 
        "instrument": "btcusd", 
        "updateSpeed":3, 
        "url" : "https://dapi.binance.com/dapi/v1/openInterest?symbol=BTCUSD_PERP"
    },
    ###
    # Funding + OI
    ###
    {
        "exchange":"gateio", 
        "insType":"perpetual", 
        "obj":"fundingOIs", 
        "instrument": "btcusdt", 
        "updateSpeed":3, 
        "url" : "https://api.gateio.ws/api/v4/futures/usdt/contracts/BTC_USDT",
        "headers" : {'Accept': 'application/json', 'Content-Type': 'application/json'}
    },
    {
        "id" : "kucoin_perpetual_btcusdt_fundingOI",
        "exchange":"kucoin", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://api-futures.kucoin.com/api/v1/contracts/XBTUSDTM",
        "headers" : build_kucoin_headers_futures()         
    },
    ###
    # Liquidation History
    ###
    {  # https://www.gate.io/docs/developers/apiv4/en/#retrieve-liquidation-history
        "exchange":"gateio", 
        "insType":"perpetual", 
        "obj":"liquidations", 
        "instrument": "btcusdt", 
        "updateSpeed":3, 
        "url" : f"https://api.gateio.ws/api/v4/futures/usdt/liq_orders?s=BTC_USDT&from={int(time.time()) - 10}&to={int(time.time())}",
        "headers" : {'Accept': 'application/json', 'Content-Type': 'application/json'}
    },    
    ###
    # Top Trades Accounts
    ###
    {
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"TTA", 
        "instrument": "btcusdt", 
        "updateSpeed":10,  # 300 
        "url" : "https://fapi.binance.com/futures/data/topLongShortAccountRatio?symbol=BTCUSDT&period=5m&limit=1"
    },
    {
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"TTA", 
        "instrument": "btcusd", 
        "updateSpeed":10, 
        "url" : "https://dapi.binance.com/futures/data/topLongShortAccountRatio?pair=BTCUSD&period=5m&limit=1"
    },
    ###
    # Top Trades Positions
    ###
    {
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"TTP", 
        "instrument": "btcusdt", 
        "updateSpeed":10, 
        "url" : "https://fapi.binance.com/futures/data/topLongShortPositionRatio?symbol=BTCUSDT&period=5m&limit=1"
    },
    {
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"TTP", 
        "instrument": "btcusd", 
        "updateSpeed":10, 
        "url" : "https://dapi.binance.com/futures/data/topLongShortPositionRatio?pair=BTCUSD&period=5m&limit=1"
    },
    ###
    # Global Traders Accounts
    ##
    {
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"GTA", 
        "instrument": "btcusdt", 
        "updateSpeed":10, 
        "url" : "https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol=BTCUSDT&period=5m&limit=1"
    },
    {
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"GTA", 
        "instrument": "btcusd", 
        "updateSpeed":10, 
        "url" : "https://dapi.binance.com/futures/data/globalLongShortAccountRatio?pair=BTCUSD&period=5m&limit=1"
    },
    {
        "exchange":"okx", 
        "insType":"perpetual", 
        "obj":"GTA", 
        "updateSpeed":10, 
        "instrument": "btcusd", 
        "url" : f"https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio?ccy=BTC&period=5m"
    }, 
    {
        "exchange":"bybit", 
        "insType":"perpetual", 
        "obj":"GTA", 
        "instrument": "btcusdt", 
        "updateSpeed":10, 
        "url" : "https://api.bybit.com/v5/market/account-ratio?category=linear&symbol=BTCUSDT&period=1d&limit=50" # the minimum limit
    },
    {
        "exchange":"bybit", 
        "insType":"perpetual", 
        "obj":"GTA", 
        "instrument": "btcusdc", 
        "updateSpeed":10, 
        "url" : "https://api.bybit.com/v5/market/account-ratio?category=linear&symbol=BTCUSDC&period=1d&limit=50" # the minimum limit
    },
    ###
    # Options OI
    ## 
    {   # Can only be called with websockets
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
    {
        "exchange":"bybit", 
        "insType":"option", 
        "obj":"OI", 
        "instrument": "btcusdt",
        "updateSpeed":1800, 
        "url" : "https://api.bybit.com/v5/market/tickers?category=option&baseCoin=BTC"
    },
    {
        "exchange":"okx", 
        "insType":"option", 
        "obj":"OI", 
        "instrument": "btc",
        "updateSpeed":1800, 
        "url" : f"https://www.okx.com/api/v5/public/open-interest?instType=OPTION&instFamily=BTC-USD"
    },
    ###
    # News Aggregator
    ###
    {   
        "exchange":"ALL", 
        "insType":"news", 
        "obj":"aggregator", 
        "instrument":"BTC_USDT_ETH",
        "updateSpeed":30,  # We use server-side caching, so there is no point of making requests more than once every 30 seconds.  https://cryptopanic.com/developers/api/
        "url" : f'https://cryptopanic.com/api/v1/posts/?auth_token={crypto_panic_token}&public=true&currencies=BTC,USDT,ETH&region=en'
    },  
    
    ]


WEBSOCKETS = [
        # Binance spot APIs: https://binance-docs.github.io/apidocs/spot/en/#change-log
        # Binance usdt APIs: https://binance-docs.github.io/apidocs/futures/en/#change-log
        # Binance coin APIs: https://binance-docs.github.io/apidocs/delivery/en/#change-log
        # OKEx: https://www.okx.com/docs-v5/en/?python#public-data-websocket-funding-rate-channel
        # Bybit: https://www.bybit.com/future-activity/en/developer
        # Coinbase: https://docs.cloud.coinbase.com/exchange/docs/websocket-channels
        # Derebit: https://docs.deribit.com/
        ###
        # Trades
        ###
        {
          "exchange":"binance", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://stream.binance.com:9443/ws",
          "msg" : {
              "method": "SUBSCRIBE", 
              "params": ["btcusdt@aggTrade"], 
              "id": generate_random_integer(10)
              }
        },
        {
          "exchange":"binance", 
          "instrument": "btcfdusd", 
          "insType":"spot", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://stream.binance.com:9443/ws",
          "msg" : {
              "method": "SUBSCRIBE", 
              "params": ["btcfdusd@aggTrade"], 
              "id": generate_random_integer(10)
              }
        },
        {
          "exchange":"binance", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://fstream.binance.com/ws",
          "msg" : {
              "method": "SUBSCRIBE", 
              "params": ["btcusdt@aggTrade"], 
              "id": generate_random_integer(10)
              }
        },
        {
          "exchange":"binance", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://dstream.binance.com/ws",
          "msg" : {
              "method": "SUBSCRIBE", 
              "params": ["btcusd_perp@aggTrade"], 
              "id": generate_random_integer(10)
              }
        },
        {
          "exchange":"okx", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'trades', 'instId': 'BTC-USDT-SWAP'
                      }
              ]
              }
        },
        {
          "exchange":"okx", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'trades', 'instId': 'BTC-USD-SWAP'
                      }
              ]
              }
        },
        {
          "exchange":"okx", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'trades', 'instId': 'BTC-USDT'
                      }
              ]
              }
        },
        {
          "exchange":"bybit", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://stream.bybit.com/v5/public/spot",
          "msg" : {
              "op": 
              "subscribe","args": [
                  "publicTrade.BTCUSDT"
                  ]
              }
        },
        {
          "exchange":"bybit", 
          "instrument": "btcusdc", 
          "insType":"spot", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://stream.bybit.com/v5/public/spot",
          "msg" : {
              "op": 
              "subscribe","args": [
                  "publicTrade.BTCUSDT"
                  ]
              }
        },
        {
          "exchange":"bybit", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://stream.bybit.com/v5/public/linear",
          "msg" : {
              "op": "subscribe",
              "args": [
                  "publicTrade.BTCUSDT"
                  ]
              }
        },
        {
          "exchange":"bybit", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://stream.bybit.com/v5/public/linear",
          "msg" : {
              "op": "subscribe",
              "args": [
                  "publicTrade.BTCUSD"
                  ]
              }
        },
        {
          "exchange":"coinbase", 
          "instrument": "btcusd", 
          "insType":"spot", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://advanced-trade-ws.coinbase.com",
          "msg" : {
              "type": "subscribe",
              "product_ids": ["BTC-USD"],
              "channel": "market_trades",
              "jwt": build_jwt_websockets(),
              "timestamp": int(time.time())
              }     
        },
        {
          "id" : "kucoin_spot_btcusdt_trades",  
          "exchange":"kucoin", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : build_kucoin_wsendpoint(),
          "msg" : {
                    "id": generate_random_integer(10),   
                    "type": "subscribe",
                    "topic": "/market/match:BTC-USDT",
                    "response": True
                    }
        },
        {
          "id" : "kucoin_perpetual_btcusdt_trades",
          "exchange":"kucoin", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : build_kucoin_wsendpoint(),
          "msg" : {
                    "id": generate_random_integer(10),   
                    "type": "subscribe",
                    "topic": "/contractMarket/execution:XBTUSDTM",
                    "response": True
                    }
        },
        {
          'exchange':'gateio', 
          'instrument': 'btcusdt', 
          'insType':'spot', 
          'obj':'trades', 
          'updateSpeed' : 0, 
          'url' : "wss://api.gateio.ws/ws/v4/",
          'msg' : {
                        "time": int(time.time()),
                        "channel": "spot.trades",
                        "event": "subscribe",  
                        "payload": ["BTC_USDT"]
                    }
        },
        { # https://www.gate.io/docs/developers/futures/ws/en/#trades-api
          'exchange':'gateio', 
          'instrument': 'btcusdt', 
          'insType':'perpetual', 
          'obj':'trades', 
          'updateSpeed' : 0, 
          'url' : "wss://fx-ws-testnet.gateio.ws/v4/ws/btc",
          'msg' : {
                        "time": int(time.time()),
                        "channel": "futures.trades",
                        "event": "subscribe",  
                        "payload": ["BTC_USDT"]
                    }
        },
        {
          "id" : "mexc_spot_btcusdt_trades",
          "exchange":"mexc", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://wbs.mexc.com/ws",
          "msg" : {
                        "method": "SUBSCRIPTION",
                        "params": [
                            "spot@public.deals.v3.api@BTCUSDT"
                        ]
                    }
        },
        {
          "id" : "mexc_perpetual_btcusdt_trades",
          "exchange":"mexc", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://contract.mexc.com/edge",
          "msg" : {
                    "method":"sub.deal",
                    "param":{
                        "symbol":"BTC_USDT"
                    }
                }
        },
        {
          "id" : "bitget_spot_btcusdt_trades",
          "exchange":"bitget", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://ws.bitget.com/v2/ws/public",
          "msg" : {
                    "op": "subscribe",
                    "args": [
                        {
                            "instType": "SPOT",
                            "channel": "trade",
                            "instId": "BTCUSDT"
                        }
                    ]
                }
        },
        {
          "id" : "bitget_perpetual_btcusdt_trades",
          "exchange":"bitget", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://ws.bitget.com/v2/ws/public",
          "msg" : {
                    "op": "subscribe",
                    "args": [
                        {
                            "instType": "USDT-FUTURES",
                            "channel": "trade",
                            "instId": "BTCUSDT"
                        }
                    ]
                }
        },
        # {
        #   "id" : "bitget_spot_btcusdt_depth",
        #   "exchange":"bitget", 
        #   "instrument": "btcusdt", 
        #   "insType":"spot", 
        #   "obj":"depth", 
        #   "updateSpeed" : 0, 
        #   "url" : "wss://ws.bitget.com/v2/ws/public",
        #   "msg" : {
        #             "op": "subscribe",
        #             "args": [
        #                 {
        #                     "instType": "SPOT",
        #                     "channel": "books",
        #                     "instId": "BTCUSDT"
        #                 }
        #             ]
        #         }
        # },
        # {
        #   "id" : "bitget_perpetual_btcusdt_depth",
        #   "exchange":"bitget", 
        #   "instrument": "btcusdt", 
        #   "insType":"perpetual", 
        #   "obj":"depth", 
        #   "updateSpeed" : 0, 
        #   "url" : "wss://ws.bitget.com/v2/ws/public",
        #   "msg" : {
        #             "op": "subscribe",
        #             "args": [
        #                 {
        #                     "instType": "USDT-FUTURES",
        #                     "channel": "books",
        #                     "instId": "BTCUSDT"
        #                 }
        #             ]
        #         }
        # },
        # {
        #   "id" : "bitget_perpetual_btcusdt_fundingOI",
        #   "exchange":"bitget", 
        #   "instrument": "btcusdt", 
        #   "insType":"perpetual", 
        #   "obj":"fundingOI", 
        #   "updateSpeed" : 0, 
        #   "url" : "wss://ws.bitget.com/v2/ws/public",
        #   "msg" : {
        #             "op": "subscribe",
        #             "args": [
        #                 {
        #                     "instType": "USDT-FUTURES",
        #                     "channel": "ticker",
        #                     "instId": "BTCUSDT"
        #                 }
        #             ]
        #         }
        # },                                 
        ###
        # Depth
        ###
        {
          "exchange":"binance", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"depth", 
          "updateSpeed" : 1, 
          "url" : "wss://stream.binance.com:9443/ws",
          "msg" : {
              "method": "SUBSCRIBE", 
              "params": ["btcusdt@depth@1000ms"], 
              "id": generate_random_integer(10)
              }
        },
        {
          "exchange":"binance", 
          "instrument": "btcfdusd", 
          "insType":"spot", 
          "obj":"depth", 
          "updateSpeed" : 1, 
          "url" : "wss://stream.binance.com:9443/ws",
          "msg" : {
              "method": "SUBSCRIBE", 
              "params": ["btcfdusd@depth@1000ms"], 
              "id": generate_random_integer(10)
              }
        },
        {
          "exchange":"binance", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"depth", 
          "updateSpeed" : 0.5, 
          "url" : "wss://stream.binance.com:9443/ws",
          "msg" : {
              "method": "SUBSCRIBE", 
              "params": ["btcusdt@depth@500ms"], 
              "id": generate_random_integer(10)
              }
        },
        {
          "exchange":"binance", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"depth", 
          "updateSpeed" : 0.5, 
          "url" : "wss://dstream.binance.com/ws",
          "msg" : {
              "method": "SUBSCRIBE", 
              "params": ["btcusd_perp@depth@500ms"], 
              "id": generate_random_integer(10)
              }
        },
        {
          "exchange":"okx", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"depth", 
          "updateSpeed" : 0.5, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'books', 'instId': 'BTC-USDT'
                      }
              ]
              }
        },
        {
          "exchange":"okx", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"depth", 
          "updateSpeed" : 0.5, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'books', 'instId': 'BTC-USD-SWAP'
                      }
              ]
              }
        },
        {
          "exchange":"okx", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"depth", 
          "updateSpeed" : 0.5, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'books', 'instId': 'BTC-USDT'
                      }
              ]
              }
        },
        {
          "exchange":"bybit", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"depth", 
          "updateSpeed" : 0.2, 
          "url" : "wss://stream.bybit.com/v5/public/spot",
          "msg" : {
              "op": 
              "subscribe","args": [
                  "orderbook.200.BTCUSDT"
                  ]
              }
        },
        {
          "exchange":"bybit", 
          "instrument": "btcusdc", 
          "insType":"spot", 
          "obj":"depth", 
          "updateSpeed" : 0.2, 
          "url" : "wss://stream.bybit.com/v5/public/spot",
          "msg" : {
              "op": 
              "subscribe","args": [
                  "orderbook.200.BTCUSDC"
                  ]
              }
        },
        {
          "exchange":"bybit", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"depth", 
          "updateSpeed" : 0.2, 
          "url" : "wss://stream.bybit.com/v5/public/linear",
          "msg" : {
              "op": 
              "subscribe","args": [
                  "orderbook.200.BTCUSDT"
                  ]
              }
        },
        {
          "exchange":"bybit", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"depth", 
          "updateSpeed" : 0.2, 
          "url" : "wss://stream.bybit.com/v5/public/linear",
          "msg" : {
              "op": 
              "subscribe","args": [
                  "orderbook.200.BTCUSD"
                  ]
              }
        },
        {
          "exchange":"coinbase", 
          "instrument": "btcusd", 
          "insType":"spot", 
          "obj":"depth", 
          "updateSpeed" : 0, 
          "url" : "wss://advanced-trade-ws.coinbase.com",
          "msg" : {
              "type": "subscribe",
              "product_ids": ["BTC-USD"],
              "channel": "level2",
              "jwt": build_jwt_websockets(),
              "timestamp": int(time.time())
              }     
        },
        {
          "exchange":"kucoin", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"depth", 
          "updateSpeed" : 0, 
          "url" : build_kucoin_wsendpoint(),
          "msg" : {
                    "id": generate_random_integer(10),   
                    "type": "subscribe",
                    "topic": "/market/level2:BTC-USDT",
                    "response": True
                    }
        },
        {
          "id" : "kucoin_perpetual_btcusdt_depth",
          "exchange":"kucoin", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : build_kucoin_wsendpoint(),
          "msg" : {
                    "id": generate_random_integer(10),   
                    "type": "subscribe",
                    "topic": "/contractMarket/level2:XBTUSDTM",
                    "response": True
                    }
        },
        {
          'exchange':'gateio', 
          'instrument': 'btcusdt', 
          'insType':'spot', 
          'obj':'depth', 
          'updateSpeed' : 0, 
          'url' : "wss://api.gateio.ws/ws/v4/",
          'msg' : {
                        "time": int(time.time()),
                        "channel": "spot.order_book_update",
                        "event": "subscribe",  
                        "payload": ["BTC_USDT", "1000ms"]
                    }

        },
        {
          'exchange':'gateio', 
          'instrument': 'btcusdt', 
          'insType':'spot', 
          'obj':'depth', 
          'updateSpeed' : 0, 
          'url' : "wss://fx-ws-testnet.gateio.ws/v4/ws/btc",
          'msg' : {
                        "time": int(time.time()),
                        "channel": "futures.order_book_update",
                        "event": "subscribe",  
                        "payload": ["BTC_USDT", "1000ms"]
                    }

        },
        {
          "id" : "mexc_spot_btcusdt_depth",
          "exchange":"mexc", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"depth", 
          "updateSpeed" : 0, 
          "url" : "wss://wbs.mexc.com/ws",
          "msg" : {
                        "method": "SUBSCRIPTION",
                        "params": [
                            "spot@public.increase.depth.v3.api@BTCUSDT"
                        ]
                    }
        },
        {
          "id" : "mexc_perpetual_btcusdt_depth",
          "exchange":"mexc", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"depth", 
          "updateSpeed" : 0, 
          "url" : "wss://contract.mexc.com/edge",
          "msg" : {
                    "method":"sub.depth",
                    "param":{
                        "symbol":"BTC_USDT"
                    }
                }
        },
        ###
        # Open interest
        ###
        {
          "exchange":"okx", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"OI", 
          "updateSpeed" : 0.5, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'open-interest', 'instId': 'BTC-USDT-SWAP'
                      }
              ]
              }
        },
        {
          "exchange":"okx", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"OI", 
          "updateSpeed" : 0.5, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'open-interest', 'instId': 'BTC-USD-SWAP'
                      }
              ]
              }
        },
        {
          "exchange":"okx", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"fundingRate", 
          "updateSpeed" : 0.5, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'funding-rate', 'instId': 'BTC-USD-SWAP'
                      }
              ]
              }
        },
        {
          "exchange":"okx", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"fundingRate", 
          "updateSpeed" : 0.5, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'funding-rate', 'instId': 'BTC-USDT-SWAP'
                      }
              ]
              }
        },
        ###
        # Liquidations
        ###
        {
          "exchange":"binance", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"liquidations", 
          "updateSpeed" : 0, 
          "url" : "wss://fstream.binance.com/ws",
          "msg" : {
              "method": "SUBSCRIBE", 
              "params": ["btcusdt@forceOrder"], 
              "id": generate_random_integer(10)
              }
        },
        {
          "exchange":"binance", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"liquidations", 
          "updateSpeed" : 0, 
          "url" : "wss://dstream.binance.com/ws",
          "msg" : {
              "method": "SUBSCRIBE", 
              "params": ["btcusd_perp@forceOrder"], 
              "id": generate_random_integer(10)
              }
        },
        {
          "exchange":"okx", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"liquidations", 
          "updateSpeed" : 0.5, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'liquidation-orders', 'instType': 'SWAP'
                      }
              ]
              }
        },
        {
          "exchange":"bybit", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"liquidations", 
          "updateSpeed" : 0.2, 
          "url" : "wss://stream.bybit.com/v5/public/linear",
          "msg" : {
              "op": 
              "subscribe","args": [
                  "liquidation.BTCUSDT"
                  ]
              }
        },
        {
          "exchange":"bybit", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"liquidations", 
          "updateSpeed" : 0.2, 
          "url" : "wss://stream.bybit.com/v5/public/linear",
          "msg" : {
              "op": 
              "subscribe","args": [
                  "liquidation.BTCUSD"
                  ]
              }
        },
        ###
        # OI + FUNDING        # OK
        ###
        {
          "exchange":"bybit", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"fundingRate_OI", 
          "updateSpeed" : 0, 
          "url" : "wss://stream.bybit.com/v5/public/linear",
          "msg" : {
              "op": 
              "subscribe","args": [
                  "tickers.BTCUSDT"
                  ]
              }
        },
        {
          "exchange":"bybit", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"fundingRate_OI", 
          "updateSpeed" : 0, 
          "url" : "wss://stream.bybit.com/v5/public/linear",
          "msg" : {
              "op": 
              "subscribe","args": [
                  "tickers.BTCUSD"
                  ]
              }
        },
        {
          "id" : "mexc_perpetual_btcusdt_fundingOI",
          "exchange":"mexc", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"fundingOI", 
          "updateSpeed" : 0, 
          "url" : "wss://contract.mexc.com/edge",
          "msg" : {
                    "method":"sub.ticker",
                    "param":{
                        "symbol":"BTC_USDT"
                    }
                }
        },    
        # HEARTBEAT # Coibase requires to use heartbeats to keep all connections opened
        {
          "exchange":"coinbase", 
          "instrument": "btcusd", 
          "insType":"spot", 
          "obj":"heartbeat", 
          "updateSpeed" : 0, 
          "url" : "wss://advanced-trade-ws.coinbase.com",
          "msg" :         {
            "type": "subscribe",
            "product_ids": [
                "BTC-USD"
            ],
            "channel": "heartbeats",
            "jwt": build_jwt_websockets(),
            "timestamp": int(time.time())
            }  
        },  
]
