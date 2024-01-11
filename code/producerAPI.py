from datetime import datetime, timedelta
import time
import asyncio
import websockets
import json
import random
import ssl
import aiohttp
from urls import APIs

def miliseconds_to_strftime(data) -> str:
    return datetime.utcfromtimestamp(int(data) / 1000.0).strftime('%Y-%m-%d %H:%M:%S UTC')

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


class combined_API():

    def __init__(self, APIs, producer):
        self.API = APIs
        self.producer = producer
    
    def get_stream_name(self, e):
        return e["exchange"]+ "_" +e["insType"]+ "_" +e["obj"]+ "_" +e["instrument"]

    async def send_to_websocket(self, data):
        async with websockets.connect(self.websocket_uri) as websocket:
            await websocket.send(data) 
    
    async def fetch_data_websockets(self, data_dict, period):
        while True:
            async with websockets.connect(data_dict["url"],  ssl=ssl_context) as websocket:
                await websocket.send(json.dumps(data_dict["msg"]))
                response = await websocket.recv()
                data = {self.get_stream_name(data_dict) : json.loads(response)}
                print(data.keys())
                await asyncio.sleep(period)

    async def fetch_data(self, data_dict, period):
        while True:
            async with aiohttp.ClientSession() as session:
                async with session.get(data_dict["url"]) as response:
                    r =  await response.text()
                    data = {self.get_stream_name(data_dict) :  json.loads(r)}
                    print(data.keys())
                    await asyncio.sleep(period)

    async def main(self):
        tasks_3_deribit = [asyncio.ensure_future(self.fetch_data_websockets(x,  x["snapshotInterval"])) for x in self.APIs if x["exchange"] == "deribit" and x["snapshotInterval"] == 3 and x["obj"] != "depth"]
        tasks_3 = [asyncio.ensure_future(self.fetch_data(x,  x["snapshotInterval"])) for x in self.APIs if x["exchange"] != "deribit" and x["snapshotInterval"] == 3 and x["obj"] != "depth"]
        task_300 = [asyncio.ensure_future(self.fetch_data(x,   x["snapshotInterval"])) for x in self.APIs if x["exchange"] != "deribit" and x["snapshotInterval"] == 300 and x["obj"] != "depth"]
        tasks = tasks_3_deribit + tasks_3 + task_300
        await asyncio.gather(*tasks)
    
loader = combined_API(APIs, "producer")
asyncio.run(loader.main())

