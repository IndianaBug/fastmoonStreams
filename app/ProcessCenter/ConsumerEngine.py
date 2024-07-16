from pathlib import Path
from functools import partial
import asyncio
from typing import AsyncIterator
import logging
from logging.handlers import RotatingFileHandler
import faust
from .db_connectors import PostgresConnector, MockdbConnector

async def ws_fetcher_helper(function):
    data = await function()
    return data

backoff_retries = 8

base_path = Path(__file__).parent.parent

class StreamApp(faust.App):
    
    def __init__(self, 
                 connection_data,
                 coin="XBT", 
                 app_name="XBTStreams",
                 app_id=None,   # if you are planning to split between many servers
                 clickhouse_host=None,
                 clickhouse_port=None,
                 clickhouse_username=None, 
                 clickhouse_password=None,
                 clickhouse_dbname="XBTMarketData",
                 postgres_host=None,
                 postgres_port=None,
                 postgres_username=None, 
                 postgres_password=None,
                 postgres_dbname="XBTStreamsMetrics",
                 log_file_bytes=10*1024*1024,
                 log_file_backup_count=5,
                 max_reconnect_retries_backoff=8,
                 mode = "testing",
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        # faust configs
        self.coin=coin
        self.app_name = app_name
        self.app_id = app_id
        self.broker = kwargs.get("broker")
        self.topic_partitions = kwargs.get("topic_partitions")
        self.value_serializer = kwargs.get("value_serializer")
        self.max_reconnect_retries_backoff = max_reconnect_retries_backoff
        self.logger = self.setup_logger(base_path, log_file_bytes, log_file_backup_count)
        self.connection_data = connection_data
        self.mode = mode

        self.market_state = {} # lates data dictionary, everyhting except trades and depth
        
        #database related
        self.sqldb = None
        self.nosqldb = None
        self.mochnosql = None
        self.clickhouse_host=clickhouse_host,
        self.clickhouse_port=clickhouse_port,
        self.clickhouse_username=clickhouse_username, 
        self.clickhouse_password=clickhouse_password,
        self.clickhouse_dbname=clickhouse_dbname,
        self.postgres_host=postgres_host,
        self.postgres_port=postgres_port,
        self.postgres_username=postgres_username, 
        self.postgres_password=postgres_password,
        self.postgres_dbname=postgres_dbname,
        
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.async_init())
        self.deribit_depths = self.fetch_initial_deribit_depth()


    async def async_init(self):
        await self.setup_databases()
            
    async def couchdb_refresh_credentials(self):
        """refreshes credentials"""
        pass
    
    async def couchdb_merge_conflicts(self):
        """ ConflictError"""
        pass

    async def couchdb_fix_request_header(self):
        """ changes header parameter"""
        pass

    async def faust_error_on_message(self):
        """ changes header parameter"""
        pass
    
    async def close(self):
        """ safe close of faust app and databases """
        await self.sqldb.close()

    def fetch_initial_deribit_depth(self):
        deribit_depths = [x for x in self.connection_data if x["exchange"]=="deribit" and x["objective"]=="depth"]
        deribit_depths = {x.get("id_api_2") : self.loop.run_until_complete(ws_fetcher_helper(x.get("1stBooksSnapMethod"))) for x in deribit_depths}
        return deribit_depths

    def setup_logger(self, log_file, maxBytes=10*1024*1024, backupCount=5):
        """
            Setups rotating logger with spesific logfile size and backup count
        """
        log_file = log_file / "logs/consumer.log"
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

    async def setup_databases(self):
        """ 
            Insert into database method must have 4 args: pipe_type, data, connection_data, on_message
                pipe_type: [id_api, id_api_2, id_ws]
                on_message : callable method, on message process
        """
        
        if self.mode == "testing":
            folder_path = "/".join([str(base_path), "jsondata"])
            self.mochnosql = MockdbConnector(folder_path)
            self.insert_into_database = partial(self.mochnosql.save, market_state=self.market_state, logger=self.logger)
            print("MochDb databse is ready!")
                    
        if self.mode == "production":
            # Postgres
            try:
                self.sqldb = PostgresConnector(self.postgres_username, self.postgres_host, self.postgres_port, self.postgres_username, self.postgres_dbname)
                self.sqldb.create_database()
                await self.sqldb.connect()
                await self.sqldb.create_tables_for_dead_messages([cd.get("topic_name") for cd in self.connection_data])
            except Exception as e:
                raise RuntimeError("Credentials for PostgreSQL database are missing, database wasn't created") from e
            # ClickHouse
            print("Postgres and Clickhouse databases are ready!")

    def create_wsbooks_agent(self, cd : dict):
        """
            cd : dictionary with connection data
                 Creating a single agent (with the help of closures)
                 https://github.com/robinhood/faust/issues/300
            
            Note that if above code will run after app is already started, you need to start your new agents manually.
            new_agent = app.agent(channel=..., name=...)(agent_coro)
            new_agent.start()        
        """
        async def process_wsbooks_agent(stream: faust.StreamT) -> AsyncIterator:
            """Handler for websocket topics of orderbooks"""
            exchange = cd.get("exchange")
            if exchange != "deribit":
                data = cd.get("1stBooksSnapMethod")()
            if exchange == "deribit":
                id_ = cd.get("id_api_2")
                data = self.deribit_depths.get(id_)
                del self.deribit_depths[id_]
            await self.insert_into_database(pipe_type="id_api_2", data=data, connection_data=cd, on_message=cd.get("on_message_method_api_2"))
            async for byte_data in stream:
                await self.insert_into_database(pipe_type="id_ws", data=byte_data.decode(), connection_data=cd, on_message=cd.get("on_message_method_ws"))
                yield byte_data
        return process_wsbooks_agent

    def create_ws_agent(self, cd : dict):
        """Handler for regular websocket topics"""
        async def process_ws_agent(stream: faust.StreamT) -> AsyncIterator:
            """ Configuration of the API agent"""
            async for byte_data in stream:
                await self.insert_into_database(pipe_type="id_ws", data=byte_data.decode(), connection_data=cd, on_message=cd.get("on_message_method_ws"))
                yield byte_data
        return process_ws_agent
    
    def create_api_agent(self, cd : dict):
        """Handler for api topics"""
        async def process_api_agent(stream: faust.StreamT) -> AsyncIterator:
            """ Configuration of the API agent"""
            async for byte_data in stream:
                data = byte_data.decode()
                await self.insert_into_database(pipe_type="id_api", data=byte_data.decode(), connection_data=cd, on_message=cd.get("on_message_method_api"))
                yield data
        return process_api_agent
            

