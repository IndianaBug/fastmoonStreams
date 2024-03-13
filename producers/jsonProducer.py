import json 
import gzip
import time
import websockets 
import asyncio
from aiokafka.errors import KafkaStorageError
import ssl
import codecs
import io
from producers.utilis_extended import AllStreamsByInstrumentS, get_dict_by_key_value, get_initial_books
from producers.utilis_core import bingx_AaWSnap_aiohttp
import aiohttp
import requests
import httpx


ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

class jsonBTCproducer():

    def __init__ (self, host, data):
        self.host = host
        self.api = [x for x in data if x["type"] == "api" and x["obj"] == "depth" and x["exchange"] == "bingx"] + [x for x in data if x["type"] == "api" and x["obj"] != "depth"]
        
        if "gateio_perpetual_btcusdt_depth" in [x["id"] for x in data]:
            self.api.append(get_dict_by_key_value([x for x in data if x["type"] == "api"], "id", "gateio_perpetual_btcusdt_depth"))

        self.ws = [x for x in data if x["type"] == "websocket"]
        self.btc_price = float(requests.get("https://api.binance.com/api/v3/trades?symbol=BTCUSDT").json()[0]["price"])
        self.initial_books = get_initial_books(self.ws) # Some websockets require to fetch books via API for the first time. Some apis can only be fetched via websocket method.# Fetch this now and delete later
        print(self.initial_books.keys())

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
                if exchange in ["coinbase", "htx"]:
                    await asyncio.sleep(ping_interval - 10)
                if exchange == "bingx":
                    await asyncio.sleep(ping_interval - 27)
                    await websocket.send("Pong")  
                if exchange in ["deribit"]:
                    await asyncio.sleep(ping_interval-25)
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
            

    async def websocket_connection(self, connection_data, producer, topic):

        count = 1
        id = connection_data["id"]
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
                    #async for message in websocket:
                    while True:
                        try:

                            if count == 1 and exchange in ["binance", "bybit", "coinbase", "kucoin", "mexc", "bitget", "gateio"]  and obj == "depth":
                                message = self.initial_books.pop(id, None)
                                message = message.get("response")
                                count += 1
                                if exchange == "deribit":
                                    message = json.loads(message)
                            else:  
                                message = await websocket.recv()
                                # Decompressing and dealing with pings
                                if exchange == "htx":
                                    try:
                                        message =  json.loads(gzip.decompress(message).decode('utf-8'))
                                    except:
                                        message = {}
                                elif exchange == "bingx":
                                    compressed_data = gzip.GzipFile(fileobj=io.BytesIO(message), mode='rb')
                                    decompressed_data = compressed_data.read()
                                    utf8_data = decompressed_data.decode('utf-8')
                                    try:
                                        message = json.loads(utf8_data)
                                    except:
                                        message = utf8_data
                                elif exchange not in ["htx", "bingx"]:
                                    try:
                                        message = json.loads(message)
                                    except:
                                        message = {}
                            
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
                                        if message.get("ping") and insType == "spot":
                                            await websocket.send(json.dumps({"pong" : message.get("ping"), "time" : message.get("time")}))
                                    if insType == "perpetual" and utf8_data == "Ping":
                                        await websocket.send("Pong")

                            # Writing down into a json file
                            try:
                                with open(f"data/{exchange}_{instrument}_{insType}_{obj}.json", 'r') as json_file:
                                    d = json.load(json_file)
                            except (FileNotFoundError, json.JSONDecodeError):
                                d = []

                            new_data = { 
                                    "exchange" : exchange,
                                    "instrument" : instrument,
                                    "insType" : insType,
                                    "obj" : obj,
                                    "btc_price" : self.btc_price,
                                    "timestamp" : time.time(),  
                                    "data" : message 
                                   }
                            d.append(new_data)

                            with open(f"data/{exchange}_{instrument}_{insType}_{obj}.json", 'w') as file:
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
                print(f"connection  closed of {exchange}, {instrument}, {insType}, {obj}. Reconnecting!")
                if exchange == "bingx":
                    await asyncio.sleep(1)
                else:
                    await asyncio.sleep(5)
                continue

    async def websockets_fetcher(self, info):
        """
            Json rpc api need to be called via websockets
        """

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
                        "btc_price" : self.btc_price,
                        "timestamp" : time.time(),  
                        "data" : json.loads(data) 
                        }

                d.append(new_data)

                with open(f'data/{info["exchange"]}_{info["instrument"]}_{info["insType"]}_{info["obj"]}.json', 'w') as file:
                    json.dump(d, file, indent=2)         
                
                await asyncio.sleep(info["updateSpeed"])

    async def fetch_data_gate(self, info):
        url = info["url"]
        headers = info["headers"]
        params = info["params"]

        while True:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, params=params, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    print(f"Received data: {data}")

            except httpx.HTTPError as e:
                print(f"HTTP error: {e}")

            # Optionally, introduce a delay before the next fetch
            await asyncio.sleep(5)  # 5 seconds delay (adjust as needed)

    async def aiohttp_fetcher(self, info):
        exchange = info["exchange"]
        instrument = info["instrument"]
        insType = info["insType"]
        obj = info["obj"]
        id = info["id"]
        if exchange == "bingx":
            while True:
                
                data = await bingx_AaWSnap_aiohttp(info["url"], info["path"], info["params"],"depth", 3)
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
                        "btc_price" : self.btc_price,
                        "timestamp" : time.time(),  
                        "data" : data
                        }
                d.append(new_data)
                with open(f'data/{info["exchange"]}_{info["instrument"]}_{info["insType"]}_{info["obj"]}.json', 'w') as file:
                    json.dump(d, file, indent=2)
                await asyncio.sleep(info["updateSpeed"])



        if exchange == "gateio" and insType == "perpetual":
            while True:
                async with aiohttp.ClientSession() as session:

                    headers = info["headers"]
                    headers["from"] = f"{int(time.time()) - 10}"
                    headers["to"] = f"{int(time.time())}" 

                    async with session.get(info["url"], headers=info["headers"], params=info["params"]) as response:
                        
                        data =  await response.text()

                        # Check for an error in the received data and raise an exception if needed
                        if "error" in data:
                            raise aiohttp.ClientResponseError(status=400, message="Error in websocket data")

                        
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
                                "btc_price" : self.btc_price,
                                "timestamp" : time.time(),  
                                "data" : json.loads(data) 
                                }
                        d.append(new_data)
                        with open(f'data/{info["exchange"]}_{info["instrument"]}_{info["insType"]}_{info["obj"]}.json', 'w') as file:
                            json.dump(d, file, indent=2)
                        await asyncio.sleep(info["updateSpeed"])
        else:
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
                                "btc_price" : self.btc_price,
                                "timestamp" : time.time(),  
                                "data" : json.loads(data) 
                                }
                        d.append(new_data)
                        with open(f'data/{info["exchange"]}_{info["instrument"]}_{info["insType"]}_{info["obj"]}.json', 'w') as file:
                            json.dump(d, file, indent=2)
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

        for info in self.ws:
            tasks.append(asyncio.ensure_future(self.websocket_connection(info, producer, topic)))

        for info in self.api:
            if info["exchange"] != "deribit":
                tasks.append(asyncio.ensure_future(self.aiohttp_fetcher(info)))
            if info["exchange"] == "deribit":
                tasks.append(asyncio.ensure_future(self.websockets_fetcher(info)))

        await asyncio.gather(*tasks) 

streams = [
    ["deribit", "perpetual", "btcusd"],
    ["gateio", "perpetual", "btcusdt"],
    ["gateio", "spot", "btcusdt"],
    ["htx", "perpetual", "btcusdt"],
    ["htx", "spot", "btcusdt"],
    ["bingx", "perpetual", "btcusdt"],
    ["bingx", "spot", "btcusdt"],
    ["bitget", "perpetual", "btcusdt"],
    ["bitget", "spot", "btcusdt"],
    ["mexc", "spot", "btcusdt"],
    ["mexc", "perpetual", "btcusdt"],
    ["kucoin", "perpetual", "btcusdt"],
    ["kucoin", "spot", "btcusdt"],
    ["bybit", "spot", "btcusdc"],
    ["bybit", "perpetual", "btcusd"],

]

data = AllStreamsByInstrumentS(streams)
from urls import AaWS
from producers.utilis_core import get_dict_by_key_value
data = [get_dict_by_key_value([x for x in AaWS if x["type"] == "websocket"], "id", "mexc_perpetual_btcusdt_fundingOI")]

if __name__ == '__main__':
    client = jsonBTCproducer('localhost:9092', data)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(client.main())