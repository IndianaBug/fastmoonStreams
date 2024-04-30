import faust
import aiocouch
import rapidjson as json
from utilis_consumer import MockCouchDB, ws_fetcher_helper
import asyncio
import faust 
from functools import partial
from faust import ChannelT, StreamT, Topic
from typing import AsyncIterator
import logging
import logging.handlers
from confluent_kafka.admin import AdminClient, NewTopic


class XBTApp(faust.App):
    
    def __init__(self, 
                 connection_data, 
                 database="mockCouchDB",
                 database_folder="mochdb_onmessage", 
                 couch_host="",
                 couch_username="", 
                 couch_password="", 
                 mode="production",
                 log_file="app.log",
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        # faust configs
        self.id = id
        self.broker = dict(kwargs).get("broker")
        self.topic_partitions = dict(kwargs).get("topic_partitions")        
        # setup logging for error handling
        self.logger = logging.getLogger(__name__)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  
        self.logger.addHandler(file_handler)
        # Connection data vehicle
        self.connection_data = connection_data
        # database setup
        self.database_name = database
        self.database_folder = database_folder
        if self.database_name == "CouchDB":
            self.db = aiocouch.Server(couch_host)
            self.db.resource.credentials = (couch_username, couch_password)
            self.ws_latencies = {}
        self.set_databases() 
        if self.database_name == "mockCouchDB":
            self.insert_into_database = self.insert_into_mockCouchDB
            self.insert_into_database_2 = self.insert_into_mockCouchDB_2
            self.insert_into_database_3 = self.insert_into_mockCouchDB_3
        if self.database_name == "CouchDB":
            self.insert_into_database = self.insert_into_CouchDB
            self.insert_into_database_2 = self.insert_into_CouchDB_2
        # Dynamic market info container
        self.market_state = {}
        # Deribit requires websockets to make api calls. websockets carrotines cant be called within websockets carotines (maybe can idk). This is the helper to mitigate the problem
        try:
            deribit_depths = [x for x in connection_data if x["exchange"]=="deribit" and x["objective"]=="depth"]
            self.deribit_depths = {x.get("id_api_2") : asyncio.run(ws_fetcher_helper(x.get("1stBooksSnapMethod"))) for x in deribit_depths}
            del deribit_depths
        except:
            pass
    
    def populate_ws_latencies(self):
        for di in self.connection_data:
            connection_id = di.get("id_ws", None)
            if connection_id is not None:
                self.ws_latencies[connection_id] = []

    def set_databases(self):
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

    def insert_into_CouchDB(self, data, connection_dict, on_message:callable):
        getattr(self, f"db_{connection_dict.get('id_ws')}").save(data=data, market_state=self.market_state, connection_data=connection_dict, on_message=on_message)

    def insert_into_CouchDB_2(self, data, connection_dict, on_message:callable):
        getattr(self, f"db_{connection_dict.get('id_api_2')}").save(data=data, market_state=self.market_state, connection_data=connection_dict, on_message=on_message)
        
    async def insert_into_mockCouchDB(self, data, connection_dict):
        try:
            await getattr(self, f"db_{connection_dict.get('id_ws')}").save(data=data, market_state=self.market_state, connection_data=connection_dict, on_message=connection_dict.get("on_message_method_ws"))
        except Exception as e:
            print(f'{connection_dict.get("id_ws")} is not working properly' )
            print(e)

    async def insert_into_mockCouchDB_2(self, data, connection_dict):
        try:
            await getattr(self, f"db_{connection_dict.get('id_api_2')}").save(data=data, market_state=self.market_state, connection_data=connection_dict, on_message=connection_dict.get("on_message_method_api_2"))
        except Exception as e:
            print(f'{connection_dict.get("id_api_2")} is not working properly' )
            print(e)

    async def insert_into_mockCouchDB_3(self, data, connection_dict):
        try:
            await getattr(self, f"db_{connection_dict.get('id_api')}").save(data=data, market_state=self.market_state, connection_data=connection_dict,  on_message=connection_dict.get("on_message_method_api"))
        except Exception as e:
            print(f'{connection_dict.get("id_api")} is not working properly' )
            print(e)

    async def initiate_stream_ws_books(self, connection_dict):
        
        if exchnage != "deribit":
            if self.database_name == "mockCouchDB":
                data = connection_data.get("1stBooksSnapMethod")()
                # await self.insert_into_mockCouchDB(data, connection_data)
                print(data)
            else:
                data = connection_data.get("1stBooksSnapMethod")()
                print(data)
                # await self.insert_into_mockCouchDB(data, connection_data)
        if exchange == "deribit":
            print(data)
            # await self.insert_into_mockCouchDB(self.deribit_depths.get(connection_dict.get("id_api_2")), connection_data)
            del self.deribit_depths

        agent_decorator = self.agent(connection_dict.get("topic_name"))
        @agent_decorator
        async def process_data(data):
            async for byte_data in data:
                print(byte_data)
                # await self.insert_into_mockCouchDB(byte_data.decode(), connection_dict)

    async def initiate_stream_ws(self, connection_dict):
        agent_decorator = self.agent(connection_dict.get("topic_name"))
        @agent_decorator
        async def process_data(data):
            async for byte_data in data:
                # await self.insert_into_mockCouchDB(byte_data.decode(), connection_dict)
                print(byte_data.decode())
 
    def ensure_dead_letter_topic_exists(self, topic_name="dead_letter", number_partitions=5, replication_factor=1):
        bootstrap_servers = self.broker.replace("kafka://", "")
        admin_client = AdminClient({"bootstrap.servers": bootstrap_servers})
        new_topic = NewTopic(topic_name, num_partitions, replication_factor)
        admin_client.create_topics([new_topic])
        admin_client.close()
                    
    async def process_api_agent(
                    self,
                    cd: dict,
                    stream: StreamT
                ) -> AsyncIterator:
        async for byte_data in stream:
            try:
                print(byte_data)
                await self.insert_into_mockCouchDB_3(byte_data, cd)
                yield byte_data
            except Exception as e:
                topic_name = cd.get("topic_name")
                self.logger.error(f"Exception raised for topic {topic_name}: {e}")
                self.logger.info(f"Exception raised for topic {topic_name}: {e}")

         
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

