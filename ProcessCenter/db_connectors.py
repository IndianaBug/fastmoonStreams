import backoff
import asyncpg
import uuid
import rapidjson as json
import aiofiles
import os
import subprocess
from asynch import connect
from asynch.cursors import DictCursor
from asynch.errors import ServerException
from pathlib import Path

class PostgresConnector:
    
    """ 
        asyncpg : https://github.com/MagicStack/asyncpg 
        oficial : https://www.postgresql.org/
    """
    
    def __init__(self, username, host, port, password, database_name):
        self.username = username
        self.host = host
        self.password = password
        self.dsn =  f"postgresql://{username}:{password}@{host}/{database_name}"
        self.port = port
        self.conn = None

    async def connect(self):
        self.conn = await asyncpg.connect(self.dsn)

    async def close(self):
        await self.conn.close()

    @backoff.on_exception(backoff.expo, (asyncpg.PostgresError), max_tries=5)
    async def execute(self, query, *args):
        async with self.conn.transaction():
            await self.conn.execute(query, *args)

    @backoff.on_exception(backoff.expo, (asyncpg.PostgresError), max_tries=5)
    async def fetch(self, query, *args):
        async with self.conn.transaction():
            return await self.conn.fetch(query, *args)

    async def create_table(self, table_name, columns):
        col_defs = ', '.join([f"{col} {dtype}" for col, dtype in columns.items()])
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({col_defs});"
        await self.execute(query)

    async def drop_table(self, table_name):
        query = f"DROP TABLE IF EXISTS {table_name};"
        await self.execute(query)

    async def add_column(self, table_name, column_name, data_type):
        query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {data_type};"
        await self.execute(query)

    async def drop_column(self, table_name, column_name):
        query = f"ALTER TABLE {table_name} DROP COLUMN {column_name};"
        await self.execute(query)

    async def insert_dict(self, table_name, data):
        keys = ', '.join(data.keys())
        values = ', '.join([f"${i+1}" for i in range(len(data))])
        query = f"INSERT INTO {table_name} ({keys}) VALUES ({values})"
        await self.execute(query, *data.values())


    async def create_table_for_topic(self, topic_name):
        query = f"""
        CREATE TABLE IF NOT EXISTS {topic_name}_dead_messages (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            message TEXT NOT NULL,
            error TEXT,
            attempts INT DEFAULT 1
        );
        """
        await self.execute(query)
        
    async def create_tables_for_dead_messages(self, topics):
        for topic in topics:
            await self.create_table_for_topic(topic)
        
    async def get_dead_messages(self, topic_name, limit=100):
        query = f"SELECT * FROM {topic_name}_dead_messages ORDER BY timestamp DESC LIMIT $1;"
        return await self.fetch(query, limit)

    async def cleanup_old_records(self, table_name, days):
        query = f"DELETE FROM {table_name} WHERE timestamp < NOW() - INTERVAL '{days} days';"
        await self.execute(query)

    def create_database(self):
        try:
            # Construct the command to create the database using psql
            command = [
                'psql',
                f'-U{self.username}',
                f'-h{self.host}',
                f'-p{self.port}',
                '-c',
                f'CREATE DATABASE {self.dsn};'
            ]
            env = {
                'PGPASSWORD': self.password
            }
            result = subprocess.run(command, env=env, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Postgres Database '{self.dsn}' created successfully.")
            else:
                print(f"Failed to create postgres database '{self.dsn}': {result.stderr}")
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while creating database '{self.dsn}': {e.stderr}")
        
        
class MockdbConnector:
    
    def __init__(self, folder_path):
        self.folder_path =  folder_path
        
    def build_fodlers(self, connection_data, pipe_type, is_raw=False):
        pipe_id = connection_data.get(pipe_type, connection_data.get("id_api"))
        folder_type = pipe_type.split("_")[1]
        exchange = connection_data.get("exchange")
        folder_type_2 = "raw" if not is_raw else "processed"
        
        folder_path = Path("/".join([self.folder_path, folder_type_2, folder_type, exchange]))
        if not folder_path.exists():
            folder_path.mkdir(parents=True, exist_ok=True)
        relative_file_path = "/".join([self.folder_path, folder_type_2, folder_type, exchange, pipe_id]) + ".json"
        return pipe_id, relative_file_path

    async def save(self, market_state, logger, pipe_type, data, connection_data, on_message:callable,):
        """  pipe_type : id_ws, id_api, id_api_2 """

        pipe_id = connection_data.get("id_api") if "id_api" in connection_data else connection_data.get("id_ws")

        try:

            data = json.loads(data)
            pipe_id, relative_file_path = self.build_fodlers(connection_data, pipe_type, False)

            # try:
            #     data = await on_message(data=data, market_state=market_state, connection_data=connection_data)
            #     pipe_id, relative_file_path = self.build_fodlers(connection_data, pipe_type, True)
            # except Exception as e:
            #     data = json.loads(data)
            #     pipe_id, relative_file_path = self.build_fodlers(connection_data, pipe_type, False)
            
            data["_doc"] = str(uuid.uuid4())
            
            if not os.path.exists(relative_file_path):
                async with aiofiles.open(relative_file_path, mode='w') as f:
                    content = [data]
                    await f.seek(0)
                    await f.truncate()
                    await f.write(json.dumps(content, indent=2))
            else:
                async with aiofiles.open(relative_file_path, mode='r+') as f:
                    try:
                        content = await f.read()
                        content = json.loads(content)
                    except json.JSONDecodeError as e:
                        print(f"JSONDecodeError reading file: {e}")
                        content = []

                    content.insert(0, data)
                    await f.seek(0)
                    await f.truncate()
                    await f.write(json.dumps(content, indent=2))
                    
        except FileNotFoundError as e:
            print(data)
            logger.error(f"FileNotFoundError of {pipe_id}: {e}")
        except PermissionError as e:
            print(data)
            logger.error(f"PermissionError of {pipe_id}: {e}")
        except IOError as e:
            print(data)
            logger.error(f"IOError handling file operations of {pipe_id}: {e}")
        except Exception as e:
            print(data)
            logger.error(f"Unexpected error handling file operations of {pipe_id}: {e}")
            


class AsyncClickHouseConnector:
    
    """  
        official: https://github.com/ClickHouse/ClickHouse
        asyncronious: https://github.com/long2ice/asynch  
        linux installer: https://clickhouse.com/docs/en/install
    """

    
    def __init__(self, host: str, logger, port: int = 9000, username: str = 'default', password: str = '', database: str = 'default', max_connections: int = 10):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.max_connections = max_connections
        self.connection = None
        self.logger = logger

    async def connect(self):
        self.connection = await connect(
            host=self.host,
            port=self.port,
            user=self.username,
            password=self.password,
            database=self.database,
            max_open_connections=self.max_connections
        )
        self.logger.info("Connected to ClickHouse")

    async def close(self):
        if self.connection:
            await self.connection.close()
            self.logger.info("Connection closed")

    async def configure(self, settings: dict):
        async with self.connection.cursor() as cursor:
            for setting, value in settings.items():
                await cursor.execute(f"SET {setting} = {value}")
                self.logger.info(f"Set {setting} = {value}")

    async def create_table(self, table_name: str, schema: str):
        """ 
            Example of schema:
                    (
                    timestamp DateTime,
                    symbol String,
                    prices Array(Float32),
                    volumes Array(UInt32),
                    sides Array(String),
                    open_interest UInt32,
                    indicator Float32
                    )
        """
        async with self.connection.cursor() as cursor:
            create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({schema}) ENGINE = MergeTree() ORDER BY tuple()"
            await cursor.execute(create_table_query)
            self.logger.info(f"Table {table_name} created with schema: {schema}")

    @backoff.on_exception(backoff.expo, ServerException, max_tries=5)
    async def insert_data(self, table_name: str, data: list):
        async with self.connection.cursor() as cursor:
            try:
                await cursor.execute(f"INSERT INTO {table_name} VALUES", data)
                self.logger.info(f"Inserted {len(data)} rows into {table_name}")
            except ServerException as e:
                self.logger.error(f"Error inserting data: {e}")

    @backoff.on_exception(backoff.expo, Exception, max_tries=5)
    async def query_data(self, query: str):
        async with self.connection.cursor(cursor=DictCursor) as cursor:
            await cursor.execute(query)
            result = await cursor.fetchall()
            self.logger.info(f"Query executed: {query}")
            return result
    
    async def set_initial_config(self, setting=None):
        if not settings:
            settings = {
                'max_memory_usage': '32G',
                'max_threads': 32,
                'max_block_size': 65536,
                'merge_tree_max_bytes_to_use_cache': 10737418240,
                'merge_tree_min_bytes_for_wide_part': 104857600,
                'keep_alive_timeout': 300,
                'max_partitions_per_insert_block': 100,
                'merge_with_ttl_timeout': 3600,
                'max_execution_time': 60,
                'max_insert_block_size': 1048576
            }
        await self.configure(settings)
        
        

# Sharding is a method of distributing data across multiple servers or nodes to improve performance and scalability. In ClickHouse, sharding is typically configured at the table level, and it involves defining how data is split across different shards.

# Steps to Configure Sharding:

# Define Cluster: Create a cluster configuration in the ClickHouse server configuration file (usually config.xml). This defines which servers are part of the cluster.

# Create Distributed Table: Create a distributed table that serves as a logical table spanning multiple physical shards.

# Shard Key: Define a shard key that determines how data is distributed among the shards.

# Example:
# Cluster Configuration (in config.xml):
# xml
# Copiar código
# <yandex>
#     <remote_servers>
#         <my_cluster>
#             <shard>
#                 <replica>
#                     <host>node1</host>
#                     <port>9000</port>
#                 </replica>
#                 <replica>
#                     <host>node2</host>
#                     <port>9000</port>
#                 </replica>
#             </shard>
#             <shard>
#                 <replica>
#                     <host>node3</host>
#                     <port>9000</port>
#                 </replica>
#                 <replica>
#                     <host>node4</host>
#                     <port>9000</port>
#                 </replica>
#             </shard>
#         </my_cluster>
#     </remote_servers>
# </yandex>