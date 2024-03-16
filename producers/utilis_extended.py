import time
import http.client
import asyncio 
from urllib.parse import urlencode
import requests
import json
from producers.utilis import bingx_AaWSnap, build_jwt_api, websocket_fetcher, get_dict_by_key_value, move_dict_to_beginning
from urls import AaWS
import concurrent.futures


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
    exchanges_for_books = ["binance", "bybit", "coinbase", "kucoin", "mexc", "bitget", "gateio"] 
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
    try:
        fu = move_dict_to_beginning(fu, "kucoin_spot_btcusdt_depth")       # Put those at the beggining
        fu = move_dict_to_beginning(fu, "kucoin_perpetual_btcusdt_depth")
    except:
        pass
    books_dic = {}
    try:
        for url in fu:
            id = url["id"]
            type_ = url["type"]
            obj = url["obj"]
            exchange = url["exchange"]
            if obj == "depth" and type_ == "websocket" and exchange not in ["htx", "deribit"]:
                books = books_snapshot(id, snaplength=1000)
                books_dic[id] = books
        return books_dic
    except:
        return {}
