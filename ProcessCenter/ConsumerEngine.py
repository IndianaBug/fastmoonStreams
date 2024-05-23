import requests
from pathlib import Path
import asyncio
from typing import AsyncIterator
import logging
from logging.handlers import RotatingFileHandler
import aiocouch
import rapidjson as json
import faust
from ProcessCenter.utilis_ConsumerEngine import MockCouchDB
from ProcessCenter.utilis_ConsumerEngine import ws_fetcher_helper, insert_into_CouchDB, insert_into_CouchDB_2
import sys
import backoff
from errors import *
# Todo: 
# Add database related exceptions, everywhere

base_path = Path(__file__).parent.parent

class XBTApp(faust.App):
    
    def __init__(self, 
                 connection_data, 
                 database="mockCouchDB",
                 couch_host="",
                 couch_username="", 
                 couch_password="", 
                 log_file_bytes=10*1024*1024,
                 log_file_backup_count=5,
                 max_reconnect_retries=8,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        # faust configs
        self.id = id
        self.broker = dict(kwargs).get("broker")
        self.topic_partitions = dict(kwargs).get("topic_partitions")
        self.value_serializer = dict(kwargs).get("value_serializer")
        self.max_reconnect_retries = max_reconnect_retries
        self.logger = self.setup_logger(base_path, log_file_bytes, log_file_backup_count)
        self.connection_data = connection_data
        self.database_name = database
        self.database_folder = str(base_path / "database")
        self.setup_database(couch_host, couch_username, couch_password) 
        self.market_state = {} # lates data dictionary, everyhting except trades and depth
        self.deribit_depths = self.fetch_initial_deribit_depth()
        
    async def handle_backoff(self, details):
        """handles what to do on recoverable exceptions"""
        exception = details['exception']
        if isinstance(exception, aiocouch.exception.UnauthorizedError):
            await self.couchdb_refresh_credentials()
        elif isinstance(exception, aiocouch.exception.ConflictError):
            await self.couchdb_merge_conflicts()
        elif isinstance(exception, aiocouch.exception.ExpectationFailedError):
            await self.couchdb_fix_request_header()
        elif isinstance(exception, faust_message_errors):
            await self.couchdb_fix_request_header()
            
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
        
    @staticmethod
    def db_errors_wrapper(func):
        """ pattern of couchdb and mochdb errors"""
        async def wrapper(self, *args, **kwargs):
            try:
                func(self, *args, **kwargs)
            except db_backup_errors as e:
                self.logger.error("database recoverable error: %s, retrying", e, exc_info=True)
                raise
            except db_proceed_errors:
                self.logger.error("database unrecoeverable error: %s", e, exc_info=True)
        async def wrapper_with_backoff(self, *args, **kwargs):
            return await backoff.on_exception(backoff.expo, db_backup_errors, max_tries=self.max_reconnect_retries, on_backoff=self.handle_backoff)(wrapper)(self, *args, **kwargs)
        return wrapper_with_backoff
    
    @staticmethod
    def faust_errors_wrapper(func):
        """ pattern of couchdb and mochdb errors"""
        async def wrapper(self, *args, **kwargs):
            try:
                func(self, *args, **kwargs)
            except faust_backup_errors as e:
                self.logger.error("faust recoverable error: %s, retrying", e, exc_info=True)
                raise
            except (faust_message_errors, faust_proceed_errors):
                self.logger.error("faust message error: %s", e, exc_info=True)
                await self.faust_error_on_message()
            except faust_shutdown_errors:
                # Handle unrecoverable errors here (e.g., clean up resources, notify user)
                pass
        async def wrapper_with_backoff(self, *args, **kwargs):
            return await backoff.on_exception(backoff.expo, faust_backup_errors, max_tries=self.max_reconnect_retries, on_backoff=self.handle_backoff)(wrapper)(self, *args, **kwargs)
        return wrapper_with_backoff
    
    
    @staticmethod
    def websocket_errors_wrapper(func):
        """ pattern of couchdb and mochdb errors"""
        async def wrapper(self, *args, **kwargs):
            try:
                func(self, *args, **kwargs)
            except ws_backoff_errors as e:
                self.logger.error("websocket recoverable error: %s, retrying", e, exc_info=True)
                raise
            except ws_unrecoverable_errors as e:
                self.logger.error("WebSocket unrecoverable error: %s, not retrying", e, exc_info=True)
                # Handle unrecoverable errors here (e.g., clean up resources, notify user)
                raise
            except Exception as e:
                self.logger.error("Unexpected error: %s, not retrying", e, exc_info=True)
                # Handle other unexpected errors
                raise
        async def wrapper_with_backoff(self, *args, **kwargs):
            return await backoff.on_exception(backoff.expo, ws_backoff_errors, max_tries=self.max_reconnect_retries, on_backoff=self.handle_backoff)(wrapper)(self, *args, **kwargs)
        
        return wrapper_with_backoff

    @websocket_errors_wrapper
    def fetch_initial_deribit_depth(self):
        deribit_depths = [x for x in self.connection_data if x["exchange"]=="deribit" and x["objective"]=="depth"]
        deribit_depths = {x.get("id_api_2") : asyncio.run(ws_fetcher_helper(x.get("1stBooksSnapMethod"))) for x in deribit_depths}
        del deribit_depths
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

    def setup_database(self, couch_host, couch_username, couch_password):
        """
            sets database
        """
        # Couch db if selected
        if self.database_name == "CouchDB":
            self.db = aiocouch.Server(couch_host)
            self.db.resource.credentials = (couch_username, couch_password)
            self.ws_latencies = {}

        ws_ids = [di.get("id_ws") for di in self.connection_data if "id_ws" in di]
        api_ids = [di.get("id_api") for di in self.connection_data if "id_api" in di]
        api_2_ids = [di.get("id_api_2") for di in self.connection_data if "id_api_2" in di]
        list_of_databases = ws_ids + api_ids + api_2_ids
        existing_databases = []
        if self.database_name == "CouchDB":
            for databse in list_of_databases:
                setattr(self, f"db_{databse}", self.db.create(databse))
                existing_databases.append(databse)
            print(f"CouchDB server with {len(existing_databases)} databases is ready!!!")
        if self.database_name == "mockCouchDB":
            for databse in list_of_databases:
                setattr(self, f"db_{databse}", MockCouchDB(databse, self.database_folder))
                existing_databases.append(databse)
            print(f"mockCouchDB server with {len(existing_databases)} databases is ready!!!")

        # Creates inserting methods
        if self.database_name == "mockCouchDB":
            self.insert_into_database = self.insert_into_mockCouchDB
            self.insert_into_database_2 = self.insert_into_mockCouchDB_2
            self.insert_into_database_3 = self.insert_into_mockCouchDB_3
        if self.database_name == "CouchDB":
            self.insert_into_database = insert_into_CouchDB
            self.insert_into_database_2 = insert_into_CouchDB_2
    
    @db_errors_wrapper
    async def insert_into_mockCouchDB(self, data, connection_dict):
        """ mockdb method 1"""
        await getattr(self, f"db_{connection_dict.get('id_ws')}").save(data=data, market_state=self.market_state, connection_data=connection_dict, on_message=connection_dict.get("on_message_method_ws"))

    @db_errors_wrapper
    async def insert_into_mockCouchDB_2(self, data, connection_dict):
        """ mockdb method 2"""
        await getattr(self, f"db_{connection_dict.get('id_api_2')}").save(data=data, market_state=self.market_state, connection_data=connection_dict, on_message=connection_dict.get("on_message_method_api_2"))

    @db_errors_wrapper
    async def insert_into_mockCouchDB_3(self, data, connection_dict):
        """ mockdb method 3"""
        await getattr(self, f"db_{connection_dict.get('id_api')}").save(data=data, market_state=self.market_state, connection_data=connection_dict,  on_message=connection_dict.get("on_message_method_api"))


    def create_wsbooks_agent(self, cd : dict):
        """
            cd : dictionary with connection data
                 Creating a single agent (with the help of closures)
                 https://github.com/robinhood/faust/issues/300
            
            Note that if above code will run after app is already started, you need to start your new agents manually.
            new_agent = app.agent(channel=..., name=...)(agent_coro)
            new_agent.start()        
        """
        @self.faust_errors_wrapper
        async def process_wsbooks_agent(stream: faust.StreamT) -> AsyncIterator:
            """Handler for websocket topics of orderbooks"""
            exchange = cd.get("exchange")
            if exchange != "deribit":
                if self.database_name == "mockCouchDB":
                    data = cd.get("1stBooksSnapMethod")()
                    await self.insert_into_database_2(data, cd)
                    print(data)
                else:
                    data = cd.get("1stBooksSnapMethod")()
                    print(data)
                    await self.insert_into_database_2(data, cd)
            if exchange == "deribit":
                print(data)
                await self.insert_into_database_2(self.deribit_depths.get(cd.get("id_api_2")), cd)
                del self.deribit_depths
            async for byte_data in stream:
                await self.insert_into_database(byte_data, cd)
                yield byte_data
        return process_wsbooks_agent

    def create_ws_agent(self, cd : dict):
        """Handler for regular websocket topics"""
        @self.faust_errors_wrapper
        async def process_ws_agent(stream: faust.StreamT) -> AsyncIterator:
            """ Configuration of the API agent"""
            async for byte_data in stream:
                await self.insert_into_database(byte_data.decode(), cd)
                yield byte_data
        return process_ws_agent
    
    def create_api_agent(self, cd : dict):
        """Handler for api topics"""
        @self.faust_errors_wrapper
        async def process_api_agent(stream: faust.StreamT) -> AsyncIterator:
            """ Configuration of the API agent"""
            async for byte_data in stream:
                data = byte_data.decode()
                await self.insert_into_database_3(data, cd)
                yield data
        return process_api_agent
            


