import asyncio
import websockets
import time
import websockets
import ssl
import rapidjson as json
from .utilis import ws_fetcher_helper
import re
import gzip
import aiocouch
import io
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from aiokafka.errors import KafkaStorageError
from aiokafka.admin.client import AIOKafkaAdminClient
from aiokafka.admin.new_topic import NewTopic
from aiokafka.structs import TopicPartition
import logging
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka._model import TopicCollection




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
        "deribit" : None, # heartbeats mechanism
        "kucoin" : None,  # defined by kucoin server
        "bitget" : 30,
        "bingx" : 5,
        "mexc" : 15, 
        "gateio" : 15,
        "htx" : 5,
        "coinbase" : None # heartbeats mechanism
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
                # print("Sending unsolicited pong")
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
                # print("Sending ping")
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
                # print("Sending ping")
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
                # print("Sending ping")
                await websocket.ping("ping") 
            except websockets.ConnectionClosed:
                print(f"Connection closed of {id_ws}. Stopping keep-alive.")
            await asyncio.sleep(ping_interval)

    async def bingx_keep_alive(self, websocket, connection_data=None, ping_interval:int=5):
        """
            https://bingx-api.github.io/docs/#/en-us/swapV2/socket/

            Once the Websocket Client and Websocket Server get connected, the server will send a heartbeat- Ping message every 5 seconds (the frequency might change).
            When the Websocket Client receives this heartbeat message, it should return Pong message.

            # SPOT
            Once the Websocket Client and Websocket Server get connected, the server will send a heartbeat- Ping message every 5 seconds (the frequency might change).
            {"ping":"2177c68e4d0e45679965f482929b59c2","time":"2022-06-07T16:27:36.323+0800"}

            When the Websocket Client receives this heartbeat message, it should return Pong message.
            {"pong":"2177c68e4d0e45679965f482929b59c2","time":"2022-06-07T16:27:36.323+0800"}

            # PERP
            send simply Pong

            Yeah, as you get keepalive is useless
        """
        id_ws = connection_data.get("id_ws", None)
        while True:
            try:
                # print("Sending ping")
                await websocket.send("Ping") 
            except websockets.ConnectionClosed:
                print(f"Connection closed of {id_ws}. Stopping keep-alive.")
            await asyncio.sleep(ping_interval)

    async def kucoin_keep_alive(self, websocket, connection_data=None, ping_interval=None):
        """
            https://www.kucoin.com/docs/websocket/basic-info/ping
            {
            "id": "1545910590801",
            "type": "ping"
            }
            To prevent the TCP link being disconnected by the server, the client side needs to send ping messages every pingInterval time to the server to keep alive the link.
            After the ping message is sent to the server, the system would return a pong message to the client side.
            If the server has not received any message from the client for a long time, the connection will be disconnected.
            {
            "id": "1545910590801",
            "type": "pong"
            }
        """
        connection_id = connection_data.get("connect_id")
        ping_interval = connection_data.get("ping_interval")
        id_ws = connection_data.get("id_ws", None)
        while True:
            try:
                print("Sending pong")
                await websocket.send({
                                        "id": str(connection_id),
                                        "type": "pong"
                                        })
            except websockets.ConnectionClosed:
                print(f"Connection closed of {id_ws}. Stopping keep-alive.")
            await asyncio.sleep(int(ping_interval))
        
    async def mexc_keep_alive(self, websocket, connection_data=None, ping_interval:int=15):
        """
            https://mexcdevelop.github.io/apidocs/contract_v1_en/#switch-the-stop-limit-price-of-trigger-orders
            Detailed data interaction commands
            Send ping message
            {
            "method": "ping"
            }
            Server return
            {
            "channel": "pong",
            "data": 1587453241453
            }
            List of subscribe/unsubscribe data commands ( ws identification is not required except the list of personal related commands)
            If no ping is received within 1 minute, the connection will be disconnected. It is recommended to send a ping for 10-20 seconds
            The ping message and server return are shown on the right

            https://mexcdevelop.github.io/apidocs/spot_v3_en/#live-subscribing-unsubscribing-to-streams
            PING/PONG
            Request
            {"method":"PING"}
            PING/PONG Response
            {
            "id":0,
            "code":0,
            "msg":"PONG"
            }
        """
        id_ws = connection_data.get("id_ws", None)
        while True:
            try:
                if connection_data.get("instType") == "spot":
                    await websocket.send("PING") 
                else:
                    await websocket.send("ping") 
            except websockets.ConnectionClosed:
                print(f"Connection closed of {id_ws}. Stopping keep-alive.")
            await asyncio.sleep(ping_interval)

    async def gateio_keep_alive(self, websocket, connection_data=None, ping_interval:int=15):
        """
            https://www.gate.io/docs/developers/apiv4/ws/en/#system-ap
            spot.ping

            https://www.gate.io/docs/developers/futures/ws/en/#ping-and-pong
            gate.io futures contract use the protocol layer ping/pong message.The server will initiate a ping message actively. If the client does not reply, the client will be disconnected.
            channel : futures.ping

            https://www.gate.io/docs/developers/apiv4/ws/en/#system-api
            options.ping
        """
        id_ws = connection_data.get("id_ws", None)
        while True:
            try:
                if connection_data.get("instType") == "spot":
                    await websocket.send({"channel" : "spot.ping"}) 
                if connection_data.get("instType") in ["future", "perpetual"]:
                    await websocket.send({"channel" : "futures.ping"}) 
                if connection_data.get("instType") == "option":
                    await websocket.send({"channel" : "options.ping"}) 
            except websockets.ConnectionClosed:
                print(f"Connection closed of {id_ws}. Stopping keep-alive.")
            await asyncio.sleep(ping_interval)

    async def htx_keep_alive(self, websocket, connection_data=None, ping_interval:int=5):
        """
            https://www.htx.com/en-us/opend/newApiPages/?id=662
            Heartbeat and Connection
            {"ping": 1492420473027}
            After connected to Huobi's Websocket server, the server will send heartbeat periodically (currently at 5s interval). The heartbeat message will have an integer in it, e.g.
            {"pong": 1492420473027}
            When client receives this heartbeat message, it should respond with a matching "pong" message which has the same integer in it, e.g.
        """
        pass

    async def coinbase_keep_alive(self, websocket, connection_data=None, ping_interval:int=5):
        """
            https://docs.cloud.coinbase.com/advanced-trade-api/docs/ws-channels#heartbeats-channel
            Subscribe to the heartbeats channel to receive heartbeats messages for specific products every second. Heartbeats include a heartbeat_counter which verifies that no messages were missed..
            Note, 1 hearbeat for a specific product
        """
        pass

class producer(keepalive):
    """
        2 modes: production, testing
    """
    def __init__(self, 
                 connection_data,
                 kafka_host='localhost:9092',
                 num_partitions=5,
                 replication_factor=1, 
                 ):
        """
            databases : CouchDB, mockCouchDB
            ws_timestamp_keys: possible key of timestamps. Needed evaluate latency
            if using tinydb, you must create a folder tinybase
        """
        self.kafka_host = kafka_host
        self.producer = None
        self.admin = AdminClient({'bootstrap.servers': self.kafka_host})
        self.num_partitions = num_partitions
        self.replication_factor = replication_factor
        self.connection_data = connection_data
        self.ws_failed_connections = {}
        # Deribit requires websockets to make api calls. websockets carrotines cant be called within websockets carotines (maybe can idk). This is the helper to mitigate the problem
        try:
            deribit_depths = [x for x in connection_data if x["exchange"]=="deribit" and x["objective"]=="depth"]
            self.deribit_depths = {x.get("id_api_2") : asyncio.run(ws_fetcher_helper(x.get("1stBooksSnapMethod"))) for x in deribit_depths}
            del deribit_depths
        except:
            pass
        self.market_state = {}
        self.kafka_topics = [NewTopic(cond.get("topic_name"), num_partitions=self.num_partitions, replication_factor=self.replication_factor) for cond in self.connection_data]
        self.kafka_topics_names = [cond.get("topic_name") for cond in self.connection_data]
    
    async def send_message_to_topic(self, topic_name, message):
        await self.producer.send_and_wait(topic_name, message.encode())

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
        on_message_method_ws = connection_data.get("on_message_method_ws")
        on_message_method_api = connection_data.get("on_message_method_api_2")

        if connection_data.get("objective") == "depth":
            if self.database_name == "mockCouchDB":
                data = connection_data.get("1stBooksSnapMethod")()
                await self.insert_into_database_2(data, connection_data, on_message_method_api)
            else:
                data = connection_data.get("1stBooksSnapMethod")()
                await self.insert_into_database(data, connection_data, on_message_method_api)
            
        async for websocket in websockets.connect(connection_data.get("url"), timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
            await websocket.send(json.dumps(connection_data.get("msg_method")()))
            keep_alive_task = asyncio.create_task(self.binance_keep_alive(websocket, connection_data))
            while websocket.open:
                try:
                    message = await websocket.recv()
                    if message == b'\x89\x00':
                        print(f"Received ping from {connection_data.get('id_ws')}. Sending pong...")
                        await websocket.pong(message)
                    await self.send_message_to_topic(topic, message)
                except websockets.ConnectionClosed:
                    print(f"Connection closed of {connection_data.get('id_ws')}")
                    break

    async def bybit_ws(self, connection_data, producer=None, topic=None):        
        async for websocket in websockets.connect(connection_data.get("url"), timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
            await websocket.send(json.dumps(connection_data.get("msg_method")()))
            keep_alive_task = asyncio.create_task(self.bybit_keep_alive(websocket, connection_data))
            while websocket.open:
                try:
                    message = await websocket.recv()
                    if message == b'\x89\x00':
                        print(f"Received ping from {connection_data.get('id_ws')}. Sending pong...")
                    await self.send_message_to_topic(topic, message)
                except websockets.ConnectionClosed:
                    print(f"Connection closed of {connection_data.get('id_ws')}")
                    break

    async def okx_ws(self, connection_data, producer=None, topic=None):
        async for websocket in websockets.connect(connection_data.get("url"), timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
            await websocket.send(json.dumps(connection_data.get("msg_method")()))
            keep_alive_task = asyncio.create_task(self.okx_keep_alive(websocket, connection_data))
            while websocket.open:
                try:
                    message = await websocket.recv()
                    await self.send_message_to_topic(topic, message)
                except websockets.ConnectionClosed:
                    print(f"Connection closed of {connection_data.get('id_ws')}")
                    break

    async def deribit_ws(self, connection_data, producer=None, topic=None):
        if connection_data.get("objective") == "heartbeats":
            async for websocket in websockets.connect(connection_data.get("url"), timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
                await websocket.send(json.dumps(connection_data.get("msg_method")()))
                while websocket.open:
                    try:
                        message = await websocket.recv()
                        message = json.loads(message)
                        if message.get("method") == "heartbeat":
                            print(f"Received heartbeat from Deribit server.")
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
        else:
            async for websocket in websockets.connect(connection_data.get("url"), ping_interval=30, timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
                await websocket.send(json.dumps(connection_data.get("msg_method")()))
                while websocket.open:
                    try:
                        message = await websocket.recv()
                        await self.send_message_to_topic(topic, message)
                    except websockets.ConnectionClosed:
                        print(f"Connection closed of {connection_data.get('id_ws')}")
                        break

    async def bitget_ws(self, connection_data, producer=None, topic=None):    
        async for websocket in websockets.connect(connection_data.get("url"), timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
            await websocket.send(json.dumps(connection_data.get("msg_method")()))
            keep_alive_task = asyncio.create_task(self.bitget_keep_alive(websocket, connection_data))
            while websocket.open:
                try:
                    message = await websocket.recv()
                    if message == b'\x89\x00':
                        print(f"Received ping from {connection_data.get('id_ws')}. Sending pong...")
                    await self.send_message_to_topic(topic, message)
                except websockets.ConnectionClosed:
                    print(f"Connection closed of {connection_data.get('id_ws')}")
                    break

    async def kucoin_ws(self, connection_data, producer=None, topic=None):
        connection_message = connection_data.get("msg_method")()
        endpoint, ping_data = connection_data.get("url_method")()
        connect_id = re.search(r'connectId=([^&\]]+)', endpoint).group(1)
        ping_interval = ping_data.get("pingInterval")
        connection_data["ping_interval"] = ping_interval
        connection_data["connect_id"] = connect_id
        async for websocket in websockets.connect(endpoint, timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
            await websocket.send(json.dumps(connection_message))
            keep_alive_task = asyncio.create_task(self.kucoin_keep_alive(websocket, connection_data))
            while websocket.open:
                try:
                    message = await websocket.recv()
                    if "ping" in message:
                        await websocket.send({
                                        "id": str(connect_id),
                                        "type": "pong"
                                        })
                    await self.send_message_to_topic(topic, message)
                except websockets.ConnectionClosed:
                    print(f"Connection closed of {connection_data.get('id_ws')}")
                    break
    
    async def bingx_ws(self, connection_data, producer=None, topic=None):
        async for websocket in websockets.connect(connection_data.get("url"), timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
            await websocket.send(json.dumps(connection_data.get("msg_method")()))
            keep_alive_task = asyncio.create_task(self.bingx_keep_alive(websocket, connection_data))
            while websocket.open:
                try:
                    message = await websocket.recv()
                    message = gzip.GzipFile(fileobj=io.BytesIO(message), mode='rb').read().decode('utf-8')
                    if "ping" in message:
                        message = json.loads(message)
                        await websocket.send(json.dumps({"pong" : message.get("ping"), "time" : message.get("time")}))
                    await self.send_message_to_topic(topic, message)
                except websockets.ConnectionClosed:
                    print(f"Connection closed of {connection_data.get('id_ws')}")
                    break
    
    async def mexc_ws(self, connection_data, producer=None, topic=None):        
        async for websocket in websockets.connect(connection_data.get("url"), timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
            await websocket.send(json.dumps(connection_data.get("msg_method")()))
            keep_alive_task = asyncio.create_task(self.mexc_keep_alive(websocket, connection_data))
            while websocket.open:
                try:
                    message = await websocket.recv()
                    if "pong" in message:
                        await websocket.send("ping")
                    if "PONG" in message:
                        await websocket.send("PONG")
                    await self.send_message_to_topic(topic, message)
                except websockets.ConnectionClosed:
                    print(f"Connection closed of {connection_data.get('id_ws')}")
                    break

    async def gateio_ws(self, connection_data, producer=None, topic=None):        
        async for websocket in websockets.connect(connection_data.get("url"), timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
            await websocket.send(json.dumps(connection_data.get("msg_method")()))
            keep_alive_task = asyncio.create_task(self.gateio_keep_alive(websocket, connection_data))
            while websocket.open:
                try:
                    message = await websocket.recv()
                    if "ping" in message:
                        await websocket.send({"channel" : json.loads(message).get("channel").repalce("ping", "pong")})
                    if "pong" in message:
                        await websocket.send({"channel" : json.loads(message).get("channel").repalce("pong", "ping")})
                    await self.send_message_to_topic(topic, message)
                except websockets.ConnectionClosed:
                    print(f"Connection closed of {connection_data.get('id_ws')}")
                    break

    async def htx_ws(self, connection_data, producer=None, topic=None):
        async for websocket in websockets.connect(connection_data.get("url"), timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
            await websocket.send(json.dumps(connection_data.get("msg_method")()))
            while websocket.open:
                try:
                    message = await websocket.recv()
                    message =  gzip.decompress(message).decode('utf-8')
                    if "ping" in message:
                        await websocket.send(json.dumps({"pong": json.loads(message).get("ping")}))
                    await self.send_message_to_topic(topic, message)
                except websockets.ConnectionClosed:
                    print(f"Connection closed of {connection_data.get('id_ws')}")
                    break

    async def coinbase_ws(self, connection_data, producer=None, topic=None):
        if message.get("channel") != "heartbeats":
            conM, a, b = connection_data.get("msg_method")()
            async for websocket in websockets.connect(connection_data.get("url"), timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
                await websocket.send(json.dumps(conM))
                while websocket.open:
                    try:
                        message = await websocket.recv()
                        await self.send_message_to_topic(topic, message)
                    except websockets.ConnectionClosed:
                        print(f"Connection closed of {connection_data.get('id_ws')}")
                        break
        if message.get("channel") == "heartbeats":
            conM, a, b = connection_data.get("msg_method")()
            async for websocket in websockets.connect(connection_data.get("url"), timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
                await websocket.send(json.dumps(conM))
                while websocket.open:
                    pass

    async def aiohttp_socket(self, connection_data, topic):
        try:
            while True:
                message = await connection_data.get("aiohttpMethod")()
                await self.send_message_to_topic(topic, message)
                time.sleep(connection_data.get("pullTimeout"))
        except Exception as e:
            print(f"Fetch API error of {connection_data.get('id_api')}, {e}")
            await asyncio.sleep(5)

    def ensure_topic_exists(self, topic_names):
        """
            # https://github.com/confluentinc/confluent-kafka-python    
        """
        try:
            fs = self.admin.create_topics(self.kafka_topics)
            for topic, f in fs.items():
                try:
                    f.result()  
                    print("Topic {} created".format(topic))
                except Exception as e:
                    print("Failed to create topic {}: {}".format(topic, e))
        except KeyboardInterrupt:
            print("Keyboard interrupt received. Closing producer...")
        except Exception as e:
            print(f"An error occurred: {e}")


    def describe_topics(self):
        """
            https://github.com/confluentinc/confluent-kafka-python/blob/master/src/confluent_kafka/admin/_topic.py
        """
        topics = self.admin.describe_topics(TopicCollection(self.kafka_topics_names))
        return list(topics.keys())

    def delete_all_topics(self):
        try:
            topics = self.describe_topics()
            self.admin.delete_topics(topics)
            print(f"{topics} were deleted")
        except Exception as e:
            print(f"An error occurred: {e}")
            
            
    async def run_producer(self):
        # self.delete_all_topics()
        # print(self.delete_all_topics())
        self.ensure_topic_exists(self.kafka_topics_names)
        self.producer = AIOKafkaProducer(bootstrap_servers=self.kafka_host)
        await self.producer.start()
        
        tasks = []
        for connection_dict in self.connection_data:
            if "id_ws" in connection_dict:
                exchange = connection_dict.get("exchange")
                ws_method = getattr(self, f"{exchange}_ws", None)
                tasks.append(asyncio.ensure_future(ws_method(connection_dict)))
            if "id_ws" not in connection_dict and "id_api" in connection_dict:
                if connection_dict.get("symbol_update_task") is True:
                    connection_dict["api_call_manager"].pullTimeout = connection_dict.get("pullTimeout")
                    connection_dict["api_call_manager"].send_message_to_topic = self.send_message_to_topic
                    connection_dict["api_call_manager"].topic_name = connection_dict.get("topic_name")
                    tasks.append(asyncio.ensure_future(connection_dict.get("api_call_manager").update_symbols(0)))
                    tasks.append(asyncio.ensure_future(connection_dict.get("api_call_manager").fetch_data()))
                elif connection_dict.get("is_still_nested") is True:
                    connection_dict["api_call_manager"].pullTimeout = connection_dict.get("pullTimeout")
                    connection_dict["api_call_manager"].send_message_to_topic = self.send_message_to_topic
                    connection_dict["api_call_manager"].topic_name = connection_dict.get("topic_name")
                    tasks.append(asyncio.ensure_future(connection_dict.get("api_call_manager").fetch_data()))
                else:
                    tasks.append(asyncio.ensure_future(self.aiohttp_socket(connection_dict, connection_dict.get("topic_name"))))
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("Keyboard interrupt received. Closing producer...")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            await self.producer.stop()
