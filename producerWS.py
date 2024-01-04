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
        Derebit: https://docs.deribit.com/
    """


    def __init__ (self, host, **kwards):
        
        self.host = host
        self.connection_data = [
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
             { "n": "binance_perpetual_forceOrder_USD", "e": "wss://dstream.binance.com/ws", "sn": "btcusd_perp@forceOrder"}, # ok ? 
             # Okx
             { "n": "binance_perpetual_depth_USD", "e": "wss://ws.okx.com:8443/ws/v5/public", "sn": "btcusd_perp@forceOrder"},   
             { "n" : "okx_",  # 11
               "e":"wss://ws.okx.com:8443/ws/v5/public", 
               "args" : [
                 {"channel": "trades", "instId": "BTC-USDT-SWAP"}, # ok
                 {"channel": "trades", "instId": "BTC-USD-SWAP"},  # ok
                 {"channel": "trades", "instId": "BTC-USDT"},      # ok
                 {"channel": "option-trades", "instType": "OPTION","instFamily": "BTC-USD"}, # ok
                 {"channel": "books", "instId": "BTC-USDT-SWAP"}, # ok # Books 400 depth levels will be pushed in the initial full snapshot. Incremental data will be pushed every 100 ms for the changes in the order book during that period of time.
                 {"channel": "books", "instId": "BTC-USD-SWAP"},  # ok
                 {"channel": "books", "instId": "BTC-USDT"},      # ok
                 {"channel": "public-struc-block-trades"}, # block trades https://www.okx.com/docs-v5/en/#block-trading-websocket-public-channel-public-structure-block-trades-channel
                 {"channel": "open-interest", "instId": "BTC-USDT-SWAP"}, # ok
                 {"channel": "open-interest", "instId": "BTC-USD-SWAP"},  # ok
                 {"channel": "funding-rate", "instId": "BTC-USDT-SWAP"},  # ok
                 {"channel": "funding-rate", "instId": "BTC-USD-SWAP"},   # ok
                 {"channel": "opt-summary", "instFamily": "BTC-USD"},     # ok
                 {"channel": "liquidation-orders", "instType": "SWAP"},   # ok
                 {"channel": "liquidation-orders", "instType": "FUTURES"},# ok
                 {"channel": "liquidation-orders", "instType": "MARGIN"}, # ok
                 {"channel": "liquidation-orders", "instType": "OPTION"}, # ok
                 {"channel": "adl-warning", "instType": "SWAP",  "instFamily": "BTC-USDT"},
                 {"channel": "adl-warning", "instType": "FUTURES",  "instFamily": "BTC-USDT"},
                 {"channel": "adl-warning", "instType": "OPTION",  "instFamily": "BTC-USDT"},
                 {"channel": "adl-warning", "instType": "SWAP",  "instFamily": "BTC-USD"},
                 {"channel": "adl-warning", "instType": "FUTURES",  "instFamily": "BTC-USD"},
                 {"channel": "adl-warning", "instType": "OPTION",  "instFamily": "BTC-USD"}
                                                        ]},
             # bybit
             { "n": "bybit_spot_depth_USDT", "e": "wss://stream.bybit.com/v5/public/spot", "sn": "orderbook.200.BTCUSDT"}, # ok
             { "n": "bybit_spot_trades_USDT", "e": "wss://stream.bybit.com/v5/public/spot", "sn": "publicTrade.BTCUSDT"},  # ok
             { "n": "bybit_perpetual_depth_USDT", "e": "wss://stream.bybit.com/v5/public/linear", "sn": "orderbook.200.BTCUSDT"},  # ok
             { "n": "bybit_perpetual_trades_USDT", "e": "wss://stream.bybit.com/v5/public/linear", "sn": "publicTrade.BTCUSDT"},   # ok
             { "n": "bybit_perpetual_forceOrder_USDT", "e": "wss://stream.bybit.com/v5/public/linear", "sn": "liquidation.BTCUSDT"},  # ok
             { "n": "bybit_perpetual_tickers_USDT", "e": "wss://stream.bybit.com/v5/public/linear", "sn": "tickers.BTCUSDT"},  # ok # OI funding turnover etc
             # coinbase
             {"n":"coinbase_spot_btcusd", "e":"wss://ws-feed.exchange.coinbase.com", "sn": {"type": "subscribe", "product_ids": ["BTC-USD"], "channels": ["level2", "ticker"]}},
             # deribit
             {"n":"deribit_", "e": "wss://streams.deribit.com/ws/api/v2", "sn": "deribit_price_index.btc_usd"}

                                                        ] 
        # Economic calendar Retrieve the most up-to-date economic calendar data. This endpoint is only applicable to VIP 1 and above users in the trading fee tier.
        # https://www.okx.com/docs-v5/en/#public-data-rest-api-get-economic-calendar-data
        # You may want to nake an API call rather than websocker


    def parse_params(self, arg, exchange):
        if exchange == "binance": 
            return json.dumps({"method": "SUBSCRIBE", "params": [arg], "id": generate_random_integer(10)})
        if exchange == "okx":
            return json.dumps({"op": "subscribe", "args": [arg]})
        if exchange == "bybit":
            return json.dumps({"op": "subscribe","args": [arg]})
        if exchange == "coinbase":
            return json.dumps(arg)
        if exchange == "deribit":
            return json.dumps({"jsonrpc" : "2.0", "id" : generate_random_integer(10), "method" : "public/subscribe", "params" : { "channels" : [arg]}})


    async def keep_alive(self, websocket, exchange, ping_interval=30):
        while True:
            try:
                if exchange == "binance":
                    await websocket.pong()
                    await asyncio.sleep(ping_interval)
                if exchange == "okx":
                    await asyncio.sleep(ping_interval - 10)
                    await websocket.send('ping')
                if exchange == "bybit":
                    await asyncio.sleep(ping_interval - 10)
                    await websocket.send(json.dumps({"op": "ping"}))  
                if exchange == "coinbase":
                    await asyncio.sleep(ping_interval - 10)
                    await websocket.send(json.dumps({"op": "ping"}))
                if exchange == "deribit":
                    await asyncio.sleep(ping_interval - 10)
                    await websocket.send(json.dumps({"op": "ping"}))                   
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed. Stopping keep-alive.")
                break

    async def websocket_connection(self, name, endpoint, sname, producer, topic):
        """
            type: usdt marginated, futures, coin marginated, perpetual, spot ....
            authentication: websocket request params
            producer: websockets producers name
            topic: aiokafka topic
        """
        async for websocket in websockets.connect(endpoint, ping_interval=None, timeout=86400, ssl=ssl_context):
            exchange = name.split("_")[0]
            await websocket.send(self.parse_params(sname, exchange))
            keep_alive_task = asyncio.create_task(self.keep_alive(websocket, name.split("_")[0], 30))
            try:
                async for message in websocket:
                    try:
                        message = await websocket.recv()
                        #await producer.send_and_wait(topic=topic, value=str(message).encode())
                        print(name, message)
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
        tasks +=  [self.websocket_connection(name=self.connection_data[-1]["n"], 
                                             endpoint=self.connection_data[-1]["e"], 
                                             sname=self.connection_data[-1]["sn"], 
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

