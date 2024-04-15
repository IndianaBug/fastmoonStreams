import websockets
import ssl
import rapidjson as json
import os
import random
import string
import aiofiles
import uuid
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

class MockCouchDB:
    def __init__(self, filename, folder_name="", buffer_size=1024):
        self.file_path =  folder_name + "/" + filename + ".txt"
        self.buffer_size = buffer_size


    async def save(self, data, market_state, connection_data, on_message:callable):
        try:
            data = await on_message(data=data, market_state=market_state, connection_data=connection_data)
        except Exception as e:
            print(e)
            return
        data["_doc"] = str(uuid.uuid4())
        async with aiofiles.open(self.file_path ,mode='w') as f:
            await json.dump(data, f)
            await f.write("\n")



        # if not os.path.exists(self.file_path):
        #     async with aiofiles.open(self.file_path ,mode='w') as f:
        #         content = []
        #         content.insert(0, data)
        #         await f.seek(0)  
        #         await f.truncate() 
        #         await f.write(json.dumps(content, indent=2)) 
        # else:
        #     async with aiofiles.open(self.file_path ,mode='r+') as f: 
        #         content = await f.read()
        #         content = json.loads(content)
        #         content.insert(0, data)
        #         content = json.dumps(content)
        #         await f.seek(0)  
        #         await f.truncate() 
        #         await f.write(content) 

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
    
class DynamicFixedSizeList_binanceOptionOI:
    def __init__(self, initial_expiries, initial_max_size):
        """
            Initializes the list with the specified initial_max_size.
        """
        self.expiries = initial_expiries
        self.max_size = initial_max_size
        self.data = []

    def update_expiries(self, expiries):
        self.expiries = expiries

    def append(self, item):
        self.set_max_size(len(self.expiries))
        # if len(self.data) == self.max_size:
        #     self.data.pop(0)  
        self.data.append(item)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        return self.data[index]

    def __setitem__(self, index, value):
        self.data[index] = value

    def set_max_size(self, new_max_size):
        if new_max_size < len(self.data):
            self.data = self.data[-new_max_size:]  
        self.max_size = new_max_size


# data_handler = MockCouchDB("large_database.json", "mochdb")
# for i in range(100):
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     loop.run_until_complete(data_handler.save({f"new_key{i}" : str(i)}))

