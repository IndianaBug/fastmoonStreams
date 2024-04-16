import fauststreaming
import aiocouch
import rapidjson as json
from utilis import MockCouchDB


class consumer():
    
    def __init__(self, connection_data, app_name="XBTStreams", database="mockCouchDB", database_folder="mochdb_onmessage", couch_host="", couch_username="", couch_password="", mode="production"):
        self.connection_data = connection_data
        self.app = fauststreaming.App(app_name)
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
        
    async def insert_into_mockCouchDB(self, data, connection_dict, on_message:callable):
        try:
            await getattr(self, f"db_{connection_dict.get('id_ws')}").save(data=data, market_state=self.market_state, connection_data=connection_dict, on_message=on_message)
        except Exception as e:
            print(f'{connection_dict.get("id_ws")} is not working properly' )
            print(e)

    async def insert_into_mockCouchDB_2(self, data, connection_dict, on_message:callable):
        try:
            await getattr(self, f"db_{connection_dict.get('id_api_2')}").save(data=data, market_state=self.market_state, connection_data=connection_dict, on_message=on_message)
        except Exception as e:
            print(f'{connection_dict.get("id_api_2")} is not working properly' )
            print(e)

    async def insert_into_mockCouchDB_3(self, data, connection_dict, on_message:callable):
        try:
            await getattr(self, f"db_{connection_dict.get('id_api')}").save(data=data, market_state=self.market_state, connection_data=connection_dict, on_message=on_message)
        except Exception as e:
            print(f'{connection_dict.get("id_api")} is not working properly' )
            print(e)

    def initiate_stream_ws(self, connection_dict):
        agent_decorator = self.app.agent(connection_dict.get("topic_name"))
        @agent_decorator
        async def process_data(data):
            for str_data in data:
                pass

    def initiate_stream_api(self, connection_dict):
        agent_decorator = self.app.agent(connection_dict.get("topic_name"))
        @agent_decorator        
        async def process_data(data):
            for str_data in data:
                pass
                


# Define the decorator function
def create_decorated_agent(topic):
    @app.agent(topic)
    async def process_order(orders):
        async for order in orders:
            # Process each order using regular Python
            total_price = order.price * order.quantity
            await send_order_received_email(order.account_id, order)

