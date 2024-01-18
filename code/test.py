import asyncio
import websockets
import json
import ssl

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False  
ssl_context.verify_mode = ssl.CERT_NONE  


o =  {"exchange":"deribit", "insType":"OPTIONS", "obj":"summary", "instrument":"BTC_integrated", 
                         "snapshotInterval":3,"url" : "wss://test.deribit.com/ws/api/v2",  "msg" : 
                                    {"jsonrpc": "2.0", "id": 15613, 
                                     "method": "public/get_book_summary_by_currency",
                                       "params": { "currency": "BTC", "kind": "option"}}}

url = o['url']
message = o['msg']


async def fetch_data_websockets():
    async with websockets.connect(url,  ssl=ssl_context) as websocket:
        await websocket.send(json.dumps(message))
        response = await websocket.recv()

        json.dump(json.loads(response), open("option_snap.json", "w"))

asyncio.run(fetch_data_websockets())