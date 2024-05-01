import requests
from pathlib import Path
import asyncio
from typing import AsyncIterator
import logging
from logging.handlers import RotatingFileHandler
import aiocouch
import rapidjson as json
import faust
from utilis_consumer import MockCouchDB
from utilis_consumer import ws_fetcher_helper, insert_into_CouchDB, insert_into_CouchDB_2
from utilis_consumer import insert_into_mockCouchDB, insert_into_mockCouchDB_2, insert_into_mockCouchDB_3
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
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        # faust configs
        self.id = id
        self.broker = dict(kwargs).get("broker")
        self.topic_partitions = dict(kwargs).get("topic_partitions")
        # logger        
        self.logger = self.setup_logger(base_path, log_file_bytes, log_file_backup_count)
        # connection data, streaming, processing 
        self.connection_data = connection_data
        # database
        self.database_name = database
        self.database_folder = str(base_path / "database")
        self.setup_database(couch_host, couch_username, couch_password) 
        # Marketstate
        self.market_state = {} # lates data dictionary, everyhting except trades and depth
        # Deribit depth
        self.deribit_depths = self.setup_deribit_depth()

    def setup_logger(self, log_file, maxBytes=10*1024*1024, backupCount=5):
        """
            Setups rotating logger with spesific logfile size and backup count
        """
        log_file = log_file / "logs/applogs.log"
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

    def setup_deribit_depth(self):
        """
            Deribit requires websockets to make api calls. websockets carrotines cant be called within websockets carotines (maybe can idk). This is the helper to mitigate the problem
        """
        try:
            deribit_depths = [x for x in self.connection_data if x["exchange"]=="deribit" and x["objective"]=="depth"]
            deribit_depths = {x.get("id_api_2") : asyncio.run(ws_fetcher_helper(x.get("1stBooksSnapMethod"))) for x in deribit_depths}
            del deribit_depths
            return deribit_depths
        except ValueError as e:
            self.logger.error("JSON decoding failed while setting deribit depth: %s", e)
        except requests.exceptions.HTTPError as e:
            self.logger.error("HTTP error occurred while setting deribit depth:: %s", e)
        except requests.exceptions.ConnectionError as e:
            self.logger.error("Connection error occurred while setting deribit depth:: %s", e)
        except requests.exceptions.Timeout as e:
            self.logger.error("Request timed out while setting deribit depth:: %s", e)
        except Exception as e:
            self.logger.error("An unexpected error occurred while setting deribit depth:: %s", e)

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
            self.insert_into_database = insert_into_mockCouchDB
            self.insert_into_database_2 = insert_into_mockCouchDB_2
            self.insert_into_database_3 = insert_into_mockCouchDB_3
        if self.database_name == "CouchDB":
            self.insert_into_database = insert_into_CouchDB
            self.insert_into_database_2 = insert_into_CouchDB_2

    async def process_wsbooks_agent(self, cd: dict, stream: faust.StreamT) -> AsyncIterator:
        """
            Handler for WSbooks topic
        """
        exchange = cd.get("exchange")
        if exchange != "deribit":
            if self.database_name == "mockCouchDB":
                data = cd.get("1stBooksSnapMethod")()
                # await self.insert_into_database_2(data, cd)
                print(data)
            else:
                data = cd.get("1stBooksSnapMethod")()
                print(data)
                # await self.insert_into_database_2(data, cd)
        if exchange == "deribit":
            print(data)
            # await self.insert_into_database_2(self.deribit_depths.get(cd.get("id_api_2")), cd)
            del self.deribit_depths

        async for byte_data in stream:
            try:
                print(byte_data)
                await self.insert_into_database(byte_data, cd)
                yield byte_data
            except ValueError as e:
                topic_name = cd.get("topic_name")
                self.logger.error("JSONDecodeError  for topic %s: %e", topic_name, e)
            except asyncio.TimeoutError  as e:
                topic_name = cd.get("topic_name")
                self.logger.error("Operation timed out for topic %s: %e", topic_name, e)
            except ConnectionError as e:
                self.logger.error("Connection error for topic %s: %e", topic_name, e)
            except Exception as e:
                topic_name = cd.get("topic_name")
                self.logger.error("Unexpected error raised for topic %s: %e", topic_name, e)
                continue

    async def process_ws_agent(self, cd: dict, stream: faust.StreamT) -> AsyncIterator:
        """
            Handler for WS topics, except depth
        """
        async for byte_data in stream:
            try:
                print(byte_data)
                await self.insert_into_database(byte_data, cd)
                yield byte_data
            except ValueError as e:
                topic_name = cd.get("topic_name")
                self.logger.error("JSONDecodeError  for topic %s: %e", topic_name, e)
            except asyncio.TimeoutError  as e:
                topic_name = cd.get("topic_name")
                self.logger.error("Operation timed out for topic %s: %e", topic_name, e)
            except ConnectionError as e:
                self.logger.error("Connection error for topic %s: %e", topic_name, e)
            except Exception as e:
                topic_name = cd.get("topic_name")
                self.logger.error("Unexpected error raised for topic %s: %e", topic_name, e)
                continue
                    
    async def process_api_agent(self, cd: dict, stream: faust.StreamT) -> AsyncIterator:
        """
            Handler for API topics
        """
        async for byte_data in stream:
            try:
                print(byte_data)
                await self.insert_into_database_3(self, byte_data, cd)
                yield byte_data
            except ValueError as e:
                topic_name = cd.get("topic_name")
                self.logger.error("JSONDecodeError  for topic %s: %e", topic_name, e)
            except asyncio.TimeoutError  as e:
                topic_name = cd.get("topic_name")
                self.logger.error("Operation timed out for topic %s: %e", topic_name, e)
            except ConnectionError as e:
                self.logger.error("Connection error for topic %s: %e", topic_name, e)
            except Exception as e:
                topic_name = cd.get("topic_name")
                self.logger.error("Unexpected error raised for topic %s: %e", topic_name, e)
                continue

# For processing time controll, for later
         
# processing time agreement
# @app.agent(topic)
# async def process(stream):
#     async for event in stream:
#         start_time = time.time()
#         # Process the event
#         # Your processing logic here
#         end_time = time.time()
#         processing_time = end_time - start_time
#         app.monitor.gauge('custom_processing_time', processing_time)

