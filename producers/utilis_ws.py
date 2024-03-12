import asyncio
import websockets
import json

class pingspongs():

    def __init__ (self, intervals = {
        "binance" : 30,    # 1o minutes https://binance-docs.github.io/apidocs/spot/en/#rolling-window-price-change-statistics
        "bybit" : 20,        # 20 seconds https://bybit-exchange.github.io/docs/v5/ws/connect, https://bybit-exchange.github.io/docs/v5/ws/connect
        "okx" : 20,           # less than 30 seconds https://www.okx.com/docs-v5/en/#overview-websocket-overview
        "deribit" : 30,        # not less than 10 https://docs.deribit.com/#private-logout
        "kucoin" : 1,          # https://docs.deribit.com/#private-logout . The logic is differnt You have to answer to the websocket channel response /public/set_heartbeat
        "bitget" : 1,
        "bingx" : 1,
        "mexc" : 1, 
        "gateio" : 1,
        "htx" : 1,
        "coinbase" : None # Uses websocket heartbeat stream to keep the connection alive
    }) :
        """
            Intervals are in seconds
        """
        self.intervals = intervals
    

    async def binance_keep_alive(self, websocket :dict, data : dict=None):
        exchange = data.get("exchange", None)
        insType = data.get("exchange", None)
        instrument = data.get("instrument", None)
        while True:
            try:
                await websocket.pong()
                await asyncio.sleep(self.intervals.get("binance"))
            except websockets.exceptions.ConnectionClosed:
                if exchange != None:
                    print(f"Connection closed of {exchange}, {insType}, {instrument}. Stopping keep-alive.")
                else:
                    print(f"Connection closed of Binance stream. Stopping keep-alive.")

    async def bybit_keep_alive(self, websocket, conn_id=None, data=None):
        """
            The id of the websocket connection
            connection id is optional
        """
        exchange = data.get("exchange", None)
        insType = data.get("exchange", None)
        instrument = data.get("instrument", None)
        if conn_id != None:
            ping_dict = {"op": "ping"}
        else:
            ping_dict = {"req_id": conn_id, "op": "ping"}
        while True:
            try:
                await websocket.send(json.dumps(ping_dict))  
                await asyncio.sleep(self.intervals.get("bybit"))
            except websockets.exceptions.ConnectionClosed:
                if exchange != None:
                    print(f"Connection closed of {exchange}, {insType}, {instrument}. Stopping keep-alive.")
                else:
                    print(f"Connection closed of Bybit stream. Stopping keep-alive.")


    async def okx_keep_alive(self, websocket, data=None):
        exchange = data.get("exchange", None)
        insType = data.get("exchange", None)
        instrument = data.get("instrument", None)
        while True:
            try:
                await websocket.send('ping')
                await asyncio.sleep(self.intervals.get("okx"))
            except websockets.exceptions.ConnectionClosed:
                if exchange != None:
                    print(f"Connection closed of {exchange}, {insType}, {instrument}. Stopping keep-alive.")
                else:
                    print(f"Connection closed of OKX stream. Stopping keep-alive.")

    async def deribit_keep_alive(self, websocket, conn_id, data=None):
        """
            conn_id : The id that was sent in the request
        """
        exchange = data.get("exchange", None)
        insType = data.get("exchange", None)
        instrument = data.get("instrument", None)
        while True:
            try:
                await websocket.send(json.dumps({"jsonrpc":"2.0", "id": conn_id, "method": "/api/v2/public/test"}))
                await asyncio.sleep(self.intervals.get("deribit"))
            except websockets.exceptions.ConnectionClosed:
                if exchange != None:
                    print(f"Connection closed of {exchange}, {insType}, {instrument}. Stopping keep-alive.")
                else:
                    print(f"Connection closed of Deribit stream. Stopping keep-alive.")

    async def bitget_keep_alive(self, websocket, data=None):
        exchange = data.get("exchange", None)
        insType = data.get("exchange", None)
        instrument = data.get("instrument", None)
        while True:
            try:
                await websocket.send("ping")
                await asyncio.sleep(self.intervals.get("bitget"))
            except websockets.exceptions.ConnectionClosed:
                if exchange != None:
                    print(f"Connection closed of {exchange}, {insType}, {instrument}. Stopping keep-alive.")
                else:
                    print(f"Connection closed of Bitget stream. Stopping keep-alive.")

    async def bingx_keep_alive(self, websocket, data=None):
        exchange = data.get("exchange", None)
        insType = data.get("exchange", None)
        instrument = data.get("instrument", None)
        while True:
            try:
                await asyncio.sleep(self.intervals.get("bingx") )
                await websocket.send("Pong")  
            except websockets.exceptions.ConnectionClosed:
                if exchange != None:
                    print(f"Connection closed of {exchange}, {insType}, {instrument}. Stopping keep-alive.")
                else:
                    print(f"Connection closed of Bingx stream. Stopping keep-alive.")

    async def kucoin_keep_alive(self, websocket, conn_id, data=None):
        """
            conn_id : id of the deribit stream with which the websocket was initiated
        """
        exchange = data.get("exchange", None)
        insType = data.get("exchange", None)
        instrument = data.get("instrument", None)
        while True:
            try:
                await asyncio.sleep(self.intervals.get("kucoin"))
                await websocket.send(json.dumps({"type": "ping", "id":conn_id}))   
            except websockets.exceptions.ConnectionClosed:
                if exchange != None:
                    print(f"Connection closed of {exchange}, {insType}, {instrument}. Stopping keep-alive.")
                else:
                    print(f"Connection closed of Kucoin stream. Stopping keep-alive.")


    async def mexc_keep_alive(self, websocket, data=None):
        exchange = data.get("exchange", None)
        insType = data.get("exchange", None)
        instrument = data.get("instrument", None)
        while True:
            try:
                await websocket.send(json.dumps({"method": "PING"}))
                await asyncio.sleep(self.intervals.get("mexc"))
            except websockets.exceptions.ConnectionClosed:
                if exchange != None:
                    print(f"Connection closed of {exchange}, {insType}, {instrument}. Stopping keep-alive.")
                else:
                    print(f"Connection closed of MEXC stream. Stopping keep-alive.")

    async def gateio_keep_alive(self, websocket, data=None):
        exchange = data.get("exchange", None)
        insType = data.get("exchange", None)
        instrument = data.get("instrument", None)
        while True:
            try:
                await asyncio.sleep(self.intervals.get("gateio"))
                await websocket.send("ping")
            except websockets.exceptions.ConnectionClosed:
                if exchange != None:
                    print(f"Connection closed of {exchange}, {insType}, {instrument}. Stopping keep-alive.")
                else:
                    print(f"Connection closed of Gate.io stream. Stopping keep-alive.")


    async def htx_keep_alive(self, websocket, data=None):
        exchange = data.get("exchange", None)
        insType = data.get("exchange", None)
        instrument = data.get("instrument", None)
        while True:
            try:
                await asyncio.sleep(self.intervals.get("htx"))
                await websocket.send("ping")
            except websockets.exceptions.ConnectionClosed:
                if exchange != None:
                    print(f"Connection closed of {exchange}, {insType}, {instrument}. Stopping keep-alive.")
                else:
                    print(f"Connection closed of HTX stream. Stopping keep-alive.")
