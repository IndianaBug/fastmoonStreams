import asyncio
import websockets
import json
import time
from urllib.parse import urlencode
import requests
import websockets
import ssl
from hashlib import sha256
import json
import jwt
from cryptography.hazmat.primitives import serialization
import secrets
import os
import sys
import hashlib
import hmac
import base64
import random
import string
import aiohttp
from utilis import generate_random_id



class keepalive():
    """
        Handles pings pongs of websockets connections
        Intervals are in seconds
    """
    prefered_intervals = {
        "binance" : 30,   
        "bybit" : 20,        # 20 seconds https://bybit-exchange.github.io/docs/v5/ws/connect, https://bybit-exchange.github.io/docs/v5/ws/connect
        "okx" : 20,           # less than 30 seconds https://www.okx.com/docs-v5/en/#overview-websocket-overview
        "deribit" : None,
        "kucoin" : 1,          # https://docs.deribit.com/#private-logout . The logic is differnt You have to answer to the websocket channel response /public/set_heartbeat
        "bitget" : 1,
        "bingx" : 1,
        "mexc" : 1, 
        "gateio" : 1,
        "htx" : 1,
        "coinbase" : None # Uses websocket heartbeat stream to keep the connection alive
    }
    
    @classmethod
    async def binance_keep_alive(cls, websocket, connectionData:dict=None, ping_interval:int=30):
        """
            https://binance-docs.github.io/apidocs/spot/en/#websocket-market-streams
            Websocket server will send a ping frame every 3 minutes.
            If the websocket server does not receive a pong frame back from the connection within a 10 minute period, the connection will be disconnected.
            When you receive a ping, you must send a pong with a copy of ping's payload as soon as possible.
            Unsolicited pong frames are allowed, but will not prevent disconnection. It is recommended that the payload for these pong frames are empty.
        """
        exchange = connectionData.get("exchange", None)
        id_ws = connectionData.get("id_ws", None)
        while True:
            await asyncio.sleep(ping_interval)
            try:
                print("Sending unsolicited pong (optional)")
                await websocket.pong(b"")  # Empty payload for unsolicited pong
            except websockets.ConnectionClosed:
                print(f"Connection closed of {id_ws}. Stopping keep-alive.")


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


class wsMongoTest(keepalive):
    
    @classmethod
    def process_data_for_mongo(cls):
        pass
    @classmethod
    def insert_into_mongo(cls):
        pass
    @classmethod
    def calculate_latency(cls):
        # Get server timestamp
        # Get current timestamp
        
        pass    
    
    @classmethod
    async def binance(cls, connectionData, producer=None, topic=None):
        """
            producer and topic are reserved for kafka integration
        """
        async for websocket in websockets.connect(endpoint, ping_interval=30, timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
            await websocket.send(json.dumps(connection_data.get("msg_method")()))
            keep_alive_task = asyncio.create_task(cls.binance_keep_alive(websocket, connectionData))
            while True:
                try:
                    if message == websockets.PING:
                        print(f"Received ping from {connectionData.get("id_ws")}. Sending pong...")
                        await websocket.pong(message)
                    # 
                except websockets.ConnectionClosed:
                    print(f"Connection closed of {id_ws}")
                    break
