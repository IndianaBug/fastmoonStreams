import asyncio
import websockets
import json

kind = ["option", "future"]

msg = {"jsonrpc": "2.0", "id": 9344, "method": "public/get_book_summary_by_currency", "params": { "currency": "BTC", "kind": "future_combo"}}

def deribit_api_call():
    async def call_api(msg):
        async with websockets.connect('wss://test.deribit.com/ws/api/v2') as websocket:
            await websocket.send(msg)
            response = await websocket.recv()
    async def main():
        await call_api(json.dumps(msg))
    asyncio.run(main())

deribit_api_call()