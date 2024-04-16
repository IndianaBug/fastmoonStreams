import websockets
import ssl
import rapidjson as json
import os
import random
import string
import aiofiles
import uuid
import asyncio
import ujson
from aiokafka import AIOKafkaProducer, TopicExistsError
from aiokafka.errors import KafkaError
import asyncio

def get_dict_by_key_value(lst, key, value):
    for d in lst:
        if d.get(key) == value:
            return d
    return None

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

async def websocket_fetcher(link, headers):
    async with websockets.connect(link,  ssl=ssl_context) as websocket:
        await websocket.send(json.dumps(headers))
        response = await websocket.recv()
        return response

def generate_random_id(length):
    characters = string.ascii_letters + string.digits
    random_id = ''.join(random.choice(characters) for i in range(length))
    return random_id

def generate_random_integer(n):
    if n <= 0:
        raise ValueError("Length should be a positive integer")
    lower_bound = 10 ** (n - 1)
    upper_bound = (10 ** n) - 1
    random_integer = random.randint(lower_bound, upper_bound)
    return random_integer


def retrieve_dictionary_by2_values(list_of_dicts, key1, value1, key2, value2):
    for dictionary in list_of_dicts:
        if key1 in dictionary and key2 in dictionary:
            if dictionary[key1] == value1 and dictionary[key2] == value2:
                return dictionary
    return None  

def move_dict_to_beginning(lst, target_id):
    for i, dictionary in enumerate(lst):
        if dictionary['id'] == target_id and dictionary['type'] == "api":
            # Pop the dictionary and insert it at the beginning
            lst.insert(0, lst.pop(i))
            break
        return lst

def iterate_dict(d):
    v = []
    if isinstance(d, dict):
        for key, value in d.items():
            if isinstance(value, dict):
                iterate_dict(value)
                v.extend(iterate_dict(value))
            else:
                v.append(value)
    else:
        v.append(d)
    return v

def unnest_list(lst):
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(unnest_list(item))
        else:
            result.append(item)
    return result

def recursive_dict_access(dictionary, keys):
    if "." in keys:
        keys = keys.split(".")
    else:
        pass
    key = keys[0]
    if key in dictionary:
        if isinstance(dictionary[key], dict):
            return recursive_dict_access(dictionary[key], keys[1:])
        else:
            return dictionary[key]    
    else:
        return dictionary.get(keys)
    

def filter_nested_dict(nested_dict, condition):
    for key, value in nested_dict.items():
        if isinstance(value, dict):
            nested_dict[key] = filter_nested_dict(value, condition)
        elif isinstance(value, list):
            nested_dict[key] = [item for item in value if condition(item)]
    return nested_dict

import rapidjson as json
import aiofiles
import uuid
import os
import asyncio
import gzip
import ijson
from itertools import islice

async def _chunks(data, chunk_size):
  for i in range(0, len(data), chunk_size):
    yield data[i:i + chunk_size]

class MockCouchDB:
    def __init__(self, filename, folder_name="", buffer_size=1024):
        self.file_path =  folder_name + "/" + filename + ".json"
        self.buffer_size = buffer_size


    async def save(self, data, market_state, connection_data, on_message:callable):
        try:
            data = await on_message(data=data, market_state=market_state, connection_data=connection_data)
        except Exception as e:
            print(e)
            return
        data["_doc"] = str(uuid.uuid4())

        if not os.path.exists(self.file_path):
            async with aiofiles.open(self.file_path ,mode='w') as f:
                content = []
                content.insert(0, data)
                await f.seek(0)  
                await f.truncate() 
                await f.write(json.dumps(content, indent=2)) 
        else:
            async with aiofiles.open(self.file_path ,mode='r+') as f: 
                content = await f.read()
                content = json.loads(content)
                content.insert(0, data)
                content = json.dumps(content)
                await f.seek(0)  
                await f.truncate() 
                await f.write(content) 

async def ws_fetcher_helper(function):
    data = await function()
    return data

def standarize_marginType(instType, marginType):
    if marginType != None:
        if "inverse" in marginType.lower():
            return "inverse"
        if "linear" in marginType.lower():
            return "linear"
    else:
        return instType
      

async def ensure_topic_exists(producer, partitions, replication_factor, topic_name):
    try:
        await producer.client.create_topics([(topic_name, {'partitions': partitions, 'replication_factor': replication_factor})], timeout_ms=10000)
        print(f"Topic '{topic_name}' created successfully or already exists.")
    except TopicExistsError:
        print(f"Topic '{topic_name}' already exists.")
    except KafkaError as e:
        print(f"Error while creating topic '{topic_name}': {e}")

