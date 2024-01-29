from datetime import datetime, timedelta
import time
import asyncio
import websockets
import json
import random
import ssl
import aiohttp
import json

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

def get_url_list():
    from urls import apizzz
    apizzz = [x for x in apizzz if x["obj"] != "depth"]
    return apizzz

links = get_url_list()

class combined_API():

    def __init__(self, links, producer):
        self.links = links
        self.producer = producer
        self.price = 0

    async def send_to_websocket(self, data):
        async with websockets.connect(self.websocket_uri) as websocket:
            await websocket.send(data) 
    
    async def websockets_fetcher(self, info):
        while True:
            async with websockets.connect(info["url"],  ssl=ssl_context) as websocket:
                await websocket.send(json.dumps(info["msg"]))
                
                data = await websocket.recv()
                
                try:
                    with open(f"data/{info["exchange"]}_{info["instrument"]}_{info["insType"]}_{info["obj"]}.json", 'r') as json_file:
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

                with open(f"data/{info["exchange"]}_{info["instrument"]}_{info["insType"]}_{info["obj"]}.json", 'w') as file:
                    json.dump(d, file, indent=2)         
                
                await asyncio.sleep(info["updateSpeed"])

    async def aiohttp_fetcher(self, info):
        while True:
            async with aiohttp.ClientSession() as session:
                async with session.get(info["url"]) as response:

                    data =  await response.text()
                    
                    try:
                        with open(f"data/{info["exchange"]}_{info["instrument"]}_{info["insType"]}_{info["obj"]}.json", 'r') as json_file:
                            d = json.load(json_file)
                    except (FileNotFoundError, json.JSONDecodeError):
                        d = []

                    new_data = {"timestamp" : time.time(),  "data" : json.loads(data)}
                    d.append(new_data)

                    with open(f"data/{info["exchange"]}_{info["instrument"]}_{info["insType"]}_{info["obj"]}.json", 'w') as file:
                        json.dump(d, file, indent=2)

                    await asyncio.sleep(info["updateSpeed"])

    async def main(self):
        tasks = []
        for info in self.links:
            if info["exchange"] != "deribit":
                tasks.append(asyncio.ensure_future(self.aiohttp_fetcher(info)))
            if info["exchange"] == "deribit":
                tasks.append(asyncio.ensure_future(self.websockets_fetcher(info)))
        await asyncio.gather(*tasks)
    
loader = combined_API(links, "producer")
asyncio.run(loader.main())


