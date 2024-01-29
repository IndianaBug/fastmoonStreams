import websockets
import asyncio
import json
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaStorageError
import json
import ssl
import random
from urls import websocketzzz as linksWS
from urls import apizzz as linksAPI
from utilis import books_snapshot
import time
import datetime




ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def miliseconds_to_strftime(data) -> str:
    return datetime.datetime.utcfromtimestamp(int(data) / 1000.0).strftime('%Y-%m-%d %H:%M:%S UTC')

def generate_random_integer(n):
    if n <= 0:
        raise ValueError("Length should be a positive integer")
    lower_bound = 10 ** (n - 1)
    upper_bound = (10 ** n) - 1
    random_integer = random.randint(lower_bound, upper_bound)
    return random_integer

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False  
ssl_context.verify_mode = ssl.CERT_NONE  

def get_url_list():
    linksAPI = [x for x in linksAPI if x["obj"] != "depth"]
    return linksAPI

linksAPI = get_url_list()



class btcproducer():
    """
        Make sure to call the websocket BTCUSDT trade the first
    """

    def __init__ (self, host, linksAPi, linksWS):
        self.host = host
        self.linksAPI = linksAPI
        self.linksWS = linksWS

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
                    await asyncio.sleep(10 - 10)
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed. Stopping keep-alive.")
                break
    

    async def websocket_connection(self, connection_data, producer, topic):
        """
            type: usdt marginated, futures, coin marginated, perpetual, spot ....
            authentication: websocket request params
            producer: websockets producers name
            topic: aiokafka topic
        """

        count = 1
        exchange = connection_data["exchange"]
        instrument = connection_data["instrument"]
        insType = connection_data["insType"]
        obj = connection_data["obj"]
        endpoint = connection_data["url"]
        msg = connection_data["msg"]

        async for websocket in websockets.connect(endpoint, ping_interval=None, timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
            
            await websocket.send(json.dumps(msg))
            
            keep_alive_task = asyncio.create_task(self.keep_alive(websocket, exchange, 30))

            
            try:
                if obj != "heartbeat":
                    async for message in websocket:
                        try:

                            if exchange == "binance" and obj == "trades" and insType == "spot" and instrument == "btcusdt":
                                response = json.loads(response)
                                self.price = response['p']

                            # Some websockets doesn't return the whole book data after the first pull. You need to fetch it via api
                            if count == 1 and exchange in ["binance", "bybit"] and obj in ["depth"]:
                                data = books_snapshot(exchange, instrument, insType, snaplength=1000)
                                data = data["response"]
                                count += 1   
                            else:
                                data = await websocket.recv()
                                try:
                                    data = json.loads(data)
                                except:
                                    data = {}
                            
                            try:
                                with open(f"data/d/{exchange}_{instrument}_{insType}_{obj}.json", 'r') as json_file:
                                    d = json.load(json_file)
                            except (FileNotFoundError, json.JSONDecodeError):
                                d = []

                            new_data = { 
                                    "exchange" : exchange,
                                    "instrument" : instrument,
                                    "insType" : insType,
                                    "obj" : obj,
                                    "btc_price" : self.price,
                                    "timestamp" : time.time(),  
                                    "data" : data 
                                   }
                            d.append(new_data)

                            with open(f"data/d/{exchange}_{instrument}_{insType}_{obj}.json", 'w') as file:
                                json.dump(d, file, indent=2)

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



    async def websockets_fetcher(self, info):

        exchange = info["exchange"]
        instrument = info["instrument"]
        insType = info["insType"]
        obj = info["obj"]
        
        while True:
            async with websockets.connect(info["url"],  ssl=ssl_context) as websocket:
                await websocket.send(json.dumps(info["msg"]))
                
                data = await websocket.recv()
                
                try:
                    with open(f'data/{info["exchange"]}_{info["instrument"]}_{info["insType"]}_{info["obj"]}.json', 'r') as json_file:
                        d = json.load(json_file)
                except (FileNotFoundError, json.JSONDecodeError):
                    d = []

                new_data = { 
                        "exchange" : exchange,
                        "instrument" : instrument,
                        "insType" : insType,
                        "obj" : obj,
                        "btc_price" : self.price,
                        "timestamp" : time.time(),  
                        "data" : json.loads(data) 
                        }

                d.append(new_data)

                with open(f'data/{info["exchange"]}_{info["instrument"]}_{info["insType"]}_{info["obj"]}.json', 'w') as file:
                    json.dump(d, file, indent=2)         
                
                await asyncio.sleep(info["updateSpeed"])


    async def aiohttp_fetcher(self, info):

        exchange = info["exchange"]
        instrument = info["instrument"]
        insType = info["insType"]
        obj = info["obj"]

        while True:
            async with aiohttp.ClientSession() as session:
                async with session.get(info["url"]) as response:

                    data =  await response.text()
                    
                    try:
                        with open(f'data/{info["exchange"]}_{info["instrument"]}_{info["insType"]}_{info["obj"]}.json', 'r') as json_file:
                            d = json.load(json_file)
                    except (FileNotFoundError, json.JSONDecodeError):
                        d = []

                    new_data = { 
                            "exchange" : exchange,
                            "instrument" : instrument,
                            "insType" : insType,
                            "obj" : obj,
                            "btc_price" : self.price,
                            "timestamp" : time.time(),  
                            "data" : json.loads(data) 
                            }
                    
                    d.append(new_data)

                    with open(f'data/{info["exchange"]}_{info["instrument"]}_{info["insType"]}_{info["obj"]}.json', 'w') as file:
                        json.dump(d, file, indent=2)

                    await asyncio.sleep(info["updateSpeed"])

    async def main(self):
        """
            Gather all websockets
        """
        #producer = AIOKafkaProducer(bootstrap_servers=self.host)
        #await producer.start()
        producer = ''
        topic = ''

        await self.websocket_connection(
                                    connection_data=self.linksWS[0],
                                    producer=producer, 
                                    topic=topic)


        tasks = []
        tasks +=  [ 
            self.websocket_connection(
                connection_data=self.linksWS[x],
                producer=producer, 
                topic=topic) 
                for x in range(1, len(self.linksWS)-1) 
                ]

        for info in self.linksAPI:
            if info["exchange"] != "deribit":
                tasks.append(asyncio.ensure_future(self.aiohttp_fetcher(info)))
            if info["exchange"] == "deribit":
                tasks.append(asyncio.ensure_future(self.websockets_fetcher(info)))

        await asyncio.gather(*tasks) 
        # try:
        #     await asyncio.gather(*tasks)
        # finally:
        #     await producer.stop()


if __name__ == '__main__':
    client = btcproducer('localhost:9092', linksAPI, linksWS)
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
