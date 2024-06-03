import string
import asyncio
import time
import ssl
import gzip
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from functools import wraps, partial
import io
import sys
import backoff
from aiokafka import AIOKafkaProducer
import websockets
from websockets import WebSocketClientProtocol
from  websockets.exceptions import WebSocketException, ConnectionClosed
from prometheus_client import start_http_server, Counter, Gauge, Histogram  # https://prometheus.github.io/client_python/exporting/http/wsgi/
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka._model import TopicCollection
import psutil
import rapidjson as json
from kafka.errors import BrokerNotAvailableError, TopicAlreadyExistsError
from kafka.errors import RETRY_ERROR_TYPES as kafka_RETRY_ERROR_TYPES
from .errors import websockets_heartbeats_errors, restart_producer_errors, kafka_message_errors, aiohttp_recoverable_errors, kafka_giveup_errors
from .utilis import ws_fetcher_helper
from confluent_kafka.cimpl import KafkaException


def should_give_up(exc):
    return isinstance(exc, kafka_giveup_errors)

base_path = Path(__file__).parent.parent

class DecoratorsPatters:

    @staticmethod
    def keepalive_decorator(func):
        """ Pattern of keep alive for every exchange"""
        async def wrapper(self, *args, **kwargs):
            connection_data = kwargs.get('connection_data')
            websocket = kwargs.get('websocket')
            logger = kwargs.get('logger')
            id_ws = connection_data.get("id_ws", "unknown")
            exchange = connection_data.get("exchange")  
            
            if exchange == "kucoin":
                pingInterval, pingTimeout = args[0].get_kucoin_pingInterval(connection_data)
                args[0].kucoin_pp_intervals[id_ws] = {
                    "pingInterval": pingInterval,
                    "pingTimeout": pingTimeout
                }
            
            args[0].keep_alives_running[id_ws] = True
            
            while args[0].keep_alives_running.get(id_ws, False):
                try:
                    await func(self, websocket, connection_data, logger, *args, **kwargs)
                except aiohttp_recoverable_errors as e:
                    logger.error("Keep-Alive error, connection closed: %s, ID_WS: %s", e, id_ws, exc_info=True)
                    args[0].KEEP_ALIVE_ERRORS.labels(error_type='recoverable_error', exchange=exchange, websocket_id=id_ws).inc()
                    raise
                except Exception as e:
                    logger.error("Keep-Alive error, connection closed: %s, ID_WS: %s", e, id_ws, exc_info=True)
                    args[0].KEEP_ALIVE_DISCONNECTS.labels(websocket_id=id_ws, exchange=exchange).inc()
                    break
        def backoff_inner_wrapper(self, *args, **kwargs):
            return backoff.on_exception(backoff.expo,
                    WebSocketException,
                    max_tries=self.max_reconnect_retries)(wrapper)(self, *args, **kwargs)
        return backoff_inner_wrapper
    
    @staticmethod
    def websocket_wrapper(keepalattr=None):
        """ pattern for every websocket connection, errors and logging """
        def wrapper(func):
            async def inner_websocket_wrapper(self, *args, **kwargs):
                connection_data = args[0]
                id_ws = connection_data.get('id_ws')
                connection_message = connection_data.get("msg_method")()
                self.ws_messages[id_ws] = connection_message
                websocket = await self.__wsaenter__(connection_data)
                connection_start_time = time.time() 
                try:
                    
                    await websocket.send(json.dumps(connection_message))
                    
                    if keepalattr:
                        keep_alive_method = getattr(self, keepalattr)
                        asyncio.create_task(keep_alive_method(self, websocket=websocket, connection_data=connection_data, logger=self.logger))
                                            
                    while websocket.open:
                        try:
                            await func(self, connection_data=connection_data, websocket=websocket, *args, **kwargs)
                        except (websockets_heartbeats_errors, WebSocketException, TimeoutError) as e: 
                            self.logger.error("WebSocket error or disconnection for %s, %s", id_ws, e, exc_info=True)
                            self.process_disconnects_metrics(id_ws, connection_start_time)
                            raise
                            
                except asyncio.TimeoutError as e:
                    self.logger.error("WebSocket connection timed out for %s, %s", id_ws, e, exc_info=True)
                except Exception as e:
                    self.logger.error("Failed to establish WebSocket connection for %s, %s", id_ws, e, exc_info=True)
                finally:
                    # metrics
                    if "CONNECTION_DURATION" in self.producer_metrics:
                        duration = time.time() - connection_start_time
                        self.CONNECTION_DURATION.labels(websocket_id=id_ws).set(duration)

                    # safe heartbeat exit
                    if kwargs.get("keep_alive_caroutine_attr") is not None:
                        await self.stop_keepalive(connection_data)
                    else:
                        if "heartbeat" in id_ws:
                            
                            related_ws, heartbeat_key = self._get_related_ws(connection_data)
                            are_all_down = all(not self.websockets.get(id_ws).open for id_ws in related_ws)
                            
                            if are_all_down:
                                heartbeat_websocket = self.websockets.get(heartbeat_key)
                                cd = [x for x in self.connection_data if x.get("id_ws") == heartbeat_websocket][0]
                                self.__wsaexit__(websocket, cd)
                    
                    self.logger.info("WebSocket connection for %s has ended.", id_ws)
                    await self.__wsaexit__(websocket, connection_data)
                        
            def backoff_inner_websocket_wrapper(self, *args, **kwargs):
                return backoff.on_exception(
                    backoff.expo,
                    (WebSocketException, TimeoutError, ConnectionClosed),
                    max_tries=self.max_reconnect_retries,
                    on_backoff=self.on_backoff
                )(inner_websocket_wrapper)(self, *args, **kwargs)

            return backoff_inner_websocket_wrapper
        return wrapper
    

    @staticmethod
    def handle_kafka_errors_backup(func):
        """
            Decorator for error and reconnecting handling
        """
        max_retries = 0
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            max_retries = self.max_reconnect_retries
            try:
                return await func(self, *args, **kwargs)
            except kafka_RETRY_ERROR_TYPES as e:
                if len(args) != 0:
                    self.logger.error("%s raised for topic %s: %s", type(e).__name__, args[1].get("topic_name"), e, exc_info=True)
                else:
                    self.logger.error("%s", e, exc_info=True)
                raise
            except TopicAlreadyExistsError:
                self.logger.info("Topic already exists, skipping to the next iteration...")
            except restart_producer_errors as e:
                self.logger.error("kafka_restart_errors raised, reconnecting producer... %s", e, exc_info=True)
                await self.reconnect_producer()
            except kafka_giveup_errors as e:
                self.logger.error("kafka_giveup_errors raised, stopping producer... %s", e, exc_info=True)
                await self.producer.stop()
        return backoff.on_exception(
            backoff.expo,
            kafka_RETRY_ERROR_TYPES,
            max_tries=max_retries,
            max_time=300,
            giveup=should_give_up
        )(wrapper)


class keepalive(DecoratorsPatters):
    """
        docs references:
            binance: https://binance-docs.github.io/apidocs/spot/en/#websocket-market-streams
            bybit: https://bybit-exchange.github.io/docs/v5/ws/connect
            bingx: 
                perpetual : https://bingx-api.github.io/docs/#/en-us/swapV2/socket/
                spot: https://bingx-api.github.io/docs/#/en-us/spot/socket/
            bitget: https://www.bitget.com/api-doc/common/websocket-intro
            coinbase: https://docs.cloud.coinbase.com/advanced-trade-api/docs/ws-channels#heartbeats-channel
            deribit: https://docs.deribit.com/#public-set_heartbeat
            kucoin: https://www.kucoin.com/docs/websocket/basic-info/ping
            gateio: https://www.gate.io/docs/developers/apiv4/ws/en/#system-ap
                    https://www.gate.io/docs/developers/futures/ws/en/#ping-and-pong
                    https://www.gate.io/docs/developers/apiv4/ws/en/#system-api
            mexc: https://mexcdevelop.github.io/apidocs/contract_v1_en/#switch-the-stop-limit-price-of-trigger-orders
                  https://mexcdevelop.github.io/apidocs/spot_v3_en/#live-subscribing-unsubscribing-to-streams
            htx:  https://www.htx.com/en-us/opend/newApiPages/?id=662
            okx: https://www.okx.com/docs-v5/en/#overview-websocket-overview
    """
    # prefered ping/pong intervals
    binance_pp_interval = 180
    binance_timeout_interval = 600
    bybit_pp_interval = 20
    bybit_timeout_interval = 40           # unspecified by bybit
    bingx_pp_interval = 5
    bingx_timeout_interval = 15           # unspecified by bingx
    bitget_pp_interval = 30
    bitget_timeout_interval = 30
    coinbase_pp_interval = None            # uses hearbeats to keep connection stable
    coinbase_timeout_interval = None
    deribit_pp_interval = None             # uses heartbeats
    deribit_timeout_interval = None
    gateio_pp_interval = 5
    gateio_timeout_interval = 10           # unspecified by gateio
    htx_pp_interval = 5
    htx_timeout_interval = 10              # needs to be refactored
    kucoin_pp_interval = None              # defined during initialization
    kucoin_timeout_interval = None         # defined during initialization
    mexc_pp_interval = 15
    mexc_timeout_interval = 60
    okx_pp_interval = 30
    okx_timeout_interval = 30
    # Running
    keep_alives_running = {}
    kucoin_pp_intervals = {}
    # Errors metricks
    KEEP_ALIVE_ERRORS = Counter('keep_alive_errors', 'Count of errors in keep alive', ['error_type', 'websocket_id', 'exchange'])
    KEEP_ALIVE_DISCONNECTS = Counter('keep_alive_disconnects', 'Count of disconnects in keep alive', ['websocket_id', 'exchnage'])
    KEEP_ALIVE_COUNTS = Counter('keep_alive_counts', 'Counts timmes ping/pong interactions', ['websocket_id'])
    last_ping_pong_times = {}
    # reconnect retries
    max_reconnect_retries = 8

    def __init__(self, max_reconnect_retries=8, *args, **kwargs):
        self.max_reconnect_retries = max_reconnect_retries


    def get_kucoin_pingInterval(self, conData):
        """ dynamicall gets ping interval of a kucoin websocket connection """
        d1, d2 = conData.get("url_method")()
        pingInterval = d2.get("pingInterval")
        pingTimeout = d2.get("pingTimeout")
        return pingInterval, pingTimeout

    async def stop_keepalive(self, connection_data):
        """ stop keep alive """
        self.keep_alives_running[connection_data.get("id_ws")] = False

    @DecoratorsPatters.keepalive_decorator
    async def binance_keepalive_func(self, *args, **kwargs):
        """ binance sends you ping and you respond with pong. NOT NEEDED"""
        websocket = kwargs.get("websocket")
        await websocket.pong(b"") 
        await asyncio.sleep(self.binance_pp_interval) 

    @DecoratorsPatters.keepalive_decorator
    async def bybit_keepalive(self, *args, **kwargs):
        """ initialize bybit keep alive caroutine"""
        id_ws = kwargs.get("connection_data").get("id_ws")
        websocket = kwargs.get("websocket")
        await websocket.send(json.dumps({"op": "ping"})) 
        print(f"Ping sent to {id_ws}")
        await asyncio.sleep(self.bybit_pp_interval) 
    
    @DecoratorsPatters.keepalive_decorator
    async def okx_keepalive(self, *args, **kwargs):
        """ initialize okx keep alive caroutine"""
        websocket = kwargs.get("websocket")
        await websocket.send("ping") 
        await asyncio.sleep(self.okx_pp_interval) 
    
    @DecoratorsPatters.keepalive_decorator
    async def bitget_keepalive(self, *args, **kwargs):
        """ initialize bitget keep alive caroutine"""
        websocket = kwargs.get("websocket")
        await websocket.send("ping") 
        await asyncio.sleep(self.bitget_pp_interval) 
    
    @DecoratorsPatters.keepalive_decorator
    async def bingx_keepalive(self, *args, **kwargs):
        """ initialize bingx keep alive caroutine (ONLY FOR PERPETUAL WEBSOCKETS)"""
        websocket = kwargs.get("websocket")
        await websocket.send("Pong") 
        await asyncio.sleep(self.bingx_pp_interval) 

    @DecoratorsPatters.keepalive_decorator
    async def kucoin_keepalive(self, *args, **kwargs):
        """ initialize kucoin keep alive caroutine"""
        websocket = kwargs.get("websocket")
        connection_data = kwargs.get("connection_data")
        await websocket.send(json.dumps({"id": str(connection_data.get("connection_id")), "type": "ping"}))
        await asyncio.sleep(self.kucoin_pp_intervals.get(connection_data.get("id_ws")).get("pingInterval", 18000)) 
    
    @DecoratorsPatters.keepalive_decorator
    async def mexc_keepalive(self, *args, **kwargs):
        """ initialize mexc keep alive caroutine"""
        websocket = kwargs.get("websocket")
        connection_data = kwargs.get("connection_data")
        if connection_data.get("instType") == "spot":
            await websocket.send(json.dumps({"method": "PING"}))
        else:
            await websocket.send(json.dumps({"method": "ping"})) 
        await asyncio.sleep(self.mexc_pp_interval) 

    @DecoratorsPatters.keepalive_decorator
    async def htx_keepalive(self, *args, **kwargs):
        """ initialize mexc keep alive caroutine"""
        websocket = kwargs.get("websocket")
        connection_data = kwargs.get("connection_data")
        await websocket.send(json.dumps({"method": "ping"}))
        await asyncio.sleep(self.mexc_pp_interval) 
    
    @DecoratorsPatters.keepalive_decorator
    async def gateio_keepalive(self, *args, **kwargs):
        """ initialize gateio keep alive caroutine"""
        websocket = kwargs.get("websocket")
        connection_data = kwargs.get("connection_data")
        if connection_data.get("instType") == "spot":
            await websocket.send('{"time": %d, "channel" : "spot.ping"}' % int(time.time()))
        if connection_data.get("instType") in ["future", "perpetual"]:
            await websocket.send('{"time": %d, "channel" : "futures.ping"}' % int(time.time()))
        if connection_data.get("instType") == "option":
            await websocket.send('{"time": %d, "channel": "options.ping"}'% int(time.time()))
        await asyncio.sleep(self.gateio_pp_interval) 
            
class publisher(keepalive):
    """
        2 modes: production, testing
    """
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    def __init__(self, 
                connection_data,
                kafka_host = 'localhost:9092',
                num_partitions = 2,
                replication_factor = 1,
                producer_reconnection_attempts = 5, 
                prometeus_start_server = 9090,
                log_file_bytes = 10*1024*1024,
                log_file_backup_count = 5,
                producer_metrics = [
                    "CONNECTION_DURATION",
                    "TOTAL_MESSAGES",
                    "MESSAGE_SIZE",
                    "ERRORS_DISCONNECTS",
                    "RECONNECT_ATTEMPTS",
                    "LATENCY",
                    "CPU_USAGE",
                    "MEMORY_USAGE",
                    "DISK_IO",
                    "NETWORK_IO"
                ],
                cpu_memory_catch_interval = 60,
                max_reconnect_retries=8,
                 ):
        """
            databases : CouchDB, mockCouchDB
            ws_timestamp_keys: possible key of timestamps. Needed evaluate latency
            if using tinydb, you must create a folder tinybase
        """
        super().__init__(max_reconnect_retries)
        self.connection_data = connection_data
        # kafka setup
        self.kafka_host = kafka_host
        self.producer = None
        self.producer_running = False
        self.producer_reconnection_attempts = producer_reconnection_attempts
        self.admin = AdminClient(
            {
                'bootstrap.servers': self.kafka_host, 
                'message.max.bytes': 10485760,
                'max.partition.fetch.bytes': 10485760,
                'request.timeout.ms': 30000, 
                'delivery.timeout.ms': 60000,
                'auto.offset.reset': 'earliest',
                'fetch.message.max.bytes': 10485760,
                'max.partition.fetch.bytes': 10485760,
                'session.timeout.ms': 60000 ,
                'compression.type': 'gzip',
                'debug': 'msg' 
                }
            )
        self.num_partitions = num_partitions
        self.replication_factor = replication_factor
        self.kafka_topics = [
            NewTopic(
                cond.get("topic_name"), 
                num_partitions=self.num_partitions, 
                replication_factor=self.replication_factor,
                config={
                    'max.message.bytes': '10485760'  
                }
                ) 
                for cond in self.connection_data
                ]
        self.kafka_topics_names = [cond.get("topic_name") for cond in self.connection_data]
        # websockets setup
        self.ws_messages = {} #ids were dynamicall generated upon creating websockets. IF you need them, extract them from here
        self.websockets = {}
        self.ws_related_to_heartbeat_channel = {}
        if self.ws_related_to_heartbeat_channel != {}:
            self.___get_list_related_websockets()
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        self.wsmessage_max_size = 1024 * 1024 * 10
        # metrics, logging
        self.cpu_memory_catch_interval = cpu_memory_catch_interval
        self.producer_metrics = producer_metrics
        self.start_prometeus_server = partial(start_http_server, prometeus_start_server)
        self.logger = self.setup_logger(base_path, log_file_bytes, log_file_backup_count)
        # Deribit requires websockets to make api calls. websockets carrotines cant be called within websockets carotines (maybe can idk). This is the helper to mitigate the problem
        try:
            deribit_depths = [x for x in connection_data if x["exchange"]=="deribit" and x["objective"]=="depth"]
            self.deribit_depths = {x.get("id_api_2") : asyncio.run(ws_fetcher_helper(x.get("1stBooksSnapMethod"))) for x in deribit_depths}
            del deribit_depths
        except Exception as e:
            self.logger.error("Couldnt fetch deribit depth %s", e, exc_info=True)
        self.loop = None
        # Metrics definitions using prometheus_client library
        if "CONNECTION_DURATION" in producer_metrics:
            self.CONNECTION_DURATION = Gauge('websocket_connection_duration_seconds', 'Time spent in WebSocket connection', ['websocket_id'])
        # Note on historgram: Crucially, after retrieving data, Prometheus resets the histogram's internal counters to zero.
        if "TOTAL_MESSAGES" in producer_metrics:
            self.TOTAL_MESSAGES = Gauge('websocket_messages_sent_total', 'Total number of WebSocket messages sent', ['websocket_id'])
        if "MESSAGE_SIZE" in producer_metrics:
            self.MESSAGE_SIZE = Histogram('websocket_message_size_bytes', 'Size of WebSocket messages', ['websocket_id'], buckets=[64, 256, 1024, 4096, 16384, 65536, 262144, 1048576, 10 * 1048576])
        if "ERRORS_DISCONNECTS" in producer_metrics:
            self.ERRORS_DISCONNECTS = Counter('websocket_errors_disconnects_total', 'Count of errors and disconnects', ['websocket_id'])
        if "RECONNECT_ATTEMPTS" in producer_metrics:
            self.RECONNECT_ATTEMPTS = Counter('websocket_reconnect_attempts_total', 'Count of reconnect attempts after disconnecting', ['websocket_id'])
        if "NETWORK_LATENCY" in producer_metrics:
            self.NETWORK_LATENCY = Gauge('websocket_latency_seconds', 'Latency of WebSocket connections', ['websocket_id'])
        if "CPU_USAGE" in producer_metrics:
            self.CPU_USAGE = Gauge('server_cpu_usage', 'CPU usage of the server')
        if "MEMORY_USAGE" in producer_metrics:
            self.MEMORY_USAGE = Gauge('server_memory_usage_bytes', 'Memory usage of the server')
        if "DISK_IO" in producer_metrics:
            self.DISK_IO = Gauge('server_disk_io_bytes', 'Disk I/O of the server')
        if "NETWORK_IO" in producer_metrics:
            self.NETWORK_IO = Gauge('server_network_io_bytes', 'Network I/O of the server')

        
        self.heartbeats_ids = {}


    #  Producer setup

    def get_asyncio_loop(self, loop):
        """ Gets loop arg"""
        self.loop=loop
        
    def start_metrics_server(self):
        """ starts prometeus server"""
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

    # metrics
    
    def update_cpu_usage(self):
        """ Get CPU usage percentage """
        cpu_percent = psutil.cpu_percent(interval=1)  # interval specifies the time to wait
        self.CPU_USAGE.set(cpu_percent)

    def update_memory_usage(self):
        """Get memory usage"""
        memory = psutil.virtual_memory()
        self.MEMORY_USAGE.set(memory.used)  # memory.used gives us the amount of used memory

    def update_disk_io(self):
        """Get disk I/O statistics"""
        disk_io = psutil.disk_io_counters()
        self.DISK_IO.set(disk_io.read_bytes + disk_io.write_bytes)  # Sum of read and write bytes

    def update_network_io(self):
        """Get network I/O statistics"""
        network_io = psutil.net_io_counters()
        self.NETWORK_IO.set(network_io.bytes_sent + network_io.bytes_recv)  # Sum of sent and received bytes
        
    async def CPU_MEMORY_diskIO_networkIO_update(self):
        while True:
            self.update_cpu_usage()
            self.update_memory_usage()
            self.update_disk_io()
            self.update_network_io()
            await asyncio.sleep(self.cpu_memory_catch_interval)  # update every 60 seconds

    # Websocket related
    
    def ___get_list_related_websockets(self):
        """
            Must be called on initialization.

            Deribit and conibase use separated websocket connection (heartbeats) to keep the connection stable.
            If for some reason all of the websockets related to coinbase or derebit cloase, the heartbeat 
            connection of the exchange should close too. (In order to not keep any unnecessary websockt connections)
            
            This method will return a list of related websockets to heartbeats.
            In coinbase and derebit, for every ticker (say BTC-USD) and all of the channels related to this ticker (like books, trades ...) there must be a single heaertbeat (BTC-USD)
        """
        ids = [x.get("id_ws") for x in self.connection_data]        
        self.ws_related_to_heartbeat_channel = { x : [] for x in ids if "heartbeat" in x}
        for data in self.connection_data:
            symbol = data.get("symbol").lower()
            symbol = ''.join(char for char in symbol if char in string.ascii_letters or char in string.digits)
            id_ws = data.get("id_Ws")
            for heartbeat in self.ws_related_to_heartbeat_channel.keys():
                if symbol in heartbeat:
                    self.ws_related_to_heartbeat_channel[heartbeat].append(id_ws)
                    
    def _get_related_ws(self, connection_data):
        exchnage = connection_data.get("exchange").lower()
        s = connection_data.get("instruments")
        symbol = s.lower() if isinstance(s, str) else s[0].lower()
        symbol = ''.join(char for char in symbol if char in string.ascii_letters or char in string.digits)
        key = ""
        for heartbeats_key in self.ws_related_to_heartbeat_channel.keys():
            if symbol in heartbeats_key:
                if exchnage in heartbeats_key:
                    key = heartbeats_key
                    break
        return self.ws_related_to_heartbeat_channel.get(key), key
             
    async def __wsaenter__(self, connection_data):
        """ initiates websocket gracefully"""
        url = connection_data.get("url")
        id_ws = connection_data.get('id_ws')
        self.websockets[id_ws] = await websockets.connect(url, ssl=self.ssl_context, max_size=self.wsmessage_max_size)
        return self.websockets[id_ws]
    
    async def __wsaexit__(self, websocket, connection_data):
        """ exits from websocket gracefully """
        exchange = connection_data.get("exchange")
        id_ws = connection_data.get("id_ws")
        payload = self.ws_messages.get(id_ws)
        if exchange == "coinabse":
            payload["type"] = "unsubscribe"
        if exchange == "deribit":
            if "heartbeat" in id_ws:
                payload["method"] = '/public/disable_heartbeat'
            if "heartbeat" not in id_ws:
                payload["method"] = '/public/unsubscribe'
        try:
            await websocket.send(json.dumps(payload))  
            await websocket.wait_closed() 
        except WebSocketException as e:
            self.logger.error("Could shut down gracefuly the websocket %s, %s", id_ws, e, exc_info=True)  
        
    async def heartbeats_listener(self):
        """ Ensures that heartbeats of conibase of derebit are running """
        for heartbeat_id, ws_ids in self.ws_related_to_heartbeat_channel.items():
            is_heartbeat_on =  self.websockets.get(heartbeat_id).open
            for ws_id in ws_ids:
                is_ws_on =  self.websockets.get(ws_id).open
                if is_heartbeat_on is False and is_ws_on is True:
                    connection_data = [x for x in self.connection_data if x.get("id_ws") == ws_id][0]
                    method = self.coinbase_ws if "coinbase" in ws_id else self.deribit_ws
                    asyncio.create_task(method(connection_data))
                    break
        
    def on_backoff(self, details):
        """ helper to count reconenct attempts """
        id_ = details['args'][0].get('id_ws') if "id_ws" in details['args'][0] else details['args'][0].get('id_api')
        if "RECONNECT_ATTEMPTS" in self.producer_metrics:
            self.RECONNECT_ATTEMPTS.labels(websocket_id=id_).inc()
        self.logger.info("Reconnecting to WebSocket ID %s. Attempt %s", id_, {details['tries']})

    def process_disconnects_metrics(self, id_ws, connection_start_time):
        """ pattern of processing disconnects"""
        if "ERRORS_DISCONNECTS" in self.producer_metrics:
            self.ERRORS_DISCONNECTS.labels(websocket_id=id_ws).inc()
        if "TOTAL_MESSAGES" in self.producer_metrics:
            self.TOTAL_MESSAGES.labels(websocket_id=id_ws).set(0)
        if "CONNECTION_DURATION" in self.producer_metrics:
            duration = time.time() - connection_start_time
            self.CONNECTION_DURATION.labels(websocket_id=id_ws).set(duration)      
                        
    def process_ws_metrics(self, id_ws, message, latency_start_time):
        """ processes 3 metrics """
        if "MESSAGE_SIZE" in self.producer_metrics:
            message_size = len(message.encode('utf-8'))   
            self.MESSAGE_SIZE.labels(websocket_id=id_ws).observe(message_size)
        if "NETWORK_LATENCY" in self.producer_metrics:   
            latency_end_time = time.time()
            latency = latency_end_time - latency_start_time
            self.NETWORK_LATENCY.labels(websocket_id=id_ws).set(latency)
        if "TOTAL_MESSAGES" in self.producer_metrics:   
            self.TOTAL_MESSAGES.labels(websocket_id=id_ws).set(0)

    async def ws_ping_process(self, websocket, message, id_ws):
        """ for websockets if you need to send ping """
        if "ping" in message:
            print("Ping recieved %s", id_ws)
            self.last_ping_pong_times[id_ws] = time.time()
            await websocket.pong()
            print("Pong send to %s", id_ws)
            self.KEEP_ALIVE_COUNTS.labels(websocket_id=id_ws).inc()
            
    async def ws_pong_process(self, message, id_ws):
        """ pong patter of websockets"""
        if "pong" in message:
            self.last_ping_pong_times[id_ws] = time.time()
            self.KEEP_ALIVE_COUNTS.labels(websocket_id=id_ws).inc()
    
    def ws_process_logger(self, id_ws, time_interval, word="Ping"):
        """ logger pattern """
        if time.time() - self.last_ping_pong_times.get(id_ws, time.time()) > time_interval:
            self.logger.error("%s interval timeout exceeded for WebSocket ID %s", word,  id_ws, exc_info=True)
            raise TimeoutError(f"{word} interval timeout exceeded for WebSocket ID {id_ws}")

    @DecoratorsPatters.websocket_wrapper(keepalattr=None)
    async def binance_ws(self, *args, **kwargs):
        """ wrapper function for binance ws websocket """
        connection_data = kwargs.get("connection_data")
        websocket = kwargs.get("websocket")
        id_ws = connection_data.get('id_ws')
        latency_start_time = time.time()
        message = await websocket.recv()
        self.process_ws_metrics(id_ws, message, latency_start_time)
        await self.ws_ping_process(websocket, message, id_ws)
        await self.send_message_to_topic(connection_data.get("topic_name"), message)
        self.ws_process_logger(id_ws, self.binance_timeout_interval)
    
    @DecoratorsPatters.websocket_wrapper(keepalattr="bybit_keepalive")
    async def bybit_ws(self, *args, **kwargs):
        """ wrapper function for bybit ws websocket """
        connection_data = kwargs.get("connection_data")
        websocket = kwargs.get("websocket")
        id_ws = connection_data.get('id_ws')
        latency_start_time = time.time()
        message = await websocket.recv()
        self.process_ws_metrics(id_ws, message, latency_start_time)
        await self.ws_pong_process(message, id_ws)
        await self.send_message_to_topic(connection_data.get("topic_name"), message)
        self.ws_process_logger(id_ws, self.bybit_timeout_interval, "Pong")
    
    @DecoratorsPatters.websocket_wrapper(keepalattr="okx_keepalive")                       
    async def okx_ws(self, *args, **kwargs):
        """ wrapper function for okx ws websocket """
        connection_data = kwargs.get("connection_data")
        websocket = kwargs.get("websocket")
        id_ws = connection_data.get('id_ws')
        latency_start_time = time.time()
        message = await websocket.recv()
        self.process_ws_metrics(id_ws, message, latency_start_time)
        await self.ws_ping_process(websocket, message, id_ws)
        await self.send_message_to_topic(connection_data.get("topic_name"), message)
        self.ws_process_logger(id_ws, self.okx_timeout_interval, "Pong")
    
    @DecoratorsPatters.websocket_wrapper(keepalattr=None)
    async def deribit_ws(self, *args, **kwargs):
        """ wrapper function for deribit ws websocket """
        connection_data = kwargs.get("connection_data")
        websocket = kwargs.get("websocket")
        latency_start_time = time.time()
        id_ws = connection_data.get("id_ws")
        message = await websocket.recv()
        await self.send_message_to_topic(connection_data.get("topic_name"), message)
        self.process_ws_metrics(id_ws, message, latency_start_time)

    @DecoratorsPatters.websocket_wrapper(keepalattr=None)
    async def deribit_heartbeats(self, *args, **kwargs):
        """ wrapper function for deribit heartbeat ws websocket """
        connection_data = kwargs.get("connection_data")
        websocket = kwargs.get("websocket")
        latency_start_time = time.time()
        id_ws = connection_data.get("id_ws")
        message = await websocket.recv()
        message = json.loads(message)
        self.process_ws_metrics(id_ws, json.dumps(message), latency_start_time)
        if message.get("result") == "ok":
            self.heartbeats_ids[id_ws] = message["id"]
        if message.get("params", {}).get("type") == "test_request":
            test_response = {
                "jsonrpc": "2.0",
                "id": self.heartbeats_ids[id_ws],
                "method": "public/test",
                "params": {}
            }
            await websocket.send(json.dumps(test_response))
        interval = connection_data.get("msg", {}).get("params", {}).get("interval", 5)
        self.ws_process_logger(id_ws, interval, "Heartbeat")

    @DecoratorsPatters.websocket_wrapper(keepalattr="bitget_keepalive")
    async def bitget_ws(self, *args, **kwargs):
        """ wrapper function for bitget ws websocket """
        connection_data = kwargs.get("connection_data")
        websocket = kwargs.get("websocket")
        latency_start_time = time.time()
        id_ws = connection_data.get("id_ws")
        message = await websocket.recv()
        self.process_ws_metrics(id_ws, message, latency_start_time)
        await self.ws_pong_process(message, id_ws)
        await self.send_message_to_topic(connection_data.get("topic_name"), message)
        self.ws_process_logger(id_ws, self.bitget_timeout_interval, "Pong")

    @DecoratorsPatters.websocket_wrapper(keepalattr="kucoin_keepalive")
    async def kucoin_ws(self, *args, **kwargs):
        """ wrapper function for kucoin ws websocket """
        connection_data = kwargs.get("connection_data")
        websocket = kwargs.get("websocket")
        latency_start_time = time.time()
        id_ws = connection_data.get("id_ws")
        message = await websocket.recv()
        self.process_ws_metrics(id_ws, message, latency_start_time)
        await self.ws_pong_process(message, id_ws)
        await self.send_message_to_topic(connection_data.get("topic_name"), message)
        interval = self.kucoin_pp_intervals.get(id_ws).get("pingTimeout", 10000)
        self.ws_process_logger(id_ws, interval, "Pong")
    
    @DecoratorsPatters.websocket_wrapper(keepalattr="bingx_keepalive")
    async def bingx_ws(self, *args, **kwargs):
        """ wrapper function for bingx ws websocket """
        connection_data = kwargs.get("connection_data")
        websocket = kwargs.get("websocket")
        latency_start_time = time.time()
        id_ws = connection_data.get("id_ws")
        instType = connection_data.get("instType")
        message = await websocket.recv()
        message = gzip.GzipFile(fileobj=io.BytesIO(message), mode='rb').read().decode('utf-8')
        self.process_ws_metrics(id_ws, message, latency_start_time)
        if "ping" in message:
            if instType == "spot":
                message = json.loads(message)
                await websocket.send(json.dumps({"pong" : message.get("ping"), "time" : message.get("time")}))
                self.last_ping_pong_times[id_ws] = time.time()
                self.KEEP_ALIVE_COUNTS.labels(websocket_id=id_ws).inc()
            if instType == "perpetual":
                await websocket.pong()
                self.last_ping_pong_times[id_ws] = time.time()
                self.KEEP_ALIVE_COUNTS.labels(websocket_id=id_ws).inc()
        await self.send_message_to_topic(connection_data.get("topic_name"), message)
        self.ws_process_logger(id_ws, self.bingx_timeout_interval, "Ping")

    @DecoratorsPatters.websocket_wrapper(keepalattr="mexc_keepalive")
    async def mexc_ws(self, *args, **kwargs):
        """ wrapper function for mexc ws websocket """
        connection_data = kwargs.get("connection_data")
        websocket = kwargs.get("websocket")
        latency_start_time = time.time()
        id_ws = connection_data.get("id_ws")
        message = await websocket.recv()
        self.process_ws_metrics(id_ws, message, latency_start_time)
        if "PONG" in message or "pong" in message:
            self.last_ping_pong_times[id_ws] = time.time()
            self.KEEP_ALIVE_COUNTS.labels(websocket_id=id_ws).inc()
        await self.send_message_to_topic(connection_data.get("topic_name"), message)
        self.ws_process_logger(id_ws, self.mexc_timeout_interval, "Pong")

    @DecoratorsPatters.websocket_wrapper(keepalattr="gateio_keepalive")
    async def gateio_ws(self, *args, **kwargs):
        """ wrapper function for gateio ws websocket """
        connection_data = kwargs.get("connection_data")
        websocket = kwargs.get("websocket")
        latency_start_time = time.time()
        id_ws = connection_data.get("id_ws")
        message = await websocket.recv()
        self.process_ws_metrics(id_ws, message, latency_start_time)
        await self.ws_pong_process(message, id_ws)
        await self.send_message_to_topic(connection_data.get("topic_name"), message)
        self.ws_process_logger(id_ws, self.mexc_timeout_interval, "Ping")
    
    @DecoratorsPatters.websocket_wrapper(keepalattr="htx_keepalive")
    async def htx_ws(self, *args, **kwargs):
        """ wrapper function for htx ws websocket """
        connection_data = kwargs.get("connection_data")
        websocket = kwargs.get("websocket")
        latency_start_time = time.time()
        id_ws = connection_data.get("id_ws")
        message = await websocket.recv()
        self.process_ws_metrics(id_ws, message, latency_start_time)
        await self.ws_pong_process(message, id_ws)
        await self.send_message_to_topic(connection_data.get("topic_name"), message)
        self.ws_process_logger(id_ws, self.htx_timeout_interval, "Pong")
    
    @DecoratorsPatters.websocket_wrapper(keepalattr=None)
    async def coinbase_ws(self, *args, **kwargs):
        """ wrapper function for coinbase ws websocket """
        connection_data = kwargs.get("connection_data")
        websocket = kwargs.get("websocket")
        latency_start_time = time.time()
        id_ws = connection_data.get("id_ws")
        message = await websocket.recv()
        self.process_ws_metrics(id_ws, message, latency_start_time)
        size_in_bytes = sys.getsizeof(message)
        #print(size_in_bytes)
        await self.send_message_to_topic(connection_data.get("topic_name"), message)


    @DecoratorsPatters.websocket_wrapper(keepalattr=None)
    async def coinbase_heartbeats(self, *args, **kwargs):
        """ coinbase heartbeats"""
        connection_data = kwargs.get("connection_data")
        websocket = kwargs.get("websocket")
        latency_start_time = time.time()
        id_ws = connection_data.get("id_ws")
        message = await websocket.recv()
        pass
    
    # aiohttp caroutine related
    

    async def aiohttp_socket(self, connection_data, initial_delay):
        """Initiates aiohttp pipe"""
        
        id_api = connection_data.get("id_api")
        connection_start_time = time.time()
        await asyncio.sleep(initial_delay)
        topic = connection_data.get("topic_name")
        
        async def inner_aiohttp_socket():
            try:
                while True:
                    latency_start_time = time.time()
                    message = await connection_data.get("aiohttpMethod")()
                    self.process_ws_metrics(id_api, message, latency_start_time)
                    await self.send_message_to_topic(topic, message)
                    # message_encoded = message.encode("utf-8")
                    # print(sys.getsizeof(message_encoded))
                    await asyncio.sleep(connection_data.get("pullTimeout"))
            except aiohttp_recoverable_errors as e:
                self.logger.error("Error from %s: %s", connection_data.get('id_api'), e, exc_info=True)
                if "CONNECTION_DURATION" in self.producer_metrics:
                    duration = time.time() - connection_start_time
                    self.CONNECTION_DURATION.labels(websocket_id=id_api).set(duration)
                if "ERRORS_DISCONNECTS" in self.producer_metrics:
                    self.ERRORS_DISCONNECTS.labels(websocket_id=id_api).inc()
                raise
            except Exception as e:
                self.logger.error("Error from %s: %s. The coroutine was completely closed or broken", connection_data.get('id_api'), e, exc_info=True)
                if "ERRORS_DISCONNECTS" in self.producer_metrics:
                    self.ERRORS_DISCONNECTS.labels(websocket_id=id_api).inc()
        return await backoff.on_exception(
            backoff.expo,
            aiohttp_recoverable_errors,
            max_tries=10,
            max_time=300,
            on_backoff=self.on_backoff
        )(inner_aiohttp_socket)()

    # Kafka server related    

    @DecoratorsPatters.handle_kafka_errors_backup
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
                self.logger.error("Reconnection failed: %s", str(e))
        self.logger.critical("Unable to reconnect to the broker after several attempts.")
        await self.producer.stop() 
        self.producer_running = False
        return False

    def ensure_topic_exists(self):
        """
            Ensures that topics exist with necessary configurations
        """
        try:
            fs = self.admin.create_topics(self.kafka_topics)
            for topic, f in fs.items():
                try:
                    f.result()  
                    print(f"Topic {topic} created")
                except KafkaException  as e:
                    self.logger.info("Topic already exists, skipping to the next iteration... %s", e)
        except KafkaException as e:
            self.logger.info("Topic already exists, skipping to the next iteration... %s", e)

            
    async def send_message_to_topic(self, topic_name, message):
        """
            Ensures messages are send while dealing with errors
        """
        try:
            await self.producer.send_and_wait(topic_name, message.encode("utf-8"))
        except kafka_message_errors as e:
            self.logger.error("kafka_send_errors raised, Sending messages to topic %s is impossible due to: %s", topic_name,  e, exc_info=True)
            await self.producer.flush()
    
    def describe_topics(self):
        """
            https://github.com/confluentinc/confluent-kafka-python/blob/master/src/confluent_kafka/admin/_topic.py
        """
        try:
            topics = self.admin.describe_topics(TopicCollection(self.kafka_topics_names))
            return list(topics.keys())
        except KafkaException as e:
            self.logger.info("Topic already exists, skipping to the next iteration... %s", e)


    def delete_all_topics(self):
        """ deletes topics """
        try:
            topics = self.describe_topics()
            self.admin.delete_topics(topics)
            print(f"{topics} were deleted")
        except KafkaException as e:
            self.logger.info("Exception raised while creating topics %s", e)
            
    # run producer
    
    def populate_apimixers(self):
        """ pass some crucial variables to apimixers"""
        for connection_dict in self.connection_data:
            if "id_ws" not in connection_dict and "id_api" in connection_dict:
                if connection_dict.get("coroutine_manager") is True:
                    connection_dict["api_call_manager"].pullTimeout = connection_dict.get("pullTimeout")
                    connection_dict["api_call_manager"].send_message_to_topic = self.send_message_to_topic
                    connection_dict["api_call_manager"].topic_name = connection_dict.get("topic_name")
                    connection_dict["api_call_manager"].connection_data = connection_dict
                    connection_dict["api_call_manager"].logger = self.logger
                    connection_dict["api_call_manager"].on_backoff = self.on_backoff
                    connection_dict["api_call_manager"].CONNECTION_DURATION = self.CONNECTION_DURATION
                    connection_dict["api_call_manager"].ERRORS_DISCONNECTS = self.ERRORS_DISCONNECTS
                    connection_dict["api_call_manager"].producer_metrics = self.producer_metrics
                    connection_dict["api_call_manager"].RECONNECT_ATTEMPTS = self.RECONNECT_ATTEMPTS
                    connection_dict["api_call_manager"].max_reconnect_retries = self.max_reconnect_retries

    async def run_producer(self, is_reconnect=False):
        """
            Runs roducer
        """
        # self.delete_all_topics()
        if is_reconnect is False:
            self.ensure_topic_exists()    
            self.producer = AIOKafkaProducer(bootstrap_servers=self.kafka_host, loop=self.loop)
        await self.start_producer()
        
        tasks = []
        
        tasks.append(asyncio.ensure_future(self.CPU_MEMORY_diskIO_networkIO_update()))
        tasks.append(asyncio.ensure_future(self.heartbeats_listener()))
        
        
        self.populate_apimixers()
                
        for delay, connection_dict in enumerate(self.connection_data):
                        
            # websocket caroutines
            if "id_ws" in connection_dict:
                connection_message = connection_dict.get("msg_method")()
                exchange = connection_dict.get("exchange")
                if connection_message.get("channel") == "heartbeats":
                    ws_method = getattr(self, f"{exchange}_heartbeats", None)
                elif connection_message.get("method") == '/public/set_heartbeat':
                    ws_method = getattr(self, f"{exchange}_heartbeats", None)
                else:
                    ws_method = getattr(self, f"{exchange}_ws", None)
                tasks.append(asyncio.ensure_future(ws_method(connection_dict)))
                    
            if "id_api" in connection_dict:
                if connection_dict.get("coroutine_manager") is True:
                    tasks.append(asyncio.ensure_future(connection_dict.get("api_call_manager").start_coroutines_orchestrator(lag=delay)))
                else:
                    tasks.append(asyncio.ensure_future(self.aiohttp_socket(connection_data=connection_dict, initial_delay=delay)))
            
            
        await asyncio.gather(*tasks)
            
            
