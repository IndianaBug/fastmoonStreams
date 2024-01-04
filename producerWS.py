import websockets
import asyncio
import json
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaStorageError
import ssl
import random


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
        Binance APIs : https://binance-docs.github.io/apidocs/spot/en/#change-log
                       https://binance-docs.github.io/apidocs/futures/en/#change-log
                       https://binance-docs.github.io/apidocs/delivery/en/#change-log
        OKEx: https://www.okx.com/docs-v5/en/?python#public-data-websocket-funding-rate-channel
        Bybit: https://www.bybit.com/future-activity/en/developer
        Coinbase: https://docs.cloud.coinbase.com/exchange/docs/websocket-channels
        Bitget: https://www.bitget.com/api-doc/contract/intro
        Derebit: https://docs.deribit.com/
    """


    def __init__ (self, host, **kwards):
        
        self.host = host
        self.connection_data = {"binance": {
                                    "exchange":"binance",
                                    "spot" : {
                                        "type":"spot",
                                        "endpoint" : "wss://stream.binance.com:9443/ws",
                                        "streamNames" : { "aggTrade_USDT" : {"n": "spot_aggTrade_USDT", "sn" : "btcusdt@aggTrade"}, 
                                                          "depth_USDT" : {"n":"spot_depth_USDT", "sn" :"btcusdt@depth@1000ms"}, 
                                                          "aggTrade_FDUSD" : {"n":"spot_aggTrade_FDUSD","sn" :"btcfdusd@aggTrade"}, 
                                                          "depth_FDUSD" : {"n":"spot_depth_FDUSD","sn" : "btcfdusd@depth@1000ms"}}
                                    },
                                    "perpetual_usdt" : {
                                        "type":"perpetual_usdt",
                                        "endpoint" : "wss://fstream.binance.com/ws",
                                        "streamNames" : {"aggTrade_USDT" : {"n": "aggTrade_USDT", "sn" : "btcusdt@aggTrade"}, 
                                                         "depth_USDT" : {"n":"depth_USDT", "sn" :"btcusdt@depth@1000ms"}, 
                                                         "forceOrder_USDT" : {"n":"forceOrder_USDT","sn" :"btcusdt@forceOrder"}}
                                    },
                                    "perpetual_usd" : {
                                        "type":"perpetual_usd",
                                        "endpoint" : "wss://dstream.binance.com/ws",
                                        "streamNames" : {"n": "aggTrade_USD", "sn" : "btcusd_perp@aggTrade", 
                                                         "n":"depth_USD", "sn" :"btcusd_perp@depth@1000ms", 
                                                         "n":"forceOrder_USD","sn" :"btcusd_perp@forceOrder"}
                                    }},
                                "okx": {
                                    "exchange":"okx",
                                    "endpoint" : "wss://ws.okx.com:8443/ws/v5/public", 
                                    "args" : {

                                             }
                                    }
                                }


    def parse_params(self, arg, exchange):
        if exchange == "binance": 
            return json.dumps({"method": "SUBSCRIBE", "params": [arg], "id": generate_random_integer(10)})

    async def keep_alive(self, websocket, exchange, ping_interval=30):
        while True:
            try:
                if exchange == "binance":
                    await websocket.pong()
                    await asyncio.sleep(ping_interval)
                if exchange == "bitget":
                    await asyncio.sleep(ping_interval)
                    await websocket.send('ping')                    
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed. Stopping keep-alive.")
                break

    async def websocket_connection(self, exchange, type_, endpoint, authentication, producer, topic):
        """
            type: usdt marginated, futures, coin marginated, perpetual, spot ....
            authentication: websocket request params
            producer: websockets producers name
            topic: aiokafka topic
        """
        async for websocket in websockets.connect(endpoint, ping_interval=None, timeout=86400, ssl=ssl_context):
            await websocket.send(self.parse_params(authentication, exchange=exchange))
            keep_alive_task = asyncio.create_task(self.keep_alive(websocket, exchange, 30))
            try:
                async for message in websocket:
                    try:
                        message = await websocket.recv()
                        #await producer.send_and_wait(topic=topic, value=str(message).encode())
                        print(type_, authentication, message)
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

    async def main(self):
        """
            Gather all websockets
        """
        #producer = AIOKafkaProducer(bootstrap_servers=self.host)
        #await producer.start()
        producer = ''
        topic = ''
        tasks = []
        tasks +=  [self.websocket_connection(exchange=self.connection_data["binance"]["exchange"], 
                                             type_=self.connection_data["binance"]["spot"]["type"],
                                             endpoint=self.connection_data["binance"]["spot"]["endpoint"], 
                                             authentication=self.connection_data["binance"]["spot"]["streamNames"]["depth_FDUSD"]["sn"], 
                                             producer=producer, 
                                             topic=topic)]
        await asyncio.gather(*tasks) 
        # try:
        #     await asyncio.gather(*tasks)
        # finally:
        #     await producer.stop()

if __name__ == '__main__':
    client = WebSocketClient(host='localhost:9092')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(client.main())

# # The value you want to find the key for
# target_value = "https://api.binance.com/api/v3"

# # Iterate through the nested dictionary to find the key
# for parent_key, child_dict in connection_data["binance"]["endpoints"].items():
#     for key, value in child_dict.items():
#         if value == target_value:
#             print("Found key:", key)
#             break
#     else:
#         continue
#     break



# TEST websockets

# from locust import HttpUser, task, between
# from locust.contrib.fasthttp import FastHttpUser
# import json
# import websocket

# class WebSocketUser(FastHttpUser):
#     wait_time = between(1, 5)  # Time between subsequent requests

#     def on_start(self):
#         # Called when a user starts executing tasks
#         self.ws_url = "ws://your-websocket-server-url"

#     @task
#     def websocket_task(self):
#         # Connect to the WebSocket
#         ws = websocket.create_connection(self.ws_url)

#         # Define your WebSocket message payload
#         message_payload = {"type": "ping", "data": "Hello, WebSocket!"}
#         ws.send(json.dumps(message_payload))

#         # Receive the response from the WebSocket server
#         response = ws.recv()
#         print("Received response:", response)

#         # Close the WebSocket connection
#         ws.close()

#     def on_stop(self):
#         # Called when a user stops executing tasks
#         pass




        # # Binance

        # # OKEx
        # # BTC-USDT-SWAP, BTC-USD-SWAP, BTC-USDT, option summary, economic calendar, adl warning, liquidation order
        # self.okx_endpoint = "wss://ws.okx.com:8443/ws/v5/public"
        # # trades
        # self.okex_trades_params_usdt = {"event": "subscribe", 
        #                                        "arg": [{"channel": "trades", 
        #                                                 "instId": "BTC-USDT-SWAP"}], 
        #                                         "connId": str(generate_random_integer(10))}
        # self.okex_trades_params_usd = {"event": "subscribe", 
        #                                        "arg": [{"channel": "trades", 
        #                                                 "instId": "BTC-USD-SWAP"}], 
        #                                         "connId": str(generate_random_integer(10))}
        # self.okex_trades_params_usdt_spot = {"event": "subscribe", 
        #                                        "arg": [{"channel": "trades", 
        #                                                 "instId": "BTC-USDT"}], 
        #                                         "connId": str(generate_random_integer(10))}
        # self.okex_option_trades_params = {"event": "subscribe", 
        #                                        "arg": [{"channel": "option-trades",
        #                                         "instType": "OPTION",
        #                                         "instFamily": "BTC-USD"}], 
        #                                         "connId": str(generate_random_integer(10))}
        # # Books 400 depth levels will be pushed in the initial full snapshot. Incremental data will be pushed every 100 ms for the changes in the order book during that period of time.
        # self.okex_books_params_usdt = {"event": "subscribe", 
        #                                        "arg": [{"channel": "books", 
        #                                                 "instId": "BTC-USDT-SWAP"}], 
        #                                         "connId": str(generate_random_integer(10))}
        # self.okex_books_params_usd = {"event": "subscribe", 
        #                                        "arg": [{"channel": "books", 
        #                                                 "instId": "BTC-USD-SWAP"}], 
        #                                         "connId": str(generate_random_integer(10))}
        # self.okex_books_params_usdt_spot = {"event": "subscribe", 
        #                                        "arg": [{"channel": "books", 
        #                                                 "instId": "BTC-USDT"}], 
        #                                         "connId": str(generate_random_integer(10))}    
        # # Block trades  
        # self.okex_block_trades = {"event": "subscribe", 
        #                                        "arg": [{"channel": "public-struc-block-trades", 
        #                                                 }], 
        #                                         "connId": str(generate_random_integer(10))}   
        # # OI
        # self.okex_open_interest_params_usdt = {"event": "subscribe", 
        #                                        "arg": [{"channel": "open-interest", 
        #                                                 "instId": "BTC-USDT-SWAP"}], 
        #                                         "connId": str(generate_random_integer(10))}
        # self.okex_open_interest_params_usd = {"event": "subscribe", 
        #                                        "arg": [{"channel": "open-interest", 
        #                                                 "instId": "BTC-USD-SWAP"}], 
        #                                         "connId": str(generate_random_integer(10))}
        # # Funding
        # self.okex_funding_params_usdt = {"event": "subscribe", 
        #                                        "arg": [{"channel": "funding-rate", 
        #                                                 "instId": "BTC-USDT-SWAP"}], 
        #                                         "connId": str(generate_random_integer(10))}
        # self.okex_funding_params_usd = {"event": "subscribe", 
        #                                        "arg": [{"channel": "funding-rate", 
        #                                                 "instId": "BTC-USD-SWAP"}], 
        #                                         "connId": str(generate_random_integer(10))}
        # # Option Summary
        # self.okex_optionSummary = {"event": "subscribe", 
        #                                        "arg": [{"channel": "opt-summary", 
        #                                                 "instId": "BTC-USD"}], 
        #                                         "connId": str(generate_random_integer(10))}
        # # Liquidations
        # self.okex_liquidation_SWAP = {"op": "subscribe", "args": [{"channel": "liquidation-orders", "instType": "SWAP", }]}
        # self.okex_liquidation_FUTURES = {"op": "subscribe", "args": [{"channel": "liquidation-orders", "instType": "FUTURES"}]}
        # self.okex_liquidation_MARGIN = {"op": "subscribe", "args": [{"channel": "liquidation-orders", "instType": "MARGIN"}]}
        # self.okex_liquidation_OPTION = {"op": "subscribe", "args": [{"channel": "liquidation-orders", "instType": "OPTION"}]}
        # # Warning
        # self.okex_warning_SWAP = {"op": "subscribe", "args": [{"channel": "adl-warning", "instType": "SWAP",  "instFamily": "BTC-USDT"}]}
        # self.okex_warning_FUTURES = {"op": "subscribe", "args": [{"channel": "adl-warning", "instType": "FUTURES",  "instFamily": "BTC-USDT"}]}
        # self.okex_warning_OPTION = {"op": "subscribe", "args": [{"channel": "adl-warning", "instType": "OPTION",  "instFamily": "BTC-USDT"}]}    
        # self.okex_warning_SWAP_usd = {"op": "subscribe", "args": [{"channel": "adl-warning", "instType": "SWAP",  "instFamily": "BTC-USD"}]}
        # self.okex_warning_FUTURES_usd = {"op": "subscribe", "args": [{"channel": "adl-warning", "instType": "FUTURES",  "instFamily": "BTC-USD"}]}
        # self.okex_warning_OPTION_usd = {"op": "subscribe", "args": [{"channel": "adl-warning", "instType": "OPTION",  "instFamily": "BTC-USD"}]}
        # # Economic calendar Retrieve the most up-to-date economic calendar data. This endpoint is only applicable to VIP 1 and above users in the trading fee tier.
        # # https://www.okx.com/docs-v5/en/#public-data-rest-api-get-economic-calendar-data
        # # You may want to nake an API call rather than websocker
        # self.economic_calendar = {"op": "subscribe", "args": [{"channel": "economic-calendar"}]}

        # # Bybit BTCUSDT BTCUSD BTCUSDTspot
        # self.bybit_spot_endpoint = "wss://stream.bybit.com/v5/public/spot"
        # self.bybit_futures_endpoint = "wss://stream.bybit.com/v5/public/linear"
        # bybit_api = "https://api.bybit.com"
        # bybit_param = {"op": "auth", "args": ["api_key", 1662350400000, "signature"]}
        # bybit_topics = ["orderbook.{500}.{symbol}", "publicTrade.{symbol}", "tickers.{symbol}", "liquidation.{symbol}"]   # OI, funding, turnover deliveryFee Volume etc
        # bybit_api_topics = ["/v5/market/insurance", "/v5/market/account-ratio"]
        # In general, if there is no "ping-pong" and no stream data sent from server end, the connection will be cut off after 10 minutes. When you have a particular need, you can configure connection alive time by max_alive_time.
        # books
# async def authenticate(websocket, api_key, api_secret):
#     auth_payload = {
#         "op": "auth",
#         "args": [api_key, api_secret],
#     }
#     await websocket.send(json.dumps(auth_payload))
        
# async def subscribe_to_trades(websocket, symbol):
#     subscribe_payload = {
#         "op": "subscribe",
#         "args": [f"trade.{symbol}"],
#     }
#     await websocket.send(json.dumps(subscribe_payload))

# async def handle_message(message):
#     data = json.loads(message)
#     print("Received message:", data)
        
# async def subscribe_to_trades(websocket, symbol):
#     subscribe_payload = {
#         "op": "subscribe",
#         "args": [f"trade.{symbol}"],
#     }
#     await websocket.send(json.dumps(subscribe_payload))

# async def handle_message(message):
#     data = json.loads(message)
#     print("Received message:", data)
        # Bitget

        # Derebit

        # Coinbase

    
    # async def keep_alive_bitget(self, websocket, ping_interval=30):
    #     while True:
    #         try:
    #             # Send a ping message to the server.
    #             await asyncio.sleep(ping_interval)
    #             await websocket.send('ping')
    #         except websockets.exceptions.ConnectionClosed:
    #             print("Connection closed. Stopping keep-alive.")
    #             break
    

    # async def bitget_websockets(self, bitget_stream, data_auth, producer, topic):
    #     async for websocket in websockets.connect(bitget_stream, ping_interval=None, timeout=86400, ssl=ssl_context): #as websocket:
    #         await websocket.send(data_auth)
    #         keep_alive_task = asyncio.create_task(self.keep_alive_bitget(websocket, 30))
    #         try:
    #             async for message in websocket:
    #                 try:
    #                     message = await websocket.recv()
    #                     await producer.send_and_wait(topic=topic, value=str(message).encode())
    #                     print(f'Bitget_{topic} recieved')
    #                 except KafkaStorageError as e:
    #                     print(f"KafkaStorageError: {e}")
    #                     await asyncio.sleep(5)
    #                     continue
    #         except asyncio.exceptions.TimeoutError:
    #             print("WebSocket operation timed out")
    #             await asyncio.sleep(5)
    #             continue
    #         except websockets.exceptions.ConnectionClosed:
    #             print("connection  closed of bitget stream, reconnecting!!!")
    #             await asyncio.sleep(5)
    #             continue
        

    # async def binance_websockets(self, binance_stream, producer, topic):
    #     ticker = binance_stream.split('/')[-1].split('@')[0]
    #     async for websocket in websockets.connect(binance_stream, ping_interval=None, timeout=86400):
    #         keep_alive_task = asyncio.create_task(self.keep_alive_binance(websocket, 30))
    #         try:
    #             async for message in websocket:
    #                 try:
    #                     if topic == 'binance_spot':
    #                         await producer.send_and_wait(topic=topic, value=json.dumps({ticker: json.loads(message)}).encode())
    #                     else:
    #                         await producer.send_and_wait(topic=topic, value=str(message).encode())
    #                     #print(json.dumps({ticker: json.loads(message)}).encode())
    #                     print(f'Binance_{topic} recieved')
    #                 except KafkaStorageError as e:
    #                     print(f"KafkaStorageError: {e}")
    #         except asyncio.exceptions.TimeoutError:
    #             await asyncio.sleep(5)
    #             print("WebSocket operation timed out")
    #         except websockets.exceptions.ConnectionClosed:
    #             print("connection  closed of binance stream, reconnecting!!!")
    #             await asyncio.sleep(5)
    #             continue

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