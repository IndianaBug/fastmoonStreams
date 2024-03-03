import time
import http.client
import asyncio 
from urllib.parse import urlencode
import requests
import json
from utilis import bingx_AaWSnap, build_jwt_api, websocket_fetcher, get_dict_by_key_value
from urls import AaWS
import concurrent.futures

def books_snapshot(id, snaplength, maximum_retries=10):
    """
      Get lates snapshot via API
    """
    stream_data = get_dict_by_key_value(AaWS, "id", id)
    url = stream_data.get("url")
    exchange = stream_data.get("exchange")
    instrument = stream_data.get("instrument")
    insType= stream_data.get("insType")

    if exchange == "binance":
        url = "&".join([url, f"limit={snaplength}"])
    if exchange == "gateio":
        url = "&".join([url, f"limit={300}"])
    if exchange == "coinbase":
        url_1 = stream_data["url_base"]
        url_2 = url
    if exchange in ["gateio",  "kucoin", "deribit"]:
        headers = stream_data['headers'] 
    
    if exchange in ['binance', 'bybit']:
        for _ in range(maximum_retries):
            response = requests.get(url)
            response = response.json()
            if 'code' in response:    
                if response.get('code', None) == -1130:
                    snaplength = snaplength - 500
                    url = "&".join([url, f"limit={snaplength}"])
            else:
                break


    if exchange == "coinbase":
        conn = http.client.HTTPSConnection(url_1)
        payload = ''
        headers = {
            "Authorization": f"Bearer {build_jwt_api()}",
            'Content-Type': 'application/json'
        }
        conn.request("GET", url_2, payload, headers)
        res = conn.getresponse()
        response = res.read()
        response = json.loads(response)

    if exchange == "kucoin":
        response = requests.get(url, headers=headers)
        response = response.json()

    if exchange == "gateio":
        response = requests.request('GET', url, headers=headers)
        response = response.json()
    
    if exchange in ["mexc", "bitget", "htx"]:
        response = requests.get(url)
        response = response.json()
    
    if exchange == "deribit":
        # def run_event_loop():
        loop = asyncio.get_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(websocket_fetcher(url, headers))
        finally:
            loop.close()
        # with concurrent.futures.ThreadPoolExecutor() as executor:
        #     future = executor.submit(run_event_loop)
        #     result = future.result()
        # response = json.loads(asyncio.get_event_loop().run_until_complete(websocket_fetcher(url, headers)))

    if exchange == 'bingx':
        path = stream_data["path"]
        params = stream_data["params"]
        p = [5, 10, 20, 50, 100, 500, 1000]
        p.reverse()
        for i, _ in enumerate(range(maximum_retries)):
            params["limit"] = p[i]
            response = bingx_AaWSnap(url, path, params)
            if response["code"] == 0:
                break

    data = {
        "exchange" : exchange,
        "instrument" : instrument,
        "insType" : insType,
        "response" : response 
    }
    return data

def flatten_list(nested_list):
    flattened_list = []
    for item in nested_list:
        if isinstance(item, list):
            flattened_list.extend(flatten_list(item))
        else:
            flattened_list.append(item)
    return flattened_list

def AllStreamsByInstrument(exchange, insType, instrument):
    link = [stream for stream in AaWS if stream["exchange"] == exchange and stream["insType"] == insType and stream["instrument"] == instrument]
    return link

def  AllStreamsByInstrumentS(list_of_streams):
    """
        list_of_streams = [[exchange, insType, instrument] ...]
    """
    data = []
    for stream in list_of_streams:
        exchange = stream[0] 
        insType = stream[1] 
        instrument = stream[2]
        link = AllStreamsByInstrument(exchange, insType, instrument)
        data.append(link)
    return flatten_list(data) 

def get_unique_instruments():
    return list(set([ "_".join(idd.split("_")[:3]) for idd in [stream["id"] for stream in AaWS]]))

def  AllStreamsExceptInstrumentS(list_of_streams):
    """
        list_of_streams = [[exchange, insType, instrument] ...]
        Returns the list of links except for selected group
    """
    data = AllStreamsByInstrumentS(list_of_streams)
    filtered_list = [elem for elem in AaWS if elem not in data]
    return filtered_list 

def get_depth_sockets(urls):
    exchanges_for_books = ["binance", "bybit", "coinbase", "kucoin", "mexc", "bitget", "deribit", "gateio"] #gateio
    filtered_urls = []
    for url in urls:
        exchange = url["exchange"]
        type_ = url["type"]
        obj = url["obj"]
        if type_ == "websocket" and exchange in exchanges_for_books and obj=="depth":
            filtered_urls.append(url)
    return filtered_urls

def get_initial_books(data):
    fu = get_depth_sockets(data)
    books_dic = {}
    for url in fu:
        id = url["id"]
        type_ = url["type"]
        obj = url["obj"]
        exchange = url["exchange"]
        if obj == "depth" and type_ == "websocket" and exchange not in ["htx", "deribit"]:
            books = books_snapshot(id, snaplength=1000)
            books_dic[id] = books
    return books_dic