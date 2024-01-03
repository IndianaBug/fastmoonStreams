import requests
from datetime import datetime
import concurrent.futures
import time
import sched
from threading import Thread, Lock
import asyncio
import websockets
import json


# BINANCE #
############################

# Order Book
class combined_API():
    """
        Params :  { the length of the orderbook snapshot of ... 1 - 4,
                    websocket uri for streaming
    """

    def __init__(self, 
                 binance_spot_books_usdt_snapshot_limit,
                 binance_spot_books_fdusd_snapshot_limit,
                 binance_futures_books_usdt_snapshot_limit,
                 binance_futures_books_usd_snapshot_limit,
                 websocket_uri
                 ):
        # BINANCE #
        # Books
        self.binance_spot_books_usdt_url = f"https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit={binance_spot_books_usdt_snapshot_limit}"
        self.binance_spot_books_fdusd_url = f"https://api.binance.com/api/v3/depth?symbol=BTCFDUSD&limit={binance_spot_books_fdusd_snapshot_limit}"
        self.binance_futures_books_usdt_url = f"https://api.binance.com/api/v3/depth?symbol=BTCFDUSD&limit={binance_futures_books_usdt_snapshot_limit}"
        self.binance_futures_books_usd_url = f"https://dapi.binance.com/dapi/v1/depth?symbol=BTCUSD_PERP&limit={binance_futures_books_usd_snapshot_limit}"
        # Funding
        self.binance_futures_funding_usdt_url = "https://fapi.binance.com/fapi/v1/premiumIndex" # Predicted funding rate. Do not forget to update funding rate every 8 hours
        self.binance_futures_funding_usdt_params = {"symbol":"BTCUSDT"}                         # Update every 5 minute
        self.binance_futures_funding_usdt_name = "binance_futures_funding_usdt"
        self.binance_futures_funding_usd_url = "https://dapi.binance.com/dapi/v1/fundingRate" # Simple funding rate
        self.binance_futures_funding_usd_params = {"symbol":"BTCUSD_PERP"}                    # Update every 5 minute
        self.binance_futures_funding_usd_name = "binance_futures_funding_usd"        
        # OI
        self.binance_futures_OI_usdt_url = "https://fapi.binance.com/fapi/v1/openInterest" # Update every 3 seconds
        self.binance_futures_OI_usdt_params = {"symbol":"BTCUSDT"}
        self.binance_futures_OI_usdt_name = "binance_futures_OI_usdt"        
        self.binance_futures_OI_usd_url = "https://dapi.binance.com/dapi/v1/openInterest" 
        self.binance_futures_OI_usd_params = {"symbol":"BTCUSD_PERP"} 
        self.binance_futures_OI_usd_name = "binance_futures_OI_usd"          
        # Top traders Account
        self.binance_futures_TTA_usdt_url = "https://fapi.binance.com/futures/data/topLongShortAccountRatio" # Update every 5 minute
        self.binance_futures_TTA_usdt_params = {"symbol":"BTCUSDT", "period": "5m", "limit": 1}
        self.binance_futures_TTA_usdt_name = "binance_futures_TTA_usdt"        
        self.binance_futures_TTA_usd_url = "https://dapi.binance.com/futures/data/topLongShortAccountRatio" 
        self.binance_futures_TTA_usd_params = {"pair":"BTCUSD", "period": "5m", "limit": 1} 
        self.binance_futures_TTA_usd_name = "binance_futures_TTA_usd"        
        # Top traders positions
        self.binance_futures_TTP_usdt_url = "https://fapi.binance.com/futures/data/topLongShortPositionRatio" # Update every 5 minute
        self.binance_futures_TTP_usdt_params = {"symbol":"BTCUSDT", "period": "5m", "limit": 1}
        self.binance_futures_TTP_usd_name = "binance_futures_TTP_usdt"        
        self.binance_futures_TTP_usd_url = "https://dapi.binance.com/futures/data/topLongShortPositionRatio" 
        self.binance_futures_TTP_usd_params = {"pair":"BTCUSD", "period": "5m", "limit": 1} 
        self.binance_futures_TTP_usd_name = "binance_futures_TTP_usd"        
        # Global traders Account
        self.binance_futures_GTP_usdt_url = "https://fapi.binance.com/futures/data/globalLongShortAccountRatio" # Update every 5 minute
        self.binance_futures_GTP_usdt_params = {"symbol":"BTCUSDT", "period": "5m", "limit": 1}
        self.binance_futures_GTP_usd_name = "binance_futures_GTP_usdt"        
        self.binance_futures_GTP_usd_url = "https://dapi.binance.com/futures/data/globalLongShortAccountRatio" 
        self.binance_futures_GTP_usd_params = {"pair":"BTCUSD", "period": "5m", "limit": 1}
        self.binance_futures_GTP_usd_name = "binance_futures_GTP_usd"        
        # OKEX #


        # Fetched data
        self.websocket_uri = websocket_uri
        self.lock = Lock()
        self.fetched_API_calls = {}
         

    def fetch_data(self, url, name, params={}, is_book=False):
        r = requests.get(url, params=params)
        if r.status_code == 200:
            data = r.json()
            if is_book == False:
                #self.fetched_API_calls[name] = data
                # asyncio.run(self.send_to_websocket(json.dumps(self.fetched_API_calls)))
                print(self.fetched_API_calls)
                return {name:data}
            if is_book == True:
                return data
        else:
            print(f"Error: {r.status_code}")
            return None
    
    async def send_to_websocket(self, data):
        async with websockets.connect(self.websocket_uri) as websocket:
            await websocket.send(data)
    
    def fetching_helper(self, max_workers, fetch_interval, api_endpoints, names, paramss):

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            while True:
                for url, name, params in zip(api_endpoints, names, paramss):
                    result = self.fetch_data(url, name, params)
                    self.fetched_API_calls[name] = result
                with self.lock:
                    # Send to the WebSocket server
                    asyncio.run(self.send_to_websocket(json.dumps(self.fetched_API_calls)))
                time.sleep(fetch_interval)

    
    def concurrent_fetching_stream(self):
        second_thread = Thread(target = self.fetching_helper, args=((5, 3, [self.binance_futures_OI_usdt_url], 
                                                                            [self.binance_futures_OI_usdt_name], 
                                                                            [self.binance_futures_OI_usdt_params])))
        minute_thread = Thread(target = self.fetching_helper, args=((5, 5, [self.binance_futures_OI_usd_url], 
                                                                            [self.binance_futures_OI_usd_name], 
                                                                            [self.binance_futures_OI_usd_params])))
        second_thread.start()
        minute_thread.start()
        second_thread.join()
        minute_thread.join()

    def miliseconds_to_strftime(self, data: int) -> str:
        return datetime.utcfromtimestamp(data / 1000.0).strftime('%Y-%m-%d %H:%M:%S UTC')



# loader = combined_API(5000, 5000, 5000, 1000, "some_websocket")
# start_time = time.time()
# loader.concurrent_fetching_stream()
# elapsed_time = time.time() - start_time
# print(f"Execution time: {elapsed_time} seconds")


