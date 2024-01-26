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
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from config import crypto_panic_token, coinbase_api, coinbase_secret

# Notes:
# To initialize binance, coinbase orderbooks, you should first make an API call and then push updates of orderbooks
# Okx has only 1 liquidation channel for all liquidations stream /// u need to filter if liquidations belon only to BTC
# bybit stream OI+funding rate in a single websocket
# bybit apis fetches TTA, TTP, GTA, GTP in a single API call

def generate_random_integer(n):
    if n <= 0:
        raise ValueError("Length should be a positive integer")
    lower_bound = 10 ** (n - 1)
    upper_bound = (10 ** n) - 1
    random_integer = random.randint(lower_bound, upper_bound)
    return random_integer

def build_jwt():
    key_name = f"organizations/b6a02fc1-cbb0-4658-8bb2-702437518d70/apiKeys/{coinbase_api}" 
    key_secret = f"-----BEGIN EC PRIVATE KEY-----\n{coinbase_secret}==\n-----END EC PRIVATE KEY-----\n" 
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



apizzz = [
    # updateSpeed in seconds

    # Binance APIs : https://binance-docs.github.io/apidocs/spot/en/#change-log
    #                 https://binance-docs.github.io/apidocs/futures/en/#change-log
    #                 https://binance-docs.github.io/apidocs/delivery/en/#change-log
    # OKEx APIs:     https://www.okx.com/docs-v5/en/?python#public-data-rest-api-get-instruments
    # Bybit APIs:    https://bybit-exchange.github.io/docs/v5/intro
    # Deribit APIs:  https://docs.deribit.com/#deribit-api-v2-1-1

    ###
    # Depth
    ###
    {
        "exchange":"binance", 
        "instrument": "btcusdt", 
        "insType":"spot", 
        "obj":"depth", 
        "updateSpeed" : 1, 
        "url" : f"https://api.binance.com/api/v3/depth?symbol=BTCUSDT"
        },
    {
        "exchange":"binance",
        "instrument": "btcfdusd", 
        "insType":"spot", 
        "obj":"depth", 
        "updateSpeed":1, 
        "url" : f"https://api.binance.com/api/v3/depth?symbol=BTCFDUSD"
    },
    {
        "exchange":"binance", 
        "instrument": "btcusdt",
        "insType":"perpetual", 
        "obj":"depth", 
        "updateSpeed":1,
        "url" : f"https://fapi.binance.com/fapi/v1/depth?symbol=BTCUSDT"
    },
    {
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument": "btcusd", 
        "updateSpeed":1, 
        "url" : f"https://dapi.binance.com/dapi/v1/depth?symbol=BTCUSD_PERP"
    },
    {
        "exchange":"bybit", 
        "insType":"spot", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1, 
        "url" : "https://api.bybit.com/v5/market/orderbook?category=spot&symbol=BTCUSDT&limit=200"
    },
    {
        "exchange":"bybit", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1, 
        "url" : "https://api.bybit.com/v5/market/orderbook?category=linear&symbol=BTCUSDT&limit=200"
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
        "obj":"TTP", 
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
        "url" : "https://fapi.binance.com/futures/data/topLongShortAccountRatio?symbol=BTCUSDT&period=5m&limit=1"
    },
    {
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"GTA", 
        "instrument": "btcusd", 
        "updateSpeed":10, 
        "url" : "https://dapi.binance.com/futures/data/topLongShortAccountRatio?pair=BTCUSD&period=5m&limit=1"
    },
    {
        "exchange":"okx", 
        "insType":"perpetual", 
        "obj":"GTA", 
        "updateSpeed":10, 
        "instrument": "btcusd", 
        "url" : f"https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio?ccy=BTC&period=5m"
    }, 
    ###
    # TTA, TTP, GTA, GTP Combined
    ##
    {
        "exchange":"bybit", 
        "insType":"perpetual", 
        "obj":"GTA_GTP_TTA_TTP", 
        "instrument": "btcusdt", 
        "updateSpeed":10, 
        "url" : "https://api.bybit.com/v5/market/account-ratio?category=linear&symbol=BTCUSDT&period=1d&limit=50" # the minimum limit
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
        "url" : "https://api.bybit.com/v5/market/tickers?category=option&symbol=BTCUSDT"
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
        "exchange":"None", 
        "insType":"news", 
        "obj":"aggregator", 
        "instrument":"BTC_USDT_ETH",
        "updateSpeed":30,  # We use server-side caching, so there is no point of making requests more than once every 30 seconds.  https://cryptopanic.com/developers/api/
        "url" : f'https://cryptopanic.com/api/v1/posts/?auth_token={crypto_panic_token}&public=true&currencies=BTC,USDT,ETH&region=en'
    },  
    
    ]


websocketzzz = [
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
              "jwt": build_jwt(),
              "timestamp": int(time.time())
              }     
        },                 
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
              "jwt": build_jwt(),
              "timestamp": int(time.time())
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
        ###
        # OI + FUNDING
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
            "jwt": build_jwt(),
            "timestamp": int(time.time())
            }  
        },  
]
