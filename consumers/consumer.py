import faust
import aiocouch
import rapidjson as json
from utilis_consumer import MockCouchDB
import asyncio
from faust import App


class XBTApp(App):
    
    def __init__(self, connection_data, app_name="XBT", database="mockCouchDB", database_folder="mochdb_onmessage", couch_host="", couch_username="", couch_password="", mode="production"):
        self.connection_data = connection_data
        self.name = app_name
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
                    
    async def initiate_stream_api(self, connection_dict):
        agent_decorator = self.agent(connection_dict.get("topic_name"))
        @agent_decorator        
        async def process_data(data):
            async for byte_data in data:
                print(byte_data)
                # await self.insert_into_mockCouchDB_3(byte_data.decode(), connection_dict)
                
    async def initiate_strems(self):
        for cd in self.connection_data:
            if "depth" in cd.get("id_ws", ""):
                await self.initiate_stream_ws_books(cd)
            elif "id_api" in cd:
                await self.initiate_stream_api(cd)
            else:
                await self.initiate_stream_ws(cd)
    
    async def start_XBT(self):
        await self.initiate_strems()
        self.main()


         

