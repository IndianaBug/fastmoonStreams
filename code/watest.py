# kucoin get public token  POST /api/v1/bullet-public
# https://www.kucoin.com/docs/websocket/basic-info/ping
# Create a keep alive to send ping message

import json 
import gzip
import requests
import time
import hashlib
import hmac
import base64
import websockets 
import asyncio
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaStorageError
import ssl
import codecs
import io
from utilis import get_dict_by_key_value
from urls import  APIS, WEBSOCKETS

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

data = get_dict_by_key_value(WEBSOCKETS, "id", "bingx_perpetual_btcusdt_trades")

class btcproducer():

    def __init__ (self, host, data):
        self.host = host
        self.data = data

    async def keep_alive(self, websocket, exchange, id=None, ping_interval=30):
        while True:
            try:
                if exchange == "binance":
                    await websocket.pong()
                    await asyncio.sleep(ping_interval)
                if exchange in ["mexc"]:
                    await websocket.send(json.dumps({"method": "PING"}))
                    await asyncio.sleep(ping_interval)
                if exchange in ["bitget"]:
                    await websocket.send("ping")
                    await asyncio.sleep(ping_interval)
                if exchange == "okx":
                    await asyncio.sleep(ping_interval - 10)
                    await websocket.send('ping')
                if exchange == "bybit":
                    await asyncio.sleep(ping_interval - 10)
                    await websocket.send(json.dumps({"op": "ping"}))  
                if exchange in ["coinbase", "htx", "bingx"]:
                    await asyncio.sleep(ping_interval - 10)
                if exchange in ["deribit"]:
                    await asyncio.sleep(ping_interval)
                    await websocket.send(json.dumps({"jsonrpc":"2.0", "id": id, "method": "/api/v2/public/test"}))
                if exchange == "kucoin":
                    await asyncio.sleep(ping_interval - 10)
                    await websocket.send(json.dumps({"type": "ping", "id":id}))   # generate random id
                if exchange == "gateio":
                    await asyncio.sleep(ping_interval - 25)
                    await websocket.send("ping")
            except websockets.exceptions.ConnectionClosed:
                print(f"Connection closed. Stopping keep-alive of {exchange}.")
                break
    
    async def receive_messages(self, websocket):
        try:
            async for message in websocket:
                print(message)
        except asyncio.exceptions.TimeoutError:
            print("WebSocket operation timed out")

    async def websocket_connection_v1(self, connection_data):

        count = 1
        exchange = connection_data["exchange"]
        instrument = connection_data["instrument"]
        insType = connection_data["insType"]
        obj = connection_data["obj"]
        endpoint = connection_data["url"]
        msg = connection_data["msg"]
        
        if connection_data["id"] in ["deribit_hearbeat"]:
            id = connection_data.get("msg").get("id")


        async for websocket in websockets.connect(endpoint, ping_interval=30, timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
                    
            await websocket.send(json.dumps(msg))

            if connection_data["id"] in ["deribit_hearbeat"]:
                keep_alive_task = asyncio.create_task(self.keep_alive(websocket, exchange, id, 30))
            else:
                keep_alive_task = asyncio.create_task(self.keep_alive(websocket, exchange, 30))
         
            try:
                if obj != "heartbeat":
                    async for message in websocket:
                        try:
                            
                            message = await websocket.recv()
                            
                            if exchange in ["htx"]:
                                message =  json.loads(gzip.decompress(message).decode('utf-8'))
                            print(message)
                            if exchange == "bingx":
                                compressed_data = gzip.GzipFile(fileobj=io.BytesIO(message), mode='rb')
                                decompressed_data = compressed_data.read()
                                utf8_data = decompressed_data.decode('utf-8')
                                try:
                                    message = json.loads(utf8_data)
                                except:
                                    message = json.loads(gzip.decompress(utf8_data).decode('utf-8'))
                            else:
                                message = json.loads(message)
                            
                            print(message)
                            if exchange == "deribit":
                                try:
                                    if message.get("error", None).get("message") == 'Method not found':
                                        await websocket.send(json.dumps({"jsonrpc":"2.0", "id":  message.get("id", None), "method": "/api/v2/public/test"}))
                                except:
                                    pass
                            if exchange == "htx":
                                if message.get("ping"):
                                    await websocket.send(json.dumps({"pong" : message.get("ping")}))
                            if exchange == "bingx":
                                if isinstance(message, dict):
                                    if message.get("ping"):
                                        if insType == "spot": 
                                            await websocket.send(json.dumps({"pong" : message.get("ping"), "time" : message.get("time")}))
                                        else:
                                            await websocket.send("pong")
                            
                        except KafkaStorageError as e:
                            print(f"KafkaStorageError: {e}")
                            await asyncio.sleep(5)
                            continue
            except asyncio.exceptions.TimeoutError:
                print("WebSocket operation timed out")
                await asyncio.sleep(5)
                continue
            except websockets.exceptions.ConnectionClosed:
                print(f"connection  closed of {exchange}, {instrument}, {insType}, {obj}. Reconnecting!")
                await asyncio.sleep(5)
                continue


    async def main(self):
        """
            Make sure to call btcusdt trades in the first place
        """
        #producer = AIOKafkaProducer(bootstrap_servers=self.host)
        #await producer.start()
        producer = ''
        topic = ''

        tasks = []
        tasks +=  [self.websocket_connection_v1(self.data)]

        await asyncio.gather(*tasks) 


if __name__ == '__main__':
    client = btcproducer('localhost:9092', data)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(client.main())

