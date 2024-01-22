import random
from datetime import datetime, timedelta
import time
import jwt
from cryptography.hazmat.primitives import serialization
import time
import secrets
from urllib.parse import urlencode
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from config import crypto_panic_token, coinbase_api, coinbase_secret

def generate_random_integer(n):
    if n <= 0:
        raise ValueError("Length should be a positive integer")
    lower_bound = 10 ** (n - 1)
    upper_bound = (10 ** n) - 1
    random_integer = random.randint(lower_bound, upper_bound)
    return random_integer

def miliseconds_to_strftime(data: int) -> str:
    return datetime.utcfromtimestamp(data / 1000.0).strftime('%Y-%m-%d %H:%M:%S UTC')



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

def built_jwt_api():
    key_name       = f"organizations/b6a02fc1-cbb0-4658-8bb2-702437518d70/apiKeys/{coinbase_api}"
    key_secret     = f"-----BEGIN EC PRIVATE KEY-----\n{coinbase_secret}==\n-----END EC PRIVATE KEY-----\n" 
    request_method = "GET"
    request_host   = "api.coinbase.com"
    request_path   = "/api/v3/brokerage/product_book"
    service_name   = "retail_rest_api_proxy"
    def build_jwt_books(service, uri):
        private_key_bytes = key_secret.encode('utf-8')
        private_key = serialization.load_pem_private_key(private_key_bytes, password=None)
        jwt_payload = {
            'sub': key_name,
            'iss': "coinbase-cloud",
            'nbf': int(time.time()),
            'exp': int(time.time()) + 120,
            'aud': [service],
            'uri': uri,
        }
        jwt_token = jwt.encode(
            jwt_payload,
            private_key,
            algorithm='ES256',
            headers={'kid': key_name, 'nonce': secrets.token_hex()},
        )
        return jwt_token
    return build_jwt_books(service_name, f"{request_method} {request_host}{request_path}")



# Binance APIs : https://binance-docs.github.io/apidocs/spot/en/#change-log
#                 https://binance-docs.github.io/apidocs/futures/en/#change-log
#                 https://binance-docs.github.io/apidocs/delivery/en/#change-log
# OKEx APIs:     https://www.okx.com/docs-v5/en/?python#public-data-rest-api-get-instruments
# Bybit APIs:    https://bybit-exchange.github.io/docs/v5/intro
# Deribit APIs:  https://docs.deribit.com/#deribit-api-v2-1-1

APIs = [
    # binance
    {"exchange":"binance", "insType":"SPOT", "obj":"depth", "instrument": "btc/usdt", "snapshotInterval":1, "url" : f"https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=1000"},
    {"exchange":"binance", "insType":"SPOT", "obj":"depth", "instrument": "btc/fdusd", "snapshotInterval":1, "url" : f"https://api.binance.com/api/v3/depth?symbol=BTCFDUSD&limit=1000"},
    {"exchange":"binance", "insType":"PERPETUAL", "obj":"depth", "instrument": "btc/usdt", "snapshotInterval":1, "url" : f"https://fapi.binance.com/fapi/v1/depth?symbol=BTCUSDT&limit=1000"},
    {"exchange":"binance", "insType":"PERPETUAL", "obj":"depth", "instrument": "btc/usd", "snapshotInterval":1, "url" : f"https://dapi.binance.com/dapi/v1/depth?symbol=BTCUSD_PERP&limit=750"},
    {"exchange":"binance", "insType":"PERPETUAL", "obj":"premiumIndex", "instrument": "btc/usdt", "snapshotInterval":300, "url" : "https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT"}, # snap every 5 minute
    {"exchange":"binance", "insType":"PERPETUAL", "obj":"fundingRate", "instrument": "btc/usd", "snapshotInterval":300, "url" : "https://dapi.binance.com/dapi/v1/fundingRate?symbol=BTCUSD_PERP"}, 
    {"exchange":"binance", "insType":"PERPETUAL", "obj":"OI", "instrument": "btc/usdt", "snapshotInterval":3, "url" : "https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT"},   # snap every 3 seconds
    {"exchange":"binance", "insType":"PERPETUAL", "obj":"OI", "instrument": "btc/usd", "snapshotInterval":3, "url" : "https://dapi.binance.com/dapi/v1/openInterest?symbol=BTCUSD_PERP"},
    {"exchange":"binance", "insType":"STATISTIC_CONTRACTS", "obj":"TTA", "instrument": "btc/usdt", "snapshotInterval":300, "url" : "https://fapi.binance.com/futures/data/topLongShortAccountRatio?symbol=BTCUSDT&period=5m&limit=1"},   # snap every 5 minute
    {"exchange":"binance", "insType":"STATISTIC_CONTRACTS", "obj":"TTA", "instrument": "btc/usd", "snapshotInterval":300, "url" : "https://dapi.binance.com/futures/data/topLongShortAccountRatio?pair=BTCUSD&period=5m&limit=1"},
    {"exchange":"binance", "insType":"STATISTIC_CONTRACTS", "obj":"TTP", "instrument": "btc/usdt", "snapshotInterval":300, "url" : "https://fapi.binance.com/futures/data/topLongShortAccountRatio?symbol=BTCUSDT&period=5m&limit=1"},   # snap every 5 minute
    {"exchange":"binance", "insType":"STATISTIC_CONTRACTS", "obj":"TTP", "instrument": "btc/usd", "snapshotInterval":300, "url" : "https://dapi.binance.com/futures/data/topLongShortAccountRatio?pair=BTCUSD&period=5m&limit=1"},
    {"exchange":"binance", "insType":"STATISTIC_CONTRACTS", "obj":"GTA", "instrument": "btc/usdt", "snapshotInterval":300, "url" : "https://fapi.binance.com/futures/data/topLongShortAccountRatio?symbol=BTCUSDT&period=5m&limit=1"},   # snap every 5 minute
    {"exchange":"binance", "insType":"STATISTIC_CONTRACTS", "obj":"GTA", "instrument": "btc/usd", "snapshotInterval":300, "url" : "https://dapi.binance.com/futures/data/topLongShortAccountRatio?pair=BTCUSD&period=5m&limit=1"},
    # bybit
    {"exchange":"bybit", "insType":"STATISTIC_GENERAL", "obj":"insurace_fund", "instrument": "integrated", "snapshotInterval":300, "url" : "https://api.bybit.com/v5/market/insurance"},
    {"exchange":"bybit", "insType":"STATISTIC_FUTURES", "obj":"position_Statistic", "instrument": "btc/usdt", "snapshotInterval":300, "url" : "https://api.bybit.com/v5/market/account-ratio?category=linear&symbol=BTCUSDT&period=1d&limit=50"},
    # okx
    {"exchange":"okx", "insType":"STATISTIC_SPOT", "obj":"TakerVolume", "instrument": "integrated", "snapshotInterval":300, "url" : f"https://www.okx.com/api/v5/rubik/stat/taker-volume?ccy=BTC&instType=SPOT&period=5m&begin={int(datetime.timestamp(datetime.now() - timedelta(minutes=5)) * 1000)}"}, # snap every 5 minute
    {"exchange":"okx", "insType":"STATISTIC_CONTRACTS", "obj":"TakerVolume", "instrument": "integrated", "snapshotInterval":300, "url" : f"https://www.okx.com/api/v5/rubik/stat/taker-volume?ccy=BTC&instType=CONTRACTS&period=5m&begin={int(datetime.timestamp(datetime.now() - timedelta(minutes=5)) * 1000)}"},
    {"exchange":"okx", "insType":"STATISTIC_MARGIN", "obj":"CumLandingRatioBTC_to_quote", "snapshotInterval":300, "instrument": "integrated_BTC", "url" : f"https://www.okx.com/api/v5/rubik/stat/margin/loan-ratio?ccy=BTC&begin={int(datetime.timestamp(datetime.now() - timedelta(minutes=5)) * 1000)}"},
    {"exchange":"okx", "insType":"STATISTIC_CONTRACTS", "obj":"netLSratio", "snapshotInterval":300, "instrument": "integrated_BTC", "url" : f"https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio?ccy=BTC&begin={int(datetime.timestamp(datetime.now() - timedelta(minutes=5)) * 1000)}"},
    {"exchange":"okx", "insType":"STATISTIC_CONTRACTS", "obj":"OIVolume_Fut_Perp", "snapshotInterval":300,"instrument": "integrated_BTC", "url" : f"https://www.okx.com/api/v5/rubik/stat/contracts/open-interest-volume?ccy=BTC&begin={int(datetime.timestamp(datetime.now() - timedelta(minutes=5)) * 1000)}"},
    {"exchange":"okx", "insType":"STATISTIC_CONTRACTS", "obj":"OIVolume_Options", "snapshotInterval":300,"instrument": "integrated_BTC", "url" : "https://www.okx.com/api/v5/rubik/stat/option/open-interest-volume?ccy=BTC"}, # every 8 hours. Descending order
    {"exchange":"okx", "insType":"STATISTIC_CONTRACTS", "obj":"Put_Call_Options", "snapshotInterval":300,"instrument": "integrated_BTC", "url" : "https://www.okx.com/api/v5/rubik/stat/option/open-interest-volume-ratio?ccy=BTC"}, # every 8 hours. Descending order
    {"exchange":"okx", "insType":"STATISTIC_CONTRACTS", "obj":"open-interest-volume-expiry", "snapshotInterval":300,"instrument": "integrated_BTC", "url" : "https://www.okx.com/api/v5/rubik/stat/option/open-interest-volume-expiry?ccy=BTC"}, # every 8 hours. Descending order
    {"exchange":"okx", "insType":"STATISTIC_CONTRACTS", "obj":"taker_block_volume", "snapshotInterval":300, "instrument": "integrated_BTC", "url" : "https://www.okx.com/api/v5/rubik/stat/option/taker-block-volume?ccy=BTC"}, # every 8 hours. Descending order
    {"exchange":"okx", "insType":"STATISTIC_MARGIN", "obj":"interest-rate-loan-quota", "snapshotInterval":300, "instrument": "integrated", "url" : "https://www.okx.com/api/v5/public/interest-rate-loan-quota"}, # Call every 8 hours
    {"exchange":"okx", "insType":"STATISTIC_MARGIN", "obj":"vip-interest-rate-loan-quota", "snapshotInterval":300, "instrument": "integrated", "url" : "https://www.okx.com/api/v5/public/vip-interest-rate-loan-quota"}, 
    {"exchange":"okx", "insType":"STATISTIC_GENERAL", "obj":"insurance-fund-MARGIN", "snapshotInterval":300, "instrument":"BTC", "url" : "https://www.okx.com/api/v5/public/insurance-fund?instType=MARGIN&ccy=BTC&limit=1"},  # every 8 hours
    {"exchange":"okx", "insType":"STATISTIC_GENERAL", "obj":"insurance-fund-MARGIN", "snapshotInterval":300, "instrument":"USDT", "url" : "https://www.okx.com/api/v5/public/insurance-fund?instType=MARGIN&ccy=USDT&limit=1"},  # every 8 hours
    {"exchange":"okx", "insType":"STATISTIC_GENERAL", "obj":"insurance-fund-SWAP", "snapshotInterval":300, "instrument":"BTC-USDT", "url" : "https://www.okx.com/api/v5/public/insurance-fund?instType=SWAP&instFamily=BTC-USDT&limit=1"},
    {"exchange":"okx", "insType":"STATISTIC_GENERAL", "obj":"insurance-fund-SWAP", "snapshotInterval":300, "instrument":"BTC-USD", "url" : "https://www.okx.com/api/v5/public/insurance-fund?instType=SWAP&instFamily=BTC-USD&limit=1"},
    {"exchange":"okx", "insType":"STATISTIC_GENERAL", "obj":"insurance-fund-FUTURES", "snapshotInterval":300, "instrument":"BTC-USDT", "url" : "https://www.okx.com/api/v5/public/insurance-fund?instType=FUTURES&instFamily=BTC-USDT&limit=1"},
    {"exchange":"okx", "insType":"STATISTIC_GENERAL", "obj":"insurance-fund-FUTURES", "snapshotInterval":300, "instrument":"BTC-USD", "url" : "https://www.okx.com/api/v5/public/insurance-fund?instType=FUTURES&instFamily=BTC-USD&limit=1"},
    {"exchange":"okx", "insType":"STATISTIC_GENERAL", "obj":"insurance-fund-OPTION", "snapshotInterval":300, "instrument":"BTC-USD", "url" : "https://www.okx.com/api/v5/public/insurance-fund?instType=OPTION&instFamily=BTC-USD&limit=1"},
    # deribit
    {"exchange":"deribit", "insType":"FUTURES", "obj":"summary", "instrument":"BTC_integrated", 
                    "snapshotInterval":3,"url" : "wss://test.deribit.com/ws/api/v2",  "msg" : 
                                                                        {"jsonrpc": "2.0", 
                                                                         "id": generate_random_integer(10), 
                                                                         "method": "public/get_book_summary_by_currency", 
                                                                         "params": { "currency": "BTC", "kind": "future"}}},  # every 5 seconds
    {"exchange":"deribit", "insType":"OPTIONS", "obj":"summary", "instrument":"BTC_integrated", 
                         "snapshotInterval":3,"url" : "wss://test.deribit.com/ws/api/v2",  "msg" : 
                                    {"jsonrpc": "2.0", "id": generate_random_integer(10), 
                                     "method": "public/get_book_summary_by_currency",
                                       "params": { "currency": "BTC", "kind": "option"}}},  # every 5 seconds
    {"exchange":"deribit", "insType":"OPTIONS", "obj":"BVOL", "instrument":"BTC_integrated", 
                                    "snapshotInterval":3,"url" : "wss://test.deribit.com/ws/api/v2", 
                                      "msg" : {"jsonrpc": "2.0", "id": generate_random_integer(10), 
                                               "method": "public/get_volatility_index_data", 
                                               "params": { "currency": "BTC", 
                                                          "start_timestamp": int(datetime.timestamp(datetime.now())), 
                                                          "end_timestamp": int(datetime.timestamp(datetime.now() - timedelta(minutes=5)) * 1000),
                                                            "resolution":"1"}}},
    # NEWS AGGREGATOR
    {"exchange":"Crypto_Panic", "insType":"news", "obj":"aggregator", "instrument":"BTC_USDT_ETH",
                                    "snapshotInterval":30, "url":f'https://cryptopanic.com/api/v1/posts/?auth_token={crypto_panic_token}&public=true&currencies=BTC,USDT,ETH&region=en'},  # Every 30 seconds
    


]

def get_API_stream_names():
    return [e["exchange"]+ "_" + e["insType"]+ "_" +e["obj"]+ "_" +e["instrument"] for e in APIs]

WSs =[
    # Binance spot APIs: https://binance-docs.github.io/apidocs/spot/en/#change-log
    # Binance usdt APIs: https://binance-docs.github.io/apidocs/futures/en/#change-log
    # Binance coin APIs: https://binance-docs.github.io/apidocs/delivery/en/#change-log
    # OKEx: https://www.okx.com/docs-v5/en/?python#public-data-websocket-funding-rate-channel
    # Bybit: https://www.bybit.com/future-activity/en/developer
    # Coinbase: https://docs.cloud.coinbase.com/exchange/docs/websocket-channels
    # Derebit: https://docs.deribit.com/
    # """
        # Binance spot
        { "n": "binance_spot_aggTrade_USDT", "e": "wss://stream.binance.com:9443/ws", "sn": "btcusdt@aggTrade"},  # ok
        { "n": "binance_spot_depth_USDT", "e": "wss://stream.binance.com:9443/ws", "sn": "btcusdt@depth@1000ms"}, # ok
        { "n": "binance_spot_aggTrade_FDUSD", "e": "wss://stream.binance.com:9443/ws", "sn": "btcfdusd@aggTrade"}, # ok
        { "n": "binance_spot_depth_FDUSD", "e": "wss://stream.binance.com:9443/ws", "sn": "btcfdusd@depth@1000ms"}, # ok
        # Binance perpetual usdt
        { "n": "binance_perpetual_aggTrade_USDT", "e": "wss://fstream.binance.com/ws", "sn": "btcusdt@aggTrade"},  # ok
        { "n": "binance_perpetual_depth_USDT", "e": "wss://fstream.binance.com/ws", "sn": "btcusdt@depth@500ms"}, # ok
        { "n": "binance_perpetual_forceOrder_USDT", "e": "wss://fstream.binance.com/ws", "sn": "btcusdt@forceOrder"}, # ok
        # Binance perpetual usd
        { "n": "binance_perpetual_aggTrade_USD", "e": "wss://dstream.binance.com/ws", "sn": "btcusd_perp@aggTrade"}, # ok
        { "n": "binance_perpetual_depth_USD", "e": "wss://dstream.binance.com/ws", "sn": "btcusd_perp@depth@500ms"},  # ok
        { "n": "binance_perpetual_forceOrder_USD", "e": "wss://dstream.binance.com/ws", "sn": "btcusd_perp@forceOrder"}, # ok 
        # Okx
        {'n': 'okx_trades_BTC-USDT-SWAP', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'trades', 'instId': 'BTC-USDT-SWAP'}}, 
        {'n': 'okx_trades_BTC-USD-SWAP', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'trades', 'instId': 'BTC-USD-SWAP'}}, 
        {'n': 'okx_trades_BTC-USDT', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'trades', 'instId': 'BTC-USDT'}}, 
        {'n': 'okx_option-trades_OPTION_BTC-USD', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'option-trades', 'instType': 'OPTION', 'instFamily': 'BTC-USD'}}, 
        {'n': 'okx_books_BTC-USDT-SWAP', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'books', 'instId': 'BTC-USDT-SWAP'}}, 
        {'n': 'okx_books_BTC-USD-SWAP', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'books', 'instId': 'BTC-USD-SWAP'}},
        {'n': 'okx_books_BTC-USDT', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'books', 'instId': 'BTC-USDT'}}, 
        {'n': 'okx_public-struc-block-trades', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'public-struc-block-trades'}}, 
        {'n': 'okx_open-interest_BTC-USDT-SWAP', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'open-interest', 'instId': 'BTC-USDT-SWAP'}}, 
        {'n': 'okx_open-interest_BTC-USD-SWAP', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'open-interest', 'instId': 'BTC-USD-SWAP'}}, 
        {'n': 'okx_funding-rate_BTC-USDT-SWAP', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'funding-rate', 'instId': 'BTC-USDT-SWAP'}}, 
        {'n': 'okx_funding-rate_BTC-USD-SWAP', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'funding-rate', 'instId': 'BTC-USD-SWAP'}}, 
        {'n': 'okx_opt-summary_BTC-USD', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'opt-summary', 'instFamily': 'BTC-USD'}}, 
        {'n': 'okx_liquidation-orders_SWAP', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'liquidation-orders', 'instType': 'SWAP'}},
        {'n': 'okx_liquidation-orders_FUTURES', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'liquidation-orders', 'instType': 'FUTURES'}},
        {'n': 'okx_liquidation-orders_MARGIN', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'liquidation-orders', 'instType': 'MARGIN'}}, 
        {'n': 'okx_liquidation-orders_OPTION', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'liquidation-orders', 'instType': 'OPTION'}}, 
        {'n': 'okx_adl-warning_SWAP_BTC-USDT', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'adl-warning', 'instType': 'SWAP', 'instFamily': 'BTC-USDT'}}, 
        {'n': 'okx_adl-warning_FUTURES_BTC-USDT', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'adl-warning', 'instType': 'FUTURES', 'instFamily': 'BTC-USDT'}}, 
        {'n': 'okx_adl-warning_OPTION_BTC-USDT', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'adl-warning', 'instType': 'OPTION', 'instFamily': 'BTC-USDT'}}, 
        {'n': 'okx_adl-warning_SWAP_BTC-USD', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'adl-warning', 'instType': 'SWAP', 'instFamily': 'BTC-USD'}},
        {'n': 'okx_adl-warning_FUTURES_BTC-USD', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'adl-warning', 'instType': 'FUTURES', 'instFamily': 'BTC-USD'}},
        {'n': 'okx_adl-warning_OPTION_BTC-USD', 'e': 'wss://ws.okx.com:8443/ws/v5/public', 'sn': 
                                                                    {'channel': 'adl-warning', 'instType': 'OPTION', 'instFamily': 'BTC-USD'}},             
        # bybit
        { "n": "bybit_spot_depth_USDT", "e": "wss://stream.bybit.com/v5/public/spot", "sn": "orderbook.200.BTCUSDT"}, # ok
        { "n": "bybit_spot_trades_USDT", "e": "wss://stream.bybit.com/v5/public/spot", "sn": "publicTrade.BTCUSDT"},  # ok
        { "n": "bybit_perpetual_depth_USDT", "e": "wss://stream.bybit.com/v5/public/linear", "sn": "orderbook.200.BTCUSDT"},  # ok
        { "n": "bybit_perpetual_trades_USDT", "e": "wss://stream.bybit.com/v5/public/linear", "sn": "publicTrade.BTCUSDT"},   # ok
        { "n": "bybit_perpetual_forceOrder_USDT", "e": "wss://stream.bybit.com/v5/public/linear", "sn": "liquidation.BTCUSDT"},  # ok
        { "n": "bybit_perpetual_tickers_USDT", "e": "wss://stream.bybit.com/v5/public/linear", "sn": "tickers.BTCUSDT"},  # ok # OI funding turnover etc
        # coinbase
        { "n": "bybit_perpetual_tickers_USDT", "e": "wss://advanced-trade-ws.coinbase.com", "sn": "tickers.BTCUSDT"},
        { "n": "bybit_perpetual_tickers_USDT", "e": "wss://advanced-trade-ws.coinbase.com", "sn": "tickers.BTCUSDT"},
        { "n": "coinbase_heartbeats", "e": "wss://advanced-trade-ws.coinbase.com", "sn": {"type": "subscribe",
                                                                                              "product_ids": ["BTC-USD"], 
                                                                                              "channel": "heartbeats",
                                                                                              "jwt": build_jwt(),
                                                                                              "timestamp": int(time.time())}},
        { "n": "coinbase_spot_depth_USD", "e": "wss://advanced-trade-ws.coinbase.com", "sn": {"type": "subscribe",
                                                                                              "product_ids": ["BTC-USD"], 
                                                                                              "channel": "level2",
                                                                                              "jwt": build_jwt(),
                                                                                              "timestamp": int(time.time())
                                                                                              }},
        { "n": "coinbase_spot_depth_USD", "e": "wss://advanced-trade-ws.coinbase.com", "sn": {"type": "subscribe",
                                                                                              "product_ids": ["BTC-USD"], 
                                                                                              "channel": "market_trades",
                                                                                              "jwt": build_jwt(),
                                                                                              "timestamp": int(time.time())
                                                                                              }},
                                                                                              ]



wallets = {
    
}


# url_params = urlencode(WSs[-1]["sn"])
# base_url = WSs[-1]["e"]
# final_url = f"{base_url}?{url_params}"
# print(final_url)

# import http.client
# import json

# conn = http.client.HTTPSConnection("api.coinbase.com")
# payload = ''
# headers = {
#   'Content-Type': 'application/json'
# }
# conn.request("GET", "/api/v3/brokerage/product_book", payload, headers)
# res = conn.getresponse()
# data = res.read()
# print(data.decode("utf-8"))


# import requests
# import json
# d =  {"exchange":"bybit", "insType":"STATISTIC_FUTURES", 
#   "obj":"position_Statistic", "instrument": "btc/usdt",
#     "snapshotInterval":300, "url" : 
#     "https://api.bybit.com/v5/market/tickers?category=option"}

# bybit = "https://api.bybit.com/v5/market/tickers?category=option"
# okx = "https://www.okx.com/api/v5/public/open-interest?instType=OPTION&instFamily=BTC-USD"

# response = requests.get("https://www.okx.com/api/v5/public/open-interest?instType=OPTION&instFamily=BTC-USD")
# data = response.json()

# with open("option_okex.json", 'w') as json_file:
#     json.dump(data, json_file, indent=4)