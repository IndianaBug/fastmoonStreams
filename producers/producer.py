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

# https://prometheus.github.io/client_python/exporting/http/wsgi/
from prometheus_client import start_http_server, Counter, Summary

def should_give_up(exc):
    return isinstance(exc, kafka_giveup_errors)



class keepalive():
    """
        docs references:
            binance: https://binance-docs.github.io/apidocs/spot/en/#websocket-market-streams
            bybit: https://bybit-exchange.github.io/docs/v5/ws/connect
            bingx: https://bingx-api.github.io/docs/#/en-us/swapV2/socket/
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
    # Errors metricks
    KEEP_ALIVE_ERRORS = Counter('keep_alive_errors', 'Count of errors in keep alive', ['error_type', 'websocket_id', 'exchange'])
    KEEP_ALIVE_DISCONNECTS = Counter('keep_alive_disconnects', 'Count of disconnects in keep alive', ['websocket_id', 'exchnage'])
    KEEP_ALIVE_COUNTS = Count('keep_alive_counts', 'Counts timmes ping/pong interactions', ['websocket_id'])
    # reconnect retries
    max_reconnect_retries = 8

    def keep_alive(self, running_attr_name:str):
        """ Pattern of keep alive for every exchange"""
        def decorator(func):
            @wraps(func)
            @backoff.on_exception(backoff.expo,
                                    websockets_errors,
                                    max_tries=self.max_reconnect_retries)
            async def wrapper(self, websocket, connection_data, logger, *args, **kwargs):
                id_ws = connection_data.get("id_ws", "unknown")
                while getattr(self, running_attr_name):
                    try:
                        await func(self, websocket, *args, **kwargs)
                    except aiohttp_recoverable_errors as e:
                        logger.exception("Keep-Alive error, connection closed: %s, ID_WS: %s", e, id_ws, exc_info=True)
                        KEEP_ALIVE_ERRORS.labels(error_type='recoverable_error', exchnage=connection_data.get("exchnage"), websocket_id=id_ws).inc()
                        raise
                    except Exception as e:
                        logger.exception("Keep-Alive error, connection closed: %s, ID_WS: %s", e, id_ws, exc_info=True)
                        KEEP_ALIVE_DISCONNECTS.labels(websocket_id=id_ws, exchnage=connection_data.get("exchnage")).inc()
                        break
            return wrapper
        return decorator

    @keep_alive("binance_keepalive_running")
    async def binance_keepalive(self, websocket, connection_data, logger):
        """ initialize binance keep alive caroutine"""
        await websocket.pong(b"") 
        await asyncio.sleep(self.binance_pp_interval) 
            
    async def stop_binance_keepalive(self):
        """ stop keep alive """
        self.binance_keepalive_running = False

    @keep_alive("bybit_keepalive_running")
    async def bybit_keepalive(self, websocket, connection_data):
        """ initialize bybit keep alive caroutine"""
        req_id = connection_data.get("req_id")
        await websocket.ping(json.dumps({"req_id": req_id, "op": "ping"})) 
        await asyncio.sleep(self.bybit_pp_interval) 
            
    async def stop_bybit_keepalive(self):
        """ stop keep alive """
        self.bybit_keepalive_running = False

    @keep_alive("okx_keepalive_running")
    async def okx_keepalive(self, websocket, connection_data):
        """ initialize okx keep alive caroutine"""
        await websocket.ping("ping") 
        await asyncio.sleep(ping_interval) 
            
    async def stop_okx_keepalive(self):
        """ stop keep alive """
        self.okx_keepalive_running = False
        
    @keep_alive("bitget_keepalive_running")
    async def bitget_keepalive(self, websocket, connection_data):
        """ initialize bitget keep alive caroutine"""
        await websocket.ping("ping") 
        await asyncio.sleep(ping_interval) 
            
    async def stop_bitget_keepalive(self):
        """ stop keep alive """
        self.bitget_keepalive_running = False
        
    @keep_alive("bingx_keepalive_running")
    async def bingx_keepalive(self, websocket, connection_data):
        """ initialize bingx keep alive caroutine (ONLY FOR PERPETUAL WEBSOCKETS)"""
        await websocket.send("Pong") 
        await asyncio.sleep(ping_interval) 
            
    async def stop_bingx_keepalive(self):
        """ stop keep alive """
        self.bingx_keepalive_running = False
        
    @keep_alive("kucoin_keepalive_running")
    async def kucoin_keepalive(self, websocket, connection_data):
        """ initialize kucoin keep alive caroutine"""
        await websocket.send({"id": str(connection_data.get("connection_id")), "type": "ping"})
        await asyncio.sleep(ping_interval) 
            
    async def stop_kucoin_keepalive(self):
        """ stop keep alive """
        self.kucoin_keepalive_running = False
        
    @keep_alive("mexc_keepalive_running")
    async def mexc_keepalive(self, websocket, connection_data):
        """ initialize mexc keep alive caroutine"""
        if connection_data.get("instType") == "spot":
            await websocket.send("PING") 
        else:
            await websocket.send("ping") 
        await asyncio.sleep(ping_interval) 
            
    async def stop_mexc_keepalive(self):
        """ stop keep alive """
        self.mexc_keepalive_running = False
        
    @keep_alive("gateio_keepalive_running")
    async def gateio_keepalive(self, websocket, connection_data):
        """ initialize gateio keep alive caroutine"""
        if connection_data.get("instType") == "spot":
            await websocket.send({"channel" : "spot.ping"}) 
        if connection_data.get("instType") in ["future", "perpetual"]:
            await websocket.send({"channel" : "futures.ping"}) 
        if connection_data.get("instType") == "option":
            await websocket.send({"channel" : "options.ping"}) 
        await asyncio.sleep(ping_interval) 
            
    async def stop_gateio_keepalive(self):
        """ stop keep alive """
        self.gateio_keepalive_running = False

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
        self.last_pong_times = {}
        
        self.ws_connections_active = Gauge('websocket_connections_active', 'Number of active WebSocket connections')
        self.api_connections_active = Gauge('API Asyncio pipes active', 'Number of active API Asyncio pipes active')
        self.connection_errors = Counter('app_connection_errors_total', 'Total number of connection errors')
        
        self.connection_duration = Histogram('app_connection_duration_seconds', 'Time connected before disconnect', buckets=(1, 5, 10, 30, 60, 300, 600))
        self.message_throughput = Counter('app_messages_total', 'Total messages sent and received')
        self.data_volume = Counter('app_data_volume_bytes', 'Total data transmitted in bytes')
        self.reconnection_attempts = Counter('app_reconnection_attempts_total', 'Total reconnection attempts')
        self.ping_pong_duration = Histogram('app_ping_pong_duration_seconds', 'Round-trip time for ping-pong messages', buckets=(0.01, 0.05, 0.1, 0.5, 1, 5))

    #  Producer setup

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

    # Websocket related
    
    async def check_pong_timeout(self, websocket, connection_data):
        while True:
            await asyncio.sleep(N) 
            if time.time() - self.last_pong_time > N:
                self.logger.error(f"No 'pong' received in the last {N} seconds for websocket ID {connection_data.get('id_ws')}")
                # raise a reconnectable exception
                


    def websocket_wrapper(self, keep_alive_caroutine_attr=None, stop_keep_alive_caroutine_attr=None):
        """Pattern for every websocket"""
        def decorator(func):
            @wraps(func)
            @backoff.on_exception(backoff.expo,
                                  websockets_errors,
                                  max_tries=self.max_reconnect_retries)
            async def wrapper(connection_data, topic):
                try:
                    url = connection_data.get("url")
                    connection_message = json.dumps(connection_data.get("msg_method")())
                    async with websocket in websockets.connect(url, timeout=86400, ssl=ssl_context, max_size=1024 * 1024 * 10):
                        await websocket.send(connection_message)
                        if keep_alive_caroutine_attr != None:
                            keep_alive_method = getattr(self, keep_alive_caroutine_attr)
                            keep_alive_task = asyncio.create_task(keep_alive_method(websocket, connection_data, self.logger))
                        while websocket.open:
                            try:
                                await func(self, connection_data, topic, websocket=websocket,)
                            except websockets_errors as e:  
                                self.logger.exception(f"WebSocket error for {connection_data.get('id_ws')}, {e}", exc_info=True)
                                break
                except asyncio.TimeoutError as e:
                    self.logger.exception(f"WebSocket connection timed out for {connection_data.get('id_ws')}, {e}", exc_info=True)
                except Exception as e:
                    self.logger.exception(f"Failed to establish WebSocket connection for {connection_data.get('id_ws')}, {e}", exc_info=True)
                finally:
                    if stop_keep_alive_caroutine_attr != None:
                        keep_alive_method = getattr(self, keep_alive_caroutine_attr)
                        if keep_alive_method:
                            stop_keep_alive_method = getattr(self, stop_keep_alive_caroutine_attr)
                            await stop_keep_alive_caroutine_attr()
                    self.logger.info(f"WebSocket connection for {connection_data.get('id_ws')} has ended.")
                    await websocket.close()

    @websocket_wrapper("binance_keepalive", "stop_binance_keepalive")
    async def binance_ws(self, connection_data, topic, websocket):
        message = await websocket.recv()
        if "ping" in message:
            await websocket.pong(message)
            self.KEEP_ALIVE_COUNTS.labels(websocket_id=connection_data.get('id_ws')).inc()
        await self.send_message_to_topic(topic, message)

    @websocket_wrapper("bybit_keepalive", "stop_bybit_keepalive")
    async def bybit_ws(self, websocket, connection_data, topic):
        message = await websocket.recv()
        if "ping" in message:
            self.KEEP_ALIVE_COUNTS.labels(websocket_id=connection_data.get('id_ws')).inc()
        await self.send_message_to_topic(topic, message)
                                       
    @websocket_wrapper("okx_keepalive", "stop_okx_keepalive")
    async def okx_ws(self, websocket, connection_data, topic):
        message = await websocket.recv()
        if "pong" in message:
            self.KEEP_ALIVE_COUNTS.labels(websocket_id=connection_data.get('id_ws')).inc()
        await self.send_message_to_topic(topic, message)
        
    @websocket_wrapper(None, None)
    async def deribit_ws(self, websocket, connection_data, topic):
        message = await websocket.recv()
        await self.send_message_to_topic(topic, message)

    @websocket_wrapper(None, None)
    async def deribit_heartbeat(self, websocket, connection_data, topic):
        message = await websocket.recv()
        message = json.loads(message)
        if message.get("method") == "heartbeat":
            print(f"Received heartbeat from Deribit server.")
        elif message.get("result") == "ok":
            test_response = {
                "jsonrpc": "2.0",
                "id": message["id"],
                "result": {
                    "method": "public/test"   
                }
            }
            await websocket.send(json.dumps(test_response))

    @websocket_wrapper("bitget_keepalive", "stop_bitget_keepalive")
    async def bitget_ws(self, websocket, connection_data, topic):
        message = await websocket.recv()
        if message == b'\x89\x00':
            print(f"Received ping from {connection_data.get('id_ws')}. Sending pong...")
        await self.send_message_to_topic(topic, message)

    @websocket_wrapper("kucoin_keepalive", "stop_kucoin_keepalive")
    async def kucoin_ws(self, websocket, connection_data, topic):
        message = await websocket.recv()
        if "ping" in message:
            connect_id = connection_data.get("connect_id")
            await websocket.send({"id": str(connect_id), "type": "pong"})
        await self.send_message_to_topic(topic, message)

    @websocket_wrapper("bingx_keepalive", "stop_bingx_keepalive")
    async def bingx_ws(self, websocket, connection_data, topic):
        message = await websocket.recv()
        message = gzip.GzipFile(fileobj=io.BytesIO(message), mode='rb').read().decode('utf-8')
        if "ping" in message:
            message = json.loads(message)
            await websocket.send(json.dumps({"pong" : message.get("ping"), "time" : message.get("time")}))
        await self.send_message_to_topic(topic, message)

    @websocket_wrapper("mexc_keepalive", "stop_mexc_keepalive")
    async def mexc_ws(self, websocket, connection_data, topic):
        message = await websocket.recv()
        if "pong" in message:
            await websocket.send("ping")
        if "PONG" in message:
            await websocket.send("PING")
        await self.send_message_to_topic(topic, message)

    @websocket_wrapper("gateio_keepalive", "stop_gateio_keepalive")
    async def gateio_ws(self, websocket, connection_data, topic):
        message = await websocket.recv()
        if "ping" in message:
            await websocket.send({"channel" : json.loads(message).get("channel").repalce("ping", "pong")})
        if "pong" in message:
            await websocket.send({"channel" : json.loads(message).get("channel").repalce("pong", "ping")})
        await self.send_message_to_topic(topic, message)
    
    @websocket_wrapper(None, None)
    async def htx_ws(self, websocket, connection_data, topic):
        message = await websocket.recv()
        message =  gzip.decompress(message).decode('utf-8')
        if "ping" in message:
            await websocket.send(json.dumps({"pong": json.loads(message).get("ping")}))
        await self.send_message_to_topic(topic, message)

    @websocket_wrapper(None, None)
    async def coinbase_ws(self, websocket, connection_data, topic):
        message = await websocket.recv()
        await self.send_message_to_topic(topic, message)

    @websocket_wrapper(None, None)
    async def coinbase_heartbeats(self, websocket, connection_data, topic):
        pass
    
    # aiohttp caroutine related
    
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
            self.logger.exception("Error from %s: %s", connection_data.get('id_api'), e, exc_info=True)
            raise  
        except Exception as e:
            logger.exception("Error from %s: %s . The caroutine was completely closed or broken", connection_data.get('id_api'), e, exc_info=True)
            break

    # Kafka server related    

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
    async def send_message_to_topic(self, topic_name, message):
        """
            Ensures messages are send while dealing with errors
        """
        await self.producer.send_and_wait(topic_name, message.encode("utf-8"))
    
            
    def describe_topics(self):
        """
            https://github.com/confluentinc/confluent-kafka-python/blob/master/src/confluent_kafka/admin/_topic.py
        """
        topics = self.admin.describe_topics(TopicCollection(self.kafka_topics_names))
        return list(topics.keys())

    def delete_all_topics(self):
        """ deletes topics """
        try:
            topics = self.describe_topics()
            self.admin.delete_topics(topics)
            print(f"{topics} were deleted")
        except Exception as e:
            print(f"An error occurred: {e}")
            
    # run producer

    @handle_kafka_errors_backup
    async def run_producer(self, is_reconnect=False):
        """
            Runs roducer
        """
        try:
            # start producer
            if is_reconnect is False:
                self.ensure_topic_exists()    
                self.producer = AIOKafkaProducer(bootstrap_servers=self.kafka_host, loop=self.loop)
            await self.start_producer()
            
            tasks = []
            
            for delay, connection_dict in enumerate(self.connection_data):
                
                # websocket caroutines
                if "id_ws" in connection_dict:
                    connection_message = json.dumps(connection_data.get("msg_method")())
                    exchange = connection_dict.get("exchange")
                    if connection_message.get("channel") != "heartbeats":                                      
                        ws_method = getattr(self, f"{exchange}_ws", None)
                    if connection_message.get("channel") == "heartbeats":
                        ws_method = getattr(self, f"{exchange}_heartbeats", None)
                    tasks.append(asyncio.ensure_future(ws_method(connection_dict)))
                        
                    
                if "id_ws" not in connection_dict and "id_api" in connection_dict:
                    
                    # special dynamic aiohttp caroutines 
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
                        
                    # regular aiohttp caroutines 
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
