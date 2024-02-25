import asyncio
import websockets
import json
import ssl
from utilis import get_dict_by_key_value
from urls import  APIS, WEBSOCKETS

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
# To subscribe to this channel:
msg = \
    {"jsonrpc": "2.0",
     "method": "public/subscribe",
     "id": 42,
     "params": {
        "channels": ["book.BTC-PERPETUAL.100ms"]}
    }

async def call_api(msg):
   async with websockets.connect('wss://test.deribit.com/ws/api/v2', ssl=ssl_context) as websocket:
       await websocket.send(msg)
       while websocket.open:
           response = await websocket.recv()
           # do something with the notifications...
           print(response)

asyncio.get_event_loop().run_until_complete(call_api(json.dumps(msg)))
