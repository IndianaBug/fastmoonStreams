import requests
from datetime import datetime, timedelta
import concurrent.futures
import time
from threading import Thread, Lock
import asyncio
import websockets
import json
import random

def miliseconds_to_strftime(data) -> str:
    return datetime.utcfromtimestamp(int(data) / 1000.0).strftime('%Y-%m-%d %H:%M:%S UTC')

def generate_random_integer(n):
    if n <= 0:
        raise ValueError("Length should be a positive integer")
    lower_bound = 10 ** (n - 1)
    upper_bound = (10 ** n) - 1
    random_integer = random.randint(lower_bound, upper_bound)
    return random_integer


# to do ;
# okx economic calendar
# Coinbase websockets books. Needs authentication

class combined_API():
    """
        Params :  { the length of the orderbook snapshot of ... 1 - 4,

                    websocket uri for streaming

                    Binance APIs : https://binance-docs.github.io/apidocs/spot/en/#change-log
                                   https://binance-docs.github.io/apidocs/futures/en/#change-log
                                   https://binance-docs.github.io/apidocs/delivery/en/#change-log
                    OKEx APIs:     https://www.okx.com/docs-v5/en/?python#public-data-rest-api-get-instruments
                    Bybit APIs:    https://bybit-exchange.github.io/docs/v5/intro
                    Deribit APIs:  https://docs.deribit.com/#deribit-api-v2-1-1
    """

    def __init__(self, 
                 binance_spot_books_usdt_snapshot_limit, # 1000 must e enough
                 binance_spot_books_fdusd_snapshot_limit,
                 binance_futures_books_usdt_snapshot_limit,
                 binance_futures_books_usd_snapshot_limit,  
                 websocket_uri
                 ):

        self.APIs = [

            {"exchange":"binance", "insType":"SPOT", "obj":"depth", "instrument": "btc/usdt", "snapshotInterval":1, "url" : f"https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit={binance_spot_books_usdt_snapshot_limit}"},
            {"exchange":"binance", "insType":"SPOT", "obj":"depth", "instrument": "btc/fdusd", "snapshotInterval":1, "url" : f"https://api.binance.com/api/v3/depth?symbol=BTCFDUSD&limit={binance_spot_books_fdusd_snapshot_limit}"},
            {"exchange":"binance", "insType":"PERPETUAL", "obj":"depth", "instrument": "btc/usdt", "snapshotInterval":1, "url" : f"https://fapi.binance.com/fapi/v1/depth?symbol=BTCUSDT&limit={binance_futures_books_usdt_snapshot_limit}"},
            {"exchange":"binance", "insType":"PERPETUAL", "obj":"depth", "instrument": "btc/usd", "snapshotInterval":1, "url" : f"https://dapi.binance.com/dapi/v1/depth?symbol=BTCUSD_PERP&limit={binance_futures_books_usd_snapshot_limit}"},
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
            {"exchange":"bybit", "insType":"STATISTIC_GENERAL", "obj":"insurace_fund", "instrument": "integrated", "snapshotInterval":300, "url" : "https://api.bybit.com/v5/market/insurance"},
            {"exchange":"bybit", "insType":"STATISTIC_FUTURES", "obj":"position_Statistic", "instrument": "btc/usdt", "snapshotInterval":300, "url" : "https://api.bybit.com/v5/market/account-ratio?category=linear&symbol=BTCUSDT&period=1d&limit=50"},
            {"exchange":"okx", "insType":"STATISTIC_SPOT", "obj":"TakerVolume", "instrument": "integrated", "snapshotInterval":300, "url" : f"https://www.okx.com/api/v5/rubik/stat/taker-volume?ccy=BTC&instType=SPOT&period=5m&begin={int(datetime.timestamp(datetime.now() - timedelta(minutes=5)) * 1000)}"}, # snap every 5 minute
            {"exchange":"okx", "insType":"STATISTIC_CONTRACTS", "obj":"TakerVolume", "instrument": "integrated", "snapshotInterval":300, "url" : f"https://www.okx.com/api/v5/rubik/stat/taker-volume?ccy=BTC&instType=CONTRACTS&period=5m&begin={int(datetime.timestamp(datetime.now() - timedelta(minutes=5)) * 1000)}"},
            {"exchange":"okx", "insType":"STATISTIC_MARGIN", "obj":"CumLandingRatioBTC_to_quote", "snapshotInterval":300, "instrument": "integrated_BTC", "url" : f"https://www.okx.com/api/v5/rubik/stat/margin/loan-ratio?ccy=BTC&begin={int(datetime.timestamp(datetime.now() - timedelta(minutes=5)) * 1000)}"},
            {"exchange":"okx", "insType":"STATISTIC_CONTRACTS", "obj":"netLSratio", "snapshotInterval":300, "instrument": "integrated_BTC", "url" : f"https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio?ccy=BTC&begin={int(datetime.timestamp(datetime.now() - timedelta(minutes=5)) * 1000)}"},
            {"exchange":"okx", "insType":"STATISTIC_CONTRACTS", "obj":"OIVolume_Fut_Perp", "snapshotInterval":300,"instrument": "integrated_BTC", "url" : f"https://www.okx.com/api/v5/rubik/stat/contracts/open-interest-volume?ccy=BTC&begin={int(datetime.timestamp(datetime.now() - timedelta(minutes=5)) * 1000)}"},
            {"exchange":"okx", "insType":"STATISTIC_CONTRACTS", "obj":"OIVolume_Options", "snapshotInterval":300,"instrument": "integrated_BTC", "url" : "https://www.okx.com/api/v5/rubik/stat/option/open-interest-volume?ccy=BTC"}, # every 8 hours. Descending order
            {"exchange":"okx", "insType":"STATISTIC_CONTRACTS", "obj":"Put_Call_Options", "snapshotInterval":300,"instrument": "integrated_BTC", "url" : "https://www.okx.com/api/v5/rubik/stat/option/open-interest-volume-ratio?ccy=BTC"}, # every 8 hours. Descending order
            {"exchange":"okx", "insType":"STATISTIC_CONTRACTS", "obj":"open-interest-volume-expiry", "snapshotInterval":300,"instrument": "integrated_BTC", "url" : "https://www.okx.com/api/v5/rubik/stat/option/open-interest-volume-expiry?ccy=BTC"}, # every 8 hours. Descending order
            {"exchange":"okx", "insType":"STATISTIC_CONTRACTS", "obj":"taker_block_volume", "snapshotInterval":300, "instrument": "integrated_BTC", "url" : "https://www.okx.com/api/v5/rubik/stat/option/taker-block-volume?ccy=BTC"}, # every 8 hours. Descending order
            # {"exchange":"okx", "insType":"STATISTIC_GENERAL", "obj":"calendar", "snapshotInterval":300, "instrument": "integrated", "url" : "https://www.okx.com/api/v5/public/economic-calendar"}, # Need authentication
            {"exchange":"okx", "insType":"STATISTIC_MARGIN", "obj":"interest-rate-loan-quota", "snapshotInterval":300, "instrument": "integrated", "url" : "https://www.okx.com/api/v5/public/interest-rate-loan-quota"}, # Call every 8 hours
            {"exchange":"okx", "insType":"STATISTIC_MARGIN", "obj":"vip-interest-rate-loan-quota", "snapshotInterval":300, "instrument": "integrated", "url" : "https://www.okx.com/api/v5/public/vip-interest-rate-loan-quota"}, 
            {"exchange":"okx", "insType":"STATISTIC_GENERAL", "obj":"insurance-fund-MARGIN", "snapshotInterval":300, "instrument":"BTC", "url" : "https://www.okx.com/api/v5/public/insurance-fund?instType=MARGIN&ccy=BTC&limit=1"},  # every 8 hours
            {"exchange":"okx", "insType":"STATISTIC_GENERAL", "obj":"insurance-fund-MARGIN", "snapshotInterval":300, "instrument":"USDT", "url" : "https://www.okx.com/api/v5/public/insurance-fund?instType=MARGIN&ccy=USDT&limit=1"},  # every 8 hours
            {"exchange":"okx", "insType":"STATISTIC_GENERAL", "obj":"insurance-fund-SWAP", "snapshotInterval":300, "instrument":"BTC-USDT", "url" : "https://www.okx.com/api/v5/public/insurance-fund?instType=SWAP&instFamily=BTC-USDT&limit=1"},
            {"exchange":"okx", "insType":"STATISTIC_GENERAL", "obj":"insurance-fund-SWAP", "snapshotInterval":300, "instrument":"BTC-USD", "url" : "https://www.okx.com/api/v5/public/insurance-fund?instType=SWAP&instFamily=BTC-USD&limit=1"},
            {"exchange":"okx", "insType":"STATISTIC_GENERAL", "obj":"insurance-fund-FUTURES", "snapshotInterval":300, "instrument":"BTC-USDT", "url" : "https://www.okx.com/api/v5/public/insurance-fund?instType=FUTURES&instFamily=BTC-USDT&limit=1"},
            {"exchange":"okx", "insType":"STATISTIC_GENERAL", "obj":"insurance-fund-FUTURES", "snapshotInterval":300, "instrument":"BTC-USD", "url" : "https://www.okx.com/api/v5/public/insurance-fund?instType=FUTURES&instFamily=BTC-USD&limit=1"},
            {"exchange":"okx", "insType":"STATISTIC_GENERAL", "obj":"insurance-fund-OPTION", "snapshotInterval":300, "instrument":"BTC-USD", "url" : "https://www.okx.com/api/v5/public/insurance-fund?instType=OPTION&instFamily=BTC-USD&limit=1"},
            {"exchange":"deribit", "insType":"FUTURES", "obj":"summary", "instrument":"BTC_integrated", "snapshotInterval":3,"url" : "wss://test.deribit.com/ws/api/v2",  "msg" : {"jsonrpc": "2.0", "id": generate_random_integer(10), "method": "public/get_book_summary_by_currency", "params": { "currency": "BTC", "kind": "future"}}},  # every 5 seconds
            {"exchange":"deribit", "insType":"OPTIONS", "obj":"summary", "instrument":"BTC_integrated", "snapshotInterval":3,"url" : "wss://test.deribit.com/ws/api/v2",  "msg" : {"jsonrpc": "2.0", "id": generate_random_integer(10), "method": "public/get_book_summary_by_currency", "params": { "currency": "BTC", "kind": "option"}}},  # every 5 seconds

        ]

        # Fetched data
        self.websocket_uri = websocket_uri
        self.lock = Lock()
        self.fetched_API_calls = {}

    def get_stream_names(self):
        return [e["exchange"]+ "_" + e["insType"]+ "_" +e["obj"]+ "_" +e["instrument"] for e in self.APIs]
    
    def get_stream_name(self, e):
        return e["exchange"]+ "_" +e["insType"]+ "_" +e["obj"]+ "_" +e["instrument"] 

    async def fetch_data_websockets(self, data_dict):
        # For derebit
        async def call_api():
            async with websockets.connect(data_dict["url"]) as websocket:
                await websocket.send(json.dumps(data_dict["msg"]))
                return await websocket.recv()
        async def main():
            result = await call_api()
            return result
        asyncio.run(main())
        response = await main()
        return response
         

    def fetch_data(self, data_dict):
        r = requests.get(data_dict["url"])
        if r.status_code == 200:
            data = r.json()
            return data
        else:
            print(f"Error: {r.status_code}")
            return None
    
    async def send_to_websocket(self, data):
        async with websockets.connect(self.websocket_uri) as websocket:
            await websocket.send(data)
    
    def fetching_helper(self, max_workers, fetch_interval, data):

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            while True:
                for data_dict in data:
                    if data_dict["exchange"] == "deribit":
                        result = self.fetch_data_websockets(json.dumps(data_dict["msg"]))
                    else:
                        result = self.fetch_data(data_dict)
                    self.fetched_API_calls[self.get_stream_name(data_dict)] = result
                    print(self.fetched_API_calls.keys())
                with self.lock:
                    # Send to the WebSocket server
                    asyncio.run(self.send_to_websocket(json.dumps(self.fetched_API_calls)))
                time.sleep(fetch_interval)

    
    def concurrent_fetching_stream(self):
        second_thread = Thread(target = self.fetching_helper, args=((50, 3, [x for x in self.APIs if x["snapshotInterval"] == 3 and x["obj"] != "depth" ])))
        minute_thread = Thread(target = self.fetching_helper, args=((50, 10, [x for x in self.APIs if x["snapshotInterval"] == 300 and x["obj"] != "depth" ])))
        
        second_thread.start()
        minute_thread.start()
        second_thread.join()
        minute_thread.join()

    def miliseconds_to_strftime(self, data: int) -> str:
        return datetime.utcfromtimestamp(data / 1000.0).strftime('%Y-%m-%d %H:%M:%S UTC')



loader = combined_API(1000, 1000, 1000, 1000, "some_websocket")
start_time = time.time()
a = loader.fetch_data_websockets(loader.APIs[-1])

print(a)
elapsed_time = time.time() - start_time
print(f"Execution time: {elapsed_time} seconds")



    # def test_api(self):

    #     for e in self.APIs:
    #         try:
    #             if e["exchange"] != "deribit":
    #                 r = requests.get(e["url"])
    #                 if r.status_code != 200:
    #                     print(e)
    #             else:
    #                 async def call_api(msg):
    #                     async with websockets.connect(e["url"]) as websocket:
    #                         await websocket.send(msg)
    #                         response = await websocket.recv()
    #                         print(response)
    #                 async def main():
    #                     await call_api(json.dumps(e["msg"]))
    #                 asyncio.run(main())
    #         except:
    #             print(e["exchange"], e["insType"], e["obj"], "not working")
    #         time.sleep(2)


