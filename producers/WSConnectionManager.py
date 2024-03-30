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
import aiocouchdb
import zlib

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


class keepalive():
    """
        Handles pings pongs of websockets connections
        Intervals are in seconds
    """
    prefered_intervals = {
        "binance" : 30,   
        "bybit" : 20,       
        "okx" : 15,         
        "deribit" : None,
        "kucoin" : 1,       
        "bitget" : 30,
        "bingx" : 1,
        "mexc" : 1, 
        "gateio" : 1,
        "htx" : 1,
        "coinbase" : None # Uses websocket heartbeat stream to keep the connection alive
    }
    
    @classmethod
    async def binance_keep_alive(cls, websocket, connection_data:dict=None, ping_interval:int=30):
        """
            https://binance-docs.github.io/apidocs/spot/en/#websocket-market-streams
            Websocket server will send a ping frame every 3 minutes.
            If the websocket server does not receive a pong frame back from the connection within a 10 minute period, the connection will be disconnected.
            When you receive a ping, you must send a pong with a copy of ping's payload as soon as possible.
            Unsolicited pong frames are allowed, but will not prevent disconnection. It is recommended that the payload for these pong frames are empty.
        """
        id_ws = connection_data.get("id_ws", None)
        while True:
            try:
                print("Sending unsolicited pong")
                await websocket.pong(b"")  # Empty payload for unsolicited pong
            except websockets.ConnectionClosed:
                print(f"Connection closed of {id_ws}. Stopping keep-alive.")
            await asyncio.sleep(ping_interval)

    async def bybit_keep_alive(self, websocket, connection_data=None, ping_interval:int=20):
        """
            https://bybit-exchange.github.io/docs/v5/ws/connect
            In general, if there is no "ping-pong" and no stream data sent from server end, the connection will be 
            cut off after 10 minutes. When you have a particular need, you can configure connection alive time by max_active_time.
            Since ticker scans every 30s, so it is not fully exact, i.e., if you configure 45s, and your last update or ping-pong is 
            occurred on 2023-08-15 17:27:23, your disconnection time maybe happened on 2023-08-15 17:28:15
            To avoid network or program issues, we recommend that you send the ping heartbeat packet every 20 seconds to maintain the WebSocket connection.

            How to seng: // req_id is a customised ID, which is optional ws.send(JSON.stringify({"req_id": "100001", "op": "ping"})
        """
        id_ws = connection_data.get("id_ws", None)
        while True:
            try:
                print("Sending pong (optional)")
                await websocket.ping(json.dumps({"req_id": connection_data.get('req_id'), "op": "ping"})) 
            except websockets.ConnectionClosed:
                print(f"Connection closed of {id_ws}. Stopping keep-alive.")
            await asyncio.sleep(ping_interval)

    async def okx_keep_alive(self, websocket, connection_data=None, ping_interval:int=15):
        """
            https://www.okx.com/docs-v5/en/#overview-websocket-overview

        If there’s a network problem, the system will automatically disable the connection.
        The connection will break automatically if the subscription is not established or data has not been pushed for more than 30 seconds.
        To keep the connection stable:
        1. Set a timer of N seconds whenever a response message is received, where N is less than 30.
        2. If the timer is triggered, which means that no new message is received within N seconds, send the String 'ping'.
        3. Expect a 'pong' as a response. If the response message is not received within N seconds, please raise an error or reconnect. 
        """
        id_ws = connection_data.get("id_ws", None)
        while True:
            try:
                print("Sending pong (optional)")
                await websocket.ping("ping") 
            except websockets.ConnectionClosed:
                print(f"Connection closed of {id_ws}. Stopping keep-alive.")
            await asyncio.sleep(ping_interval)

    async def deribit_keep_alive(self, websocket, conn_id, data=None):
        """
            https://docs.deribit.com/#public-set_heartbeat

            Deribit's heartbeat mechanism is different from a traditional "keep-alive" approach. It uses two types of messages:

                Heartbeats: Sent by the server at the specified interval (30 seconds in this example).
                Test Requests: Sent by the server periodically to verify that the client is responsive.

            Responding to both types of messages is crucial to maintain a healthy connection. Your application doesn't need to send periodic "keep-alive" messages itself.
        """
        pass

    async def bitget_keep_alive(self, websocket, connection_data=None, ping_interval:int=30):
        """
            https://www.bitget.com/api-doc/common/websocket-intro

        To keep the connection stable:

            Set a timer of 30 seconds.
            If the timer is triggered, send a String 'ping'.
            Expect a 'pong' as a response. If the response message is not received within 30 seconds, please raise an error and/or reconnect.
            The Websocket server accepts up to 10 messages per second. The message includes:

            PING frame (Not tcp ping)
            Messages in JSON format, such as subscribe, unsubscribe.

            If the user sends more messages than the limit, the connection will be disconnected. IPs that are repeatedly disconnected may be blocked by the server;
        """
        id_ws = connection_data.get("id_ws", None)
        while True:
            try:
                print("Sending pong (optional)")
                await websocket.ping("ping") 
            except websockets.ConnectionClosed:
                print(f"Connection closed of {id_ws}. Stopping keep-alive.")
            await asyncio.sleep(ping_interval)

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


class producer(keepalive):
    """
        2 modes: production, testing
    """

    def __init__(self, couch_host, couch_username, couch_password, connection_data, ws_timestamp_keys=None, mode="production"):
        self.couch_server = aiocouchdb.Server(couch_host)
        self.couch_server.resource.credentials = (couch_username, couch_password)
        self.ws_latencies = {}
        self.connection_data = connection_data
        self.ws_timestamp_keys = ws_timestamp_keys
        self.ws_failed_connections = {}
        self.mode = mode
        self.verify_databases() 
        self.populate_ws_latencies()

    def onInterrupt_write_to_json(self):
        """
            Writes to json latencies and failed connections on Interrupt keyboard
        """
        if self.ws_latencies:
            with open(f"ws_latencies.json", 'w') as file:
                json.dump(self.ws_latencies, file)
        if self.ws_failed_connections:
            with open(f"ws_failed_connections.json", 'w') as file:
                json.dump(self.ws_failed_connections, file)
    
    def verify_databases(self):
        connection_data = self.connection_data
        ws_ids = [conndict.get("id_ws") for conndict in connection_data if conndict.get("id_ws") in conndict]
        api_ids = [conndict.get("id_api") for conndict in connection_data if conndict.get("id_api") in conndict]
        list_of_databases = ws_ids + api_ids
        existing_databases = []
        for databse in list_of_databases:
            try:
                self.couch_server[databse]
                existing_databases.append(databse)
            except aiocouchdb.http.ResourceNotFound:
                print(f"Database {databse} doesn't exist. Creating...")
                self.couch_server[databse].create(databse)
                existing_databases.append(databse)
        print(f"CouchDB server with {len(existing_databases)} databases is ready!!!")

    def insert_into_database(self, connection_data, json_data):
        """
            Inserts into couch database
        """
        db = self.couch_server[connection_data.get("id_ws")]
        data = zlib.compress(json_data.encode('utf-8'))
        db.save(data)

    def populate_ws_latencies(self):
        for data in self.connection_data:
            connection_id = data.get("id_ws", None)
            if connection_id is not None:
                self.ws_latencies[connection_id] = {"process_timestamp" : [], "recieved_timestamp" : []}
    
    def get_latency(self, connection_data_dic, data):
        """
            Gets process and recieved timestamps
        """
        data = json.load(data)
        process_timestamp = time.time()
        for key in self.ws_timestamp_keys:
            recieved_timestamp = data.get(key, None)
            if recieved_timestamp is not None:
                self.ws_latencies[connection_data_dic["id_ws"]]["process_timestamp"] = process_timestamp
                self.ws_latencies[connection_data_dic["id_ws"]]["recieved_timestamp"] = recieved_timestamp
                break

    async def check_websocket_connection(self, connection_data_dic):
        try:
            async with websockets.connect(connection_data_dic.get("url")) as websocket:
                await websocket.send(json.dumps(connection_data_dic.get("msg_method")()))
        except websockets.exceptions.WebSocketException as e:
            print(f"WebSocket connection failed: {connection_data_dic.get('id_ws')}.  Reason: {e}")
            self.ws_failed_connections[connection_data_dic.get('id_ws')] = e
    
    async def binance_ws(self, connection_data, producer=None, topic=None):
        """
            producer and topic are reserved for kafka integration
        """
        async for websocket in websockets.connect(connection_data.get("url"), ping_interval=30, timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
            await websocket.send(json.dumps(connection_data.get("msg_method")()))
            keep_alive_task = asyncio.create_task(self.binance_keep_alive(websocket, connection_data))
            while websocket.open:
                try:
                    message = websocket.recv()
                    if message == b'\x89\x00':
                        print(f"Received ping from {connection_data.get('id_ws')}. Sending pong...")
                        await websocket.pong(message)
                    if self.mode == "production":
                        self.insert_into_database(connection_data, message)
                    if self.mode == "testing":
                        self.get_latency(connection_data, message)
                except websockets.ConnectionClosed:
                    print(f"Connection closed of {connection_data.get('id_ws')}")
                    break

    async def bybit_ws(self, connection_data, producer=None, topic=None):
        """
            producer and topic are reserved for kafka integration
        """
        async for websocket in websockets.connect(connection_data.get("url"), ping_interval=30, timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
            await websocket.send(json.dumps(connection_data.get("msg_method")()))
            keep_alive_task = asyncio.create_task(self.bybit_keep_alive(websocket, connection_data))
            while websocket.open:
                try:
                    message = websocket.recv()
                    if message == b'\x89\x00':
                        print(f"Received ping from {connection_data.get('id_ws')}. Sending pong...")
                    if self.mode == "production":
                        self.insert_into_database(connection_data, message)
                    if self.mode == "testing":
                        self.get_latency(connection_data, message)
                except websockets.ConnectionClosed:
                    print(f"Connection closed of {connection_data.get('id_ws')}")
                    break

    async def okx_ws(self, connection_data, producer=None, topic=None):
        """
            producer and topic are reserved for kafka integration
        """
        async for websocket in websockets.connect(connection_data.get("url"), ping_interval=30, timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
            await websocket.send(json.dumps(connection_data.get("msg_method")()))
            keep_alive_task = asyncio.create_task(self.okx_keep_alive(websocket, connection_data))
            while websocket.open:
                try:
                    message = websocket.recv()
                    if message == b'\x89\x00':
                        print(f"Received ping from {connection_data.get('id_ws')}. Sending pong...")
                    if self.mode == "production":
                        self.insert_into_database(connection_data, message)
                    if self.mode == "testing":
                        self.get_latency(connection_data, message)
                except websockets.ConnectionClosed:
                    print(f"Connection closed of {connection_data.get('id_ws')}")
                    break

    async def deribit_ws(self, connection_data, producer=None, topic=None, type_="production"):
        """
            types : production, heartbeats
            producer and topic are reserved for kafka integration
        """
        if type_ == "heartbeats":
            async for websocket in websockets.connect(connection_data.get("url"), ping_interval=30, timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
                await websocket.send(json.dumps(connection_data.get("msg_method")()))
                while websocket.open:
                    try:
                        message = websocket.recv()
                        if message.get("method") == "heartbeat":
                            print(f"Received heartbeat from server.")
                        elif message.get("result") == "ok":
                            test_response = {
                                "jsonrpc": "2.0",
                                "id": message["id"],
                                "result": {
                                    "method": "public/test"   # /api/v2/public/test
                                }
                            }
                            await websocket.send(json.dumps(test_response))
                    except websockets.ConnectionClosed:
                        print(f"Connection closed of {connection_data.get('id_ws')}")
                        break

        if type_ == "production":
            async for websocket in websockets.connect(connection_data.get("url"), ping_interval=30, timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
                await websocket.send(json.dumps(connection_data.get("msg_method")()))
                while websocket.open:
                    try:
                        message = websocket.recv()
                        if self.mode == "production":
                            self.insert_into_database(connection_data, message)
                        if self.mode == "testing":
                            self.get_latency(connection_data, message)
                    except websockets.ConnectionClosed:
                        print(f"Connection closed of {connection_data.get('id_ws')}")
                        break


    async def main(self, ):
        tasks = []

        # Implement that connections between exchanges must have 1 second timeout

        # Establish WebSocket connections
        for info in self.connection_data:
            tasks.append(asyncio.ensure_future(self.connection_data(info)))

        # Handle WebSocket connections and other tasks concurrently
        for info in self.connection_data:
            if info["exchange"] != "deribit":
                tasks.append(asyncio.ensure_future(self.connection_data(info)))
            if info["exchange"] == "deribit":
                tasks.append(asyncio.ensure_future(self.connection_data(info)))

        # Run all tasks concurrently
        try:
            await asyncio.gather(*tasks)
        except (websockets.exceptions.WebSocketException, KeyboardInterrupt) as e:
            if self.mode == "testing":
                print(f"WebSocket connection interrupted: {e}")
                self.onInterrupt_write_to_json()