import asyncio
import time
import websockets
import ssl
import rapidjson as json
from .utilis import ws_fetcher_helper
import re
import gzip
import aiocouch
import io
import sys
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps
import backoff
from aiokafka import AIOKafkaProducer
from errors import websockets_errors, kafka_recoverable_errors, kafka_restart_errors, kafka_giveup_errors, aiohttp_recoverable_errors, kafka_send_errors
from kafka.errors import BrokerNotAvailableError
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka._model import TopicCollection
from prometheus_client import start_http_server, Counter, Gauge, Histogram

def should_give_up(exc):
    return isinstance(exc, kafka_giveup_errors)


# Connection duration
# Latency of every websocket
# Latency of a group of websockets (per exchange)
# Number of disconnects. When do they happe

class keepalive():
    """
        docs references:
            binance: https://binance-docs.github.io/apidocs/spot/en/#websocket-market-streams
            bybit: https://bybit-exchange.github.io/docs/v5/ws/connect
            bingx:
            bitget: https://www.bitget.com/api-doc/common/websocket-intro
            coinbase:
            deribit:
            kucoin:
            gateio:
            mexc:
            htx:
            okx: 
    """
    # prefered ping/pong intervals
    binance_pp_interval = 30
    bybit_pp_interval = 20
    bingx_pp_interval = 5
    bitget_pp_interval = 30
    coinbase_pp_interval = None
    deribit_pp_interval = None
    gateio_pp_interval = 15
    htx_pp_interval = 5
    kucoin_pp_interval = None
    mexc_pp_interval = 15
    okx_pp_interval = 15
    # Running
    binance_keepalive_running = False
    bybit_keepalive_running = False
    bingx_keepalive_running = False
    bitget_keepalive_running = False
    coinbase_keepalive_running = False
    deribit_keepalive_running = False
    gateio_keepalive_running = False
    htx_keepalive_running = False
    kucoin_keepalive_running = False
    mexc_keepalive_running = False
    okx_keepalive_running = False

    def keep_alive(self, running_attr_name:str):
        """ Pattern of keep alive for every exchange"""
        def decorator(func):
            @wraps(func)
            async def wrapper(self, websocket, connection_data, logger, *args, **kwargs):
                running = getattr(self, running_attr_name)
                id_ws = connection_data.get("id_ws", "unknown")
                while getattr(self, running):
                    try:
                        await func(self, websocket, *args, **kwargs)
                    except websockets_errors as e:
                        logger.exception("Keep-Alive error, connection closed: %s", e, id_ws, exc_info=True)
                        break
                    except Exception as e:
                        logger.exception("Unexpected error in keep-alive: %s", e, id_ws, exc_info=True)
                        break
            return wrapper
        return decorator

    @keep_alive("binance_keepalive_running")
    async def binance_keepalive(self, websocket):
        """ initialize binance keep alive caroutine"""
        await websocket.pong(b"") 
        await asyncio.sleep(self.binance_pp_interval) 
            
    def stop_binance_keepalive(self):
        """ stop keep alive """
        self.binance_keepalive_running = False

    @keep_alive("bybit_keepalive_running")
    async def bybit_keepalive(self, websocket, connection_data):
        """ initialize bybit keep alive caroutine"""
        await websocket.ping(json.dumps({"req_id": connection_data.get("req_id"), "op": "ping"})) 
        await asyncio.sleep(self.bybit_pp_interval) 
            
    def stop_bybit_keepalive(self):
        """ stop keep alive """
        self.bybit_keepalive_running = False





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
        id_ws = connection_data.get("id_ws", "unknown")
        req_id = connection_data.get('req_id', None)
        self.okx_keep_alive = True
        
        while self.okx_keep_alive:
            try:
                await websocket.ping("ping") 
                await asyncio.sleep(ping_interval) 
            except websockets_errors as e:  
                self.logger.exception(f"Keep-Alive error for {id_ws}, {e}", exc_info=True)
                break
            except Exception as e:
                self.logger.exception(f"Unexpected error in keep-alive for {id_ws}, {e}", exc_info=True)
                break

    def okx_keep_alive_stop(self):
        self.okx_keep_alive = False

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
        id_ws = connection_data.get("id_ws", "unknown")
        req_id = connection_data.get('req_id', None)
        self.bitget_keep_alive = True
        
        while self.bitget_keep_alive:
            try:
                await websocket.ping("ping") 
                await asyncio.sleep(ping_interval) 
            except websockets_errors as e:  
                self.logger.exception(f"Keep-Alive error for {id_ws}, {e}", exc_info=True)
                break
            except Exception as e:
                self.logger.exception(f"Unexpected error in keep-alive for {id_ws}, {e}", exc_info=True)
                break

    def bitget_keep_alive_stop(self):
        self.bitget_keep_alive = False

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
        
        id_ws = connection_data.get("id_ws", "unknown")
        req_id = connection_data.get('req_id', None)
        self.bingx_keep_alive = True
        
        while self.bingx_keep_alive:
            try:
                await websocket.send("Pong") 
                await asyncio.sleep(ping_interval) 
            except websockets_errors as e:  
                self.logger.exception(f"Keep-Alive error for {id_ws}, {e}", exc_info=True)
                break
            except Exception as e:
                self.logger.exception(f"Unexpected error in keep-alive for {id_ws}, {e}", exc_info=True)
                break

    def bingx_keep_alive_stop(self):
        self.bingx_keep_alive = False

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
        self.kucoin_keep_alive = True
        
        while self.kucoin_keep_alive:
            try:
                await websocket.send({
                                        "id": str(connection_id),
                                        "type": "ping"
                                        })
                await asyncio.sleep(ping_interval) 
            except websockets_errors as e:  
                self.logger.exception(f"Keep-Alive error for {id_ws}, {e}", exc_info=True)
                break
            except Exception as e:
                self.logger.exception(f"Unexpected error in keep-alive for {id_ws}, {e}", exc_info=True)
                break
            
    def kucoin_keep_alive_stop(self):
        self.kucoin_keep_alive = False
        
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
        ping_interval = connection_data.get("ping_interval")
        id_ws = connection_data.get("id_ws", None)
        self.mexc_keep_alive = True
        while self.mexc_keep_alive:
            try:
                if connection_data.get("instType") == "spot":
                    await websocket.send("PING") 
                    await asyncio.sleep(ping_interval) 
                else:
                    await websocket.send("ping") 
                    await asyncio.sleep(ping_interval) 
            except websockets_errors as e:  
                self.logger.exception(f"Keep-Alive error for {id_ws}, {e}", exc_info=True)
                break
            except Exception as e:
                self.logger.exception(f"Unexpected error in keep-alive for {id_ws}, {e}", exc_info=True)
                break

    def mexc_keep_alive_stop(self):
        self.mexc_keep_alive = False

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
        ping_interval = connection_data.get("ping_interval")
        id_ws = connection_data.get("id_ws", None)
        self.gateio_keep_alive = True
        while self.gateio_keep_alive:
            try:
                if connection_data.get("instType") == "spot":
                    await websocket.send({"channel" : "spot.ping"}) 
                if connection_data.get("instType") in ["future", "perpetual"]:
                    await websocket.send({"channel" : "futures.ping"}) 
                if connection_data.get("instType") == "option":
                    await websocket.send({"channel" : "options.ping"}) 
                await asyncio.sleep(ping_interval) 
            except websockets_errors as e:  
                self.logger.exception(f"Keep-Alive error for {id_ws}, {e}", exc_info=True)
                break
            except Exception as e:
                self.logger.exception(f"Unexpected error in keep-alive for {id_ws}, {e}", exc_info=True)
                break
            
    def gateio_keep_alive_stop(self):
        self.gateio_keep_alive = False

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
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    def __init__(self, 
                 connection_data,
                 kafka_host='localhost:9092',
                 num_partitions=5,
                 replication_factor=1,
                 producer_reconnection_attempts=5, 
                 prometeus_start_server=8000
                 ):
        """
            databases : CouchDB, mockCouchDB
            ws_timestamp_keys: possible key of timestamps. Needed evaluate latency
            if using tinydb, you must create a folder tinybase
        """
        self.kafka_host = kafka_host
        self.producer = None
        self.producer_running = False
        self.producer_reconnection_attempts = producer_reconnection_attempts
        self.admin = AdminClient({'bootstrap.servers': self.kafka_host})
        self.num_partitions = num_partitions
        self.replication_factor = replication_factor
        self.connection_data = connection_data
        self.ws_failed_connections = {}
        self.start_prometeus_server = start_http_server
        # Deribit requires websockets to make api calls. websockets carrotines cant be called within websockets carotines (maybe can idk). This is the helper to mitigate the problem
        try:
            deribit_depths = [x for x in connection_data if x["exchange"]=="deribit" and x["objective"]=="depth"]
            self.deribit_depths = {x.get("id_api_2") : asyncio.run(ws_fetcher_helper(x.get("1stBooksSnapMethod"))) for x in deribit_depths}
            del deribit_depths
        except:
            pass
        self.kafka_topics = [NewTopic(cond.get("topic_name"), num_partitions=self.num_partitions, replication_factor=self.replication_factor) for cond in self.connection_data]
        self.kafka_topics_names = [cond.get("topic_name") for cond in self.connection_data]
        self.logger = self.setup_logger(base_path, log_file_bytes, log_file_backup_count)
        self.loop = None
        
        # Connection metrics
        self.ws_connections_active = Gauge('websocket_connections_active', 'Number of active WebSocket connections')
        self.api_connections_active = Gauge('API Asyncio pipes active', 'Number of active API Asyncio pipes active')
        self.connection_errors = Counter('app_connection_errors_total', 'Total number of connection errors')
        
        self.connection_duration = Histogram('app_connection_duration_seconds', 'Time connected before disconnect', buckets=(1, 5, 10, 30, 60, 300, 600))
        self.message_throughput = Counter('app_messages_total', 'Total messages sent and received')
        self.data_volume = Counter('app_data_volume_bytes', 'Total data transmitted in bytes')
        self.reconnection_attempts = Counter('app_reconnection_attempts_total', 'Total reconnection attempts')
        self.ping_pong_duration = Histogram('app_ping_pong_duration_seconds', 'Round-trip time for ping-pong messages', buckets=(0.01, 0.05, 0.1, 0.5, 1, 5))

    def get_asyncio_loop(self, loop):
        """ Gets loop arg"""
        self.loop=loop
        
    def start_metrics_server(self):
        self.start_prometeus_server()
        
    def setup_logger(self, log_file, maxBytes=10*1024*1024, backupCount=5):
        """
            Setups rotating logger with spesific logfile size and backup count
        """
        log_file = log_file / "logs/producerlogger.log"
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        file_handler = RotatingFileHandler(
                        log_file, 
                        maxBytes=maxBytes, 
                        backupCount=backupCount      
                    )
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger
                                            
    async def binance_ws(self, connection_data, producer=None, topic=None):
        """
            producer and topic are reserved for kafka integration
            Maintain a WebSocket connection with automatic reconnection using exponential backoff.
        """ 
        @backoff.on_exception(backoff.expo,
                            websockets_errors,
                            max_tries=8)
        async def connect_and_listen():
            try:
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
                        except websockets_errors as e:  
                            self.logger.exception(f"WebSocket error for {connection_data.get('id_ws')}, {e}", exc_info=True)
                            break
            except asyncio.TimeoutError as e:
                self.logger.exception(f"WebSocket connection timed out for {connection_data.get('id_ws')}, {e}", exc_info=True)
            except Exception as e:
                self.logger.exception(f"Failed to establish WebSocket connection for {connection_data.get('id_ws')}, {e}", exc_info=True)
            finally:
                if self.binance_keep_alive:
                    self.binance_keep_alive_stop()
                self.logger.info(f"WebSocket connection for {connection_data.get('id_ws')} has ended.")

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

    @backoff.on_exception(backoff.expo,
                          kafka_recoverable_errors,
                          max_tries=5,
                          max_time=300,
                          giveup=should_give_up)
    def handle_kafka_errors_backup(self, func):
        """
            Decorator for error and reconnecting handling
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except kafka_recoverable_errors as e:
                self.logger.exception("%s raised for topic %s: %s", type(e).__name__, args[1], e, exc_info=True)
                raise
            except kafka_restart_errors as e:
                self.logger.exception("kafka_restart_errors raised, reconnecting producer... %s", e, exc_info=True)
                await self.reconnect_producer()
            except kafka_giveup_errors as e:
                self.logger.exception("kafka_giveup_errors raised, stopping producer... %s", e, exc_info=True)
                await self.producer.stop()
        return wrapper

    async def start_producer(self):
        """
            Starts producer with handling
        """
        await self.producer.start()
        print("Producer started successfully.")

    @backoff.on_exception(backoff.expo,
                        BrokerNotAvailableError,
                        max_time=300)
    async def reconnect_producer(self):
        """
            Reconnects producer in case of crashing
        """
        for i in range(self.producer_reconnection_attempts):  
            await asyncio.sleep(10) 
            try:
                await self.run_producer(is_reconnect=True)
                self.logger.info("Reconnected to the broker successfully")
                self.producer_running = True
                return True
            except Exception as e:
                self.logger.exception("Reconnection failed: %s", str(e))
        self.logger.critical("Unable to reconnect to the broker after several attempts.")
        await self.producer.stop() 
        self.producer_running = False
        return False

    async def ensure_topic_exists(self):
        """
            Ensures that topics exist with necessary configurations
        """
        fs = self.admin.create_topics(self.kafka_topics)
        for topic, f in fs.items():
            f.result()  
            print(f"Topic {topic} created")

    @handle_kafka_errors_backup
    async def run_producer(self, is_reconnect=False):
        """
            Runs roducer
        """
        try:
            if is_reconnect is False:
                self.ensure_topic_exists()    
                self.producer = AIOKafkaProducer(bootstrap_servers=self.kafka_host, loop=self.loop)
            await self.start_producer()
            tasks = []
            for delay, connection_dict in enumerate(self.connection_data):
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
                        tasks.append(asyncio.ensure_future(self.aiohttp_socket(connection_dict, connection_dict.get("topic_name"), initial_delay=delay)))
                await asyncio.gather(*tasks)
        except kafka_recoverable_errors as e:
            self.logger.exception("Recoverable error raised %s, reconnecting", e, exc_info=True)
            raise  
        except kafka_restart_errors:
            self.logger.exception("kafka_restart_errors raised, reconnecting producer... {e}", exc_info=True)
            await self.reconnect_producer()
        except kafka_giveup_errors:
            self.logger.exception("kafka_giveup_errors raised, stopping producer... {e}", exc_info=True)
            await self.producer.stop()
    
    @handle_kafka_errors_backup
    async def send_message_to_topic(self, topic_name, message):
        """
            Ensures messages are send while dealing with errors
        """
        await self.producer.send_and_wait(topic_name, message.encode("utf-8"))
    

    @backoff.on_exception(backoff.expo,
                        aiohttp_recoverable_errors,  
                        max_tries=10,  
                        max_time=300) 
    async def aiohttp_socket(self, connection_data, topic, initial_delay):
        """ initiates aiohttp pipe"""
        await asyncio.sleep(initial_delay)
        try:
            while True:
                message = await connection_data.get("aiohttpMethod")()
                await self.send_message_to_topic(topic, message)
                message = message.encode("utf-8")
                print(sys.getsizeof(message))
                await asyncio.sleep(connection_data.get("pullTimeout"))
        except aiohttp_recoverable_errors as e:  
            self.logger.exception("Error from {connection_data.get('id_api')}: %s", e, exc_info=True)
            raise  

            
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
            
            
            
# 1. Granularity of connection duration per exchange
# 2. Measure latency for every book websocket and consider sending alerts when latency os too high. Integrate telegram into the notification system. Or email notification system. Many modern monitoring tools like Prometheus come with built-in alerting functionalities. Prometheus’s Alertmanager, for example, can route alerts to various endpoints including email, Slack, PagerDuty, and more.
# 3. Overall system latency to correlate with CPU and memory usage to identify resource bottlenecks
# 4. Reconnection attempts
# import psutil

# # CPU Utilization
# cpu_usage = psutil.cpu_percent(interval=1)

# # Memory Utilization
# memory = psutil.virtual_memory()
# memory_usage = memory.percent  # percentage of memory use

# print(f"CPU Usage: {cpu_usage}%")
# print(f"Memory Usage: {memory_usage}%")


# 5. Infrastructure Health: Monitor infrastructure metrics such as server load, network I/O, and disk I/O. 

# # Disk I/O
# disk_io = psutil.disk_io_counters()
# print(disk_io)

# # Network I/O
# net_io = psutil.net_io_counters()
# print(net_io)

# 6. Historical Data Analysis: Store historical metrics data for trend analysis and capacity planning. 
# Summarize the data before storing it

# Time-Series Databases: Databases like InfluxDB or TimescaleDB (an extension to PostgreSQL) are designed for time-series data and can be ideal for storing metrics. These databases efficiently handle high write and read loads and are good at compressing data.
# Relational Databases: If your load is not extremely high, traditional relational databases like MySQL or PostgreSQL can be used effectively with proper indexing.
# Integration with Prometheus: If you are using Prometheus for monitoring, it already stores time-series data and provides capabilities for querying historical data. Prometheus stores its data in a custom time-series database format optimized for high performance and efficiency.

# Disk Space: The amount of disk space required will grow over time, especially with high-frequency data collection. You need to estimate the data growth and plan the infrastructure accordingly.
# Operational Maintenance: Over such long periods, you will likely need to perform maintenance on the storage system, including hardware replacements and upgrades, migration to newer systems, and possibly changes in the data format.
# Data Summarization: Over long periods, it may become impractical to keep all data at the highest granularity. You might need to summarize or downsample older data.
# Integration with External Long-term Storage Solutions: Because Prometheus is not ideally suited for multi-year data retention due to its in-memory indexing, many use it in conjunction with other solutions designed for long-term storage. Common strategies include:
# Using Prometheus with Remote Write: Prometheus can be configured to "remote write" its data to external long-term storage systems such as Thanos, Cortex, or M3, which are designed to handle longer retention periods efficiently.
# Thanos: Integrating Prometheus with Thanos can provide a seamless way to manage long-term storage across multiple Prometheus instances. Thanos adds a storage layer that supports querying large amounts of historical metric data and can integrate with cloud storage solutions like Amazon S3, Google Cloud Storage, or Microsoft Azure Blob Storage, making it more scalable and resilient.
# Cortex: Similar to Thanos, Cortex provides horizontally scalable, highly available, multi-tenant, long-term storage for Prometheus.

# # Faust has proper metrics to monitor kafka servers