import websockets
import asyncio
import json
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaStorageError
import ssl
import random
from urls import WSs as wss 
from urls import generate_random_integer
import http.client
import json

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

class WebSocketClient():

    def __init__ (self, host, connection_data):
        
        self.host = host
        self.connection_data = connection_data


    def parse_params(self, arg, exchange):
        if exchange == "binance": 
            return json.dumps({"method": "SUBSCRIBE", "params": [arg], "id": generate_random_integer(10)})
        if exchange == "okx":
            return json.dumps({"op": "subscribe", "args": [arg]})
        if exchange == "bybit":
            return json.dumps({"op": "subscribe","args": [arg]})
        if exchange in ["coinbase", "blockchain"] :
            return json.dumps(arg)

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
                    # await websocket.send(json.dumps({"op": "ping"})) 
                if exchange == "blockchain":
                    await asyncio.sleep(ping_interval - 10)
                    await websocket.send('ping')
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

        count = 1

        async for websocket in websockets.connect(endpoint, ping_interval=None, timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
            exchange = name.split("_")[0]
            await websocket.send(self.parse_params(sname, exchange))
            keep_alive_task = asyncio.create_task(self.keep_alive(websocket, name.split("_")[0], 30))
            try:
                async for message in websocket:
                    try:

                        if count == 1:
                            conn = http.client.HTTPSConnection("api.binance.com")
                            conn.request("GET", "/api/v3/depth?symbol=BTCUSDT&limit=1000")
                            res = conn.getresponse()
                            data = res.read()
                            data = data.decode("utf-8")
                            count += 1
                            with open(f"bbooks.json", 'w') as json_file:
                                json.dump(json.loads(data), json_file, indent=4)

                        message = await websocket.recv()
                        #await producer.send_and_wait(topic=topic, value=str(message).encode())
                        print(name, type(message))

                        with open(f"trades_{count}.json", 'w') as json_file:
                            json.dump(json.loads(message), json_file, indent=4)

                        count += 1
                        
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
        tasks +=  [ self.websocket_connection(name=self.connection_data[x]["n"], 
                                             endpoint=self.connection_data[x]["e"], 
                                             sname=self.connection_data[x]["sn"], 
                                             producer=producer, 
                                             topic=topic) for x in [0]]
        await asyncio.gather(*tasks) 
        # try:
        #     await asyncio.gather(*tasks)
        # finally:
        #     await producer.stop()

if __name__ == '__main__':
    client = WebSocketClient('localhost:9092', wss)
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

