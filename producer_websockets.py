import websockets
import asyncio
import time
import json
import requests
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaStorageError
from collections import Counter
import ssl
import random
import okx.PublicData as PublicData

# ! pip install python-okx --upgrade


ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def generate_random_integer(n):
    if n <= 0:
        raise ValueError("Length should be a positive integer")
    lower_bound = 10 ** (n - 1)
    upper_bound = (10 ** n) - 1
    random_integer = random.randint(lower_bound, upper_bound)
    return random_integer

class WebSocketClient():

    """
        OKEx: https://www.okx.com/docs-v5/en/?python#public-data-websocket-funding-rate-channel
    """


    def __init__ (self, host, **kwards):
        
        self.host = host
        
        # Binance
        self.binance_spot_basepoint = "wss://stream.binance.com:9443"
        self.binance_spot_request = json.loads({"method": "SUBSCRIBE", "params": ["btcusdt@aggTrade", 
                                                                                  "btcusdt@depth@100ms", 
                                                                                  "btcfdusd@aggTrade", 
                                                                                  "btcfdus@depth@100ms"], 
                                                                                  "id": generate_random_integer(10)})
        self.binance_usdtFutures_basepoint = "wss://fstream.binance.com"
        self.binance_usdtFutures_request = json.loads({"method": "SUBSCRIBE", "params": ["btcusdt@aggTrade", 
                                                                                         "btcusdt@depth@100ms",
                                                                                         "btcusdt@forceOrder"], 
                                                                                         "id": generate_random_integer(10)})
        self.binance_usdtFutures_basepoint = "wss://dstream.binance.com"
        self.binance_usdtFutures_request = json.loads({"method": "SUBSCRIBE", "params": ["btcusdt_perp@aggTrade", 
                                                                                         "btcusdt_perp@depth@100ms",
                                                                                         "btcusdt_perp@forceOrder"], 
                                                                                         "id": generate_random_integer(10)})
        # OKEx
        # BTC-USDT-SWAP, BTC-USD-SWAP, BTC-USDT, option summary, economic calendar, adl warning, liquidation order
        self.okx_endpoint = "wss://ws.okx.com:8443/ws/v5/public"
        self.okex_open_interest_params_usdt = {"event": "subscribe", 
                                               "arg": [{"channel": "open-interest", 
                                                        "instId": "BTC-USDT-SWAP"}], 
                                                "connId": str(generate_random_integer(10))}
        self.okex_open_interest_params_usd = {"event": "subscribe", 
                                               "arg": [{"channel": "open-interest", 
                                                        "instId": "BTC-USD-SWAP"}], 
                                                "connId": str(generate_random_integer(10))}
        self.okex_funding_params_usdt = {"event": "subscribe", 
                                               "arg": [{"channel": "funding-rate", 
                                                        "instId": "BTC-USDT-SWAP"}], 
                                                "connId": str(generate_random_integer(10))}
        self.okex_funding_params_usd = {"event": "subscribe", 
                                               "arg": [{"channel": "funding-rate", 
                                                        "instId": "BTC-USD-SWAP"}], 
                                                "connId": str(generate_random_integer(10))}
        self.okex_optionSummary = {"event": "subscribe", 
                                               "arg": [{"channel": "opt-summary", 
                                                        "instId": "BTC-USD"}], 
                                                "connId": str(generate_random_integer(10))}


        # Bybit

        # Bitget

        # Derebit

        # Kucoin

        # Coinbase

    
    async def keep_alive_bitget(self, websocket, ping_interval=30):
        while True:
            try:
                # Send a ping message to the server.
                await asyncio.sleep(ping_interval)
                await websocket.send('ping')
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed. Stopping keep-alive.")
                break
    
    async def keep_alive_binance(self, websocket, ping_interval=30):
        while True:
            try:
                # Send a ping message to the server.
                await websocket.pong()
                await asyncio.sleep(ping_interval)
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed. Stopping keep-alive.")
                break

    async def bitget_websockets(self, bitget_stream, data_auth, producer, topic):
        async for websocket in websockets.connect(bitget_stream, ping_interval=None, timeout=86400, ssl=ssl_context): #as websocket:
            await websocket.send(data_auth)
            keep_alive_task = asyncio.create_task(self.keep_alive_bitget(websocket, 30))
            try:
                async for message in websocket:
                    try:
                        message = await websocket.recv()
                        await producer.send_and_wait(topic=topic, value=str(message).encode())
                        print(f'Bitget_{topic} recieved')
                    except KafkaStorageError as e:
                        print(f"KafkaStorageError: {e}")
                        await asyncio.sleep(5)
                        continue
            except asyncio.exceptions.TimeoutError:
                print("WebSocket operation timed out")
                await asyncio.sleep(5)
                continue
            except websockets.exceptions.ConnectionClosed:
                print("connection  closed of bitget stream, reconnecting!!!")
                await asyncio.sleep(5)
                continue
        

    async def binance_websockets(self, binance_stream, producer, topic):
        ticker = binance_stream.split('/')[-1].split('@')[0]
        async for websocket in websockets.connect(binance_stream, ping_interval=None, timeout=86400):
            keep_alive_task = asyncio.create_task(self.keep_alive_binance(websocket, 30))
            try:
                async for message in websocket:
                    try:
                        if topic == 'binance_spot':
                            await producer.send_and_wait(topic=topic, value=json.dumps({ticker: json.loads(message)}).encode())
                        else:
                            await producer.send_and_wait(topic=topic, value=str(message).encode())
                        #print(json.dumps({ticker: json.loads(message)}).encode())
                        print(f'Binance_{topic} recieved')
                    except KafkaStorageError as e:
                        print(f"KafkaStorageError: {e}")
            except asyncio.exceptions.TimeoutError:
                await asyncio.sleep(5)
                print("WebSocket operation timed out")
            except websockets.exceptions.ConnectionClosed:
                print("connection  closed of binance stream, reconnecting!!!")
                await asyncio.sleep(5)
                continue

    async def main(self):
        producer = AIOKafkaProducer(bootstrap_servers=self.host)
        await producer.start()
        #producer = ''
        tasks = []
        tasks += [self.binance_websockets(stream.lower(), producer, 'binance') for stream in self.binance_futures_authenticators]
        tasks +=  [self.bitget_websockets(bitget_stream=self.bitget_futures_stream, data_auth=self.bitget_futures_authenticators, producer=producer, topic='bitget')]
        try:
            await asyncio.gather(*tasks)
        finally:
            await producer.stop()

if __name__ == '__main__':
    client = WebSocketClient(host='localhost:9092')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(client.main())



# Notes
    
#     {
#   "e": "aggTrade",  // Event type
#   "E": 1672515782136,   // Event time
#   "s": "BNBBTC",    // Symbol
#   "a": 12345,       // Aggregate trade ID
#   "p": "0.001",     // Price
#   "q": "100",       // Quantity
#   "f": 100,         // First trade ID
#   "l": 105,         // Last trade ID
#   "T": 1672515782136,   // Trade time
#   "m": true,        // Is the buyer the market maker?
#   "M": true         // Ignore
# }
    

# https://binance-docs.github.io/apidocs/spot/en/#diff-depth-stream
# {
#   "e": "depthUpdate", // Event type
#   "E": 1672515782136,     // Event time
#   "s": "BNBBTC",      // Symbol
#   "U": 157,           // First update ID in event
#   "u": 160,           // Final update ID in event
#   "b": [              // Bids to be updated
#     [
#       "0.0024",       // Price level to be updated
#       "10"            // Quantity
#     ]
#   ],
#   "a": [              // Asks to be updated
#     [
#       "0.0026",       // Price level to be updated
#       "100"           // Quantity
#     ]
#   ]
# }
    

# Open a stream to wss://stream.binance.com:9443/ws/bnbbtc@depth.
# Buffer the events you receive from the stream.
# Get a depth snapshot from https://api.binance.com/api/v3/depth?symbol=BNBBTC&limit=1000 .
# Drop any event where u is <= lastUpdateId in the snapshot.
# The first processed event should have U <= lastUpdateId+1 AND u >= lastUpdateId+1.
# While listening to the stream, each new event's U should be equal to the previous event's u+1.
# The data in each event is the absolute quantity for a price level.
# If the quantity is 0, remove the price level.
# Receiving an event that removes a price level that is not in your local order book can happen and is normal.
    

# Liquidation order
    
#     { https://binance-docs.github.io/apidocs/futures/en/#liquidation-order-streams

#     "e":"forceOrder",                   // Event Type
#     "E":1568014460893,                  // Event Time
#     "o":{

#         "s":"BTCUSDT",                   // Symbol
#         "S":"SELL",                      // Side
#         "o":"LIMIT",                     // Order Type
#         "f":"IOC",                       // Time in Force
#         "q":"0.014",                     // Original Quantity
#         "p":"9910",                      // Price
#         "ap":"9910",                     // Average Price
#         "X":"FILLED",                    // Order Status
#         "l":"0.014",                     // Order Last Filled Quantity
#         "z":"0.014",                     // Order Filled Accumulated Quantity
#         "T":1568014460893,              // Order Trade Time

#     }

# }