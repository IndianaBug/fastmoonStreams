import time
import http.client
import asyncio 
from urllib.parse import urlencode
import requests
import json
from utilis import bingx_AaWSnap, build_jwt_api, websocket_fetcher, get_dict_by_key_value
from urls import AaWS

def books_snapshot(id, snaplength):
    """
      Get lates snapshot via API
    """
    stream_data = get_dict_by_key_value(AaWS, "id", id)
    url = stream_data.get("url")
    exchange = stream_data.get("exchange")
    instrument = stream_data.get("instrument")
    insType= stream_data.get("insType")

    if exchange in ["binance", "gateio"]:
        url = "&".join([url, f"limit={snaplength}"])
    if exchange == "coinbase":
        url_1 = stream_data["url_base"]
        url_2 = url
    if exchange in ["gateio",  "kucoin", "deribit"]:
        headers = stream_data['headers'] 
    
    if exchange in ['binance', 'bybit']:
        response = requests.get(url)
        response = response.json()    
        if 'code' in response:
            time.sleep(1)
            books_snapshot(id, snaplength-100)
    
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
        response = json.loads(asyncio.get_event_loop().run_until_complete(websocket_fetcher(url, headers)))

    if exchange == 'bingx':
        path = stream_data["path"]
        params = stream_data["params"]
        params["limit"] = str(snaplength)
        response = bingx_AaWSnap(url, path, params)
        if 'code' in response:
            time.sleep(0.51)
            books_snapshot(id, snaplength-100)

    data = {
        "exchange" : exchange,
        "instrument" : instrument,
        "insType" : insType,
        "response" : response
    }
    return data


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
    return data 

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


print(books_snapshot("binance_perpetual_btcusd_depth", 100))