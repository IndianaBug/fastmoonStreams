import time
from urllib.parse import urlencode
import requests
import websockets
import ssl
from hashlib import sha256
import json
import jwt
from cryptography.hazmat.primitives import serialization
import secrets
import os
import sys
import hashlib
import hmac
import base64
import random
import string
import aiohttp

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from config import crypto_panic_token, coinbaseAPI, coinbaseSecret, kucoinAPI, kucoinPass, kucoinSecret


# Notes:
# To initialize binance, coinbase orderbooks, you should first make an API call and then push updates of orderbooks
# Okx has only 1 liquidation channel for all liquidations stream /// u need to filter if liquidations belon only to BTC
# bybit stream OI+funding rate in a single websocket


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