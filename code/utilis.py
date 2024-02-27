import json
import time
import http.client
from urls import build_jwt_api
import requests
from urls import APIS
import asyncio 
import websockets
import ssl
import hmac
from hashlib import sha256

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

def bingx_apisnap(APIURL, path, paramsMap):
    APIKEY = ""
    SECRETKEY = ""
    def demo():
        payload = {}
        method = "GET"
        paramsStr = parseParam(paramsMap)
        return send_request(method, path, paramsStr, payload)

    def get_sign(api_secret, payload):
        signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
        return signature


    def send_request(method, path, urlpa, payload):
        url = "%s%s?%s&signature=%s" % (APIURL, path, urlpa, get_sign(SECRETKEY, urlpa))
        headers = {
            'X-BX-APIKEY': APIKEY,
        }
        response = requests.request(method, url, headers=headers, data=payload)
        return response.json()

    def parseParam(paramsMap):
        sortedKeys = sorted(paramsMap)
        paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
        if paramsStr != "": 
            return paramsStr+"&timestamp="+str(int(time.time() * 1000))
        else:
            return paramsStr+"timestamp="+str(int(time.time() * 1000))
    return demo()

# Helper to retrive books

def books_snapshot(exchange, instrument, insType, snaplength):
    """
      Gets full latest snapshot of limit orders.
    """
    if exchange in ["binance", "gateio"]:
        link = [x['url'] for x in APIS if x["exchange"] == exchange and x["instrument"] == instrument and x["insType"] == insType][0]
        link = "&".join([link, f"limit={snaplength}"])
    if exchange == "coinbase":
        url_1 = [x["url_base"] for x in APIS if x["exchange"] == "coinbase" and x["obj"] == "depth"][0]
        url_2 = [x["url"] for x in APIS if x["exchange"] == "coinbase" and x["obj"] == "depth"][0] 
    else:
        link = [x['url'] for x in APIS if x["exchange"] == exchange and x["instrument"] == instrument and x["insType"] == insType][0]

    
    if exchange in ['binance', 'bybit']:
        response = requests.get(link)
        response = response.json()    
        if 'code' in response:
            time.sleep(1)
            books_snapshot(exchange, instrument, insType, snaplength-500)
    

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
        headers = [x['headers'] for x in APIS if x["exchange"] == exchange and x["instrument"] == instrument and x["insType"] == insType][0]
        response = requests.get(link, headers=headers)
        response = response.json()

    if exchange == "gateio":
        headers = [x['headers'] for x in APIS if x["exchange"] == exchange and x["instrument"] == instrument and x["insType"] == insType][0]
        response = requests.request('GET', link, headers=headers)
        response = response.json()
    
    if exchange in ["mexc", "bitget", "htx"]:
        response = requests.get(link)
        response = response.json()
    
    if exchange == "deribit":
        headers = [x['headers'] for x in APIS if x["exchange"] == exchange and x["instrument"] == instrument and x["insType"] == insType][0]
        response = json.loads(asyncio.get_event_loop().run_until_complete(websocket_fetcher(link, headers)))

    if exchange == 'bingx':
        path = [x['path'] for x in APIS if x["exchange"] == exchange and x["instrument"] == instrument and x["insType"] == insType][0]
        params = [x['params'] for x in APIS if x["exchange"] == exchange and x["instrument"] == instrument and x["insType"] == insType][0]
        response = bingx_apisnap(link, path, params)

    data = {
        "exchange" : exchange,
        "instrument" : instrument,
        "insType" : insType,
        "response" : response
    }
    return data

def set_deribit_heartbeat():
    d = get_dict_by_key_value(APIS, "id", "deribit_hearbeat")
    url = d["url"]
    msg = d["msg"]
    asyncio.get_event_loop().run_until_complete(websocket_fetcher(url, msg))
    print("Deribit heartbeat is set")

d = get_dict_by_key_value(APIS, "id", "bingx_perpetual_btcusdt_OI")
print(bingx_apisnap(d["url"], d["path"], d["params"]))