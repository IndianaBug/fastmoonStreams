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
import aiohttp
import requests
from collections import deque

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


# Depth is not needed
linksAPI = [x for x in linksAPI if x["obj"] != "depth"]


class btcproducerTest():

    def __init__ (self, host, num_connections, linksAPi, linksWS):   
        self.num_connections = num_connections
        self.host = host
        self.linksAPI = linksAPi
        self.linksWS = linksWS
        self.btc_price = float(requests.get("https://api.binance.com/api/v3/trades?symbol=BTCUSDT").json()[0]["price"])
        self.rtt_averages = [deque(maxlen=10) for _ in range(num_connections)]

    def update_rtt_average(self, index, rtt):
        self.rtt_averages[index].append(rtt)

    def get_average_rtt(self, index):
        if self.rtt_averages[index]:
            return sum(self.rtt_averages[index]) / len(self.rtt_averages[index])
        else:
            return 0

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
                async for message in websocket:
                    try:
                        start_time = time.time()
                        if exchange == "binance" and obj == "trades" and insType == "spot" and instrument == "btcusdt":
                            response = await websocket.recv()
                            response = json.loads(response)
                            self.btc_price = float(response['p'])

                        # Some websockets doesn't return the whole book data after the first pull. You need to fetch it via api
                        if count == 1 and exchange in ["binance", "bybit", "coinbase"] and obj in ["depth"]:
                            data = books_snapshot(exchange, instrument, insType, snaplength=1000)
                            data = data["response"]
                            count += 1   
                        else:
                            data = await websocket.recv()
                        end_time = time.time()
                        rtt = end_time - start_time
                        self.update_rtt_average(index, rtt)
                        print(f"WebSocket {index} - RTT: {rtt:.4f} seconds (Avg: {self.get_average_rtt(index):.4f} seconds)")

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
        """
            Json rpc api need to be called via websockets
        """
        while True:
            async with websockets.connect(info["url"],  ssl=ssl_context) as websocket:
                await websocket.send(json.dumps(info["msg"]))
                data = await websocket.recv()  
                await asyncio.sleep(info["updateSpeed"])

    async def aiohttp_fetcher(self, info):
        while True:
            async with aiohttp.ClientSession() as session:
                async with session.get(info["url"]) as response:
                    data =  await response.text()
                    await asyncio.sleep(info["updateSpeed"])

    async def main(self):
        """
            Make sure to call btcusdt trades in the first place
        """
        #producer = AIOKafkaProducer(bootstrap_servers=self.host)
        #await producer.start()
        producer = ''
        topic = ''

        tasks = []
        tasks +=  [ 
            self.websocket_connection(
                connection_data=self.linksWS[x],
                producer=producer, 
                topic=topic) 
                for x in range(0, len(self.linksWS)-1) 
                ]

        for info in self.linksAPI:
            if info["exchange"] != "deribit":
                tasks.append(asyncio.ensure_future(self.aiohttp_fetcher(info)))
            if info["exchange"] == "deribit":
                tasks.append(asyncio.ensure_future(self.websockets_fetcher(info)))
        await asyncio.gather(*tasks) 



if __name__ == '__main__':
    client = btcproducerTest('localhost:9092', linksAPI, linksWS)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(client.main())
