import uuid
import random
import json
import requests

from monitors.loggers.logger_setup import LoggerSetup

logger_setup = LoggerSetup("app.logs")

class Common_API_Methods:
    
    logger = logger_setup.logger
    def generate_uuid(self):
        """ Generates a unique identifier using UUID4. """
        return str(uuid.uuid4())

    def generate_random_number_id(self, length=8):
        """ Generates a unique identifier using UUID4. """
        digits = '0123456789'
        random_id = ''.join(random.choice(digits) for _ in range(length))
        return int(random_id)

    def make_api_request(self, url, params=None, headers=None):
        """ makes simple api call """
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()  
            return response.json()  
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(
                "HTTP error occurred: %s, URL: %s, Params: %s, Headers: %s",
                http_err, url, params, headers, exc_info=True
            )
        except requests.exceptions.RequestException as req_err:
            self.logger.error(
                "Request error occurred: %s, URL: %s, Params: %s, Headers: %s",
                req_err, url, params, headers, exc_info=True
            )
        except Exception as err:
            self.logger.error(
                "An error occurred: %s, URL: %s, Params: %s, Headers: %s",
                err, url, params, headers, exc_info=True
            )

    def load_params_from_yaml(self, yaml_file, what):
        return None

# Binance Info Spot : Only need to get available symbols in both asyncio and normal method


class BinanceApiConfig:
    # api gtattattp pair for inverse(only basecoin like btcusd) and ysmbol for linear
    binance_api_spot_basepoint = "https://api.binance.com"
    binance_api_linear_basepoint = "https://fapi.binance.com"
    binance_api_inverse_basepoint = "https://dapi.binance.com"
    binance_api_option_basepoint = "https://eapi.binance.com"
    binance_api_endpoint = {
        "spot": {
            "info": "/api/v3/exchangeInfo",
            "depth": "/api/v3/depth",
            "24h_statistics": "/api/v3/ticker/24hr"
        },
        "linear": {
            "info": "/fapi/v1/exchangeInfo",
            "depth": "/fapi/v1/depth",
            "24h_statistics": "/fapi/v1/ticker/24hr",
            "funding": "/fapi/v1/fundingRate",
            "open_interest": "/fapi/v1/openInterest",
            "global_traders_accounts": "/fapi/v1/globalLongShortAccountRatio",
            "top_traders_positions": "/fapi/v1/topLongShortPositionRatio"
        },
        "inverse": {
            "info": "/dapi/v1/exchangeInfo",
            "depth": "/dapi/v1/depth",
            "24h_statistics": "/dapi/v1/ticker/24hr",
            "funding": "/dapi/v1/fundingRate",
            "open_interest": "/dapi/v1/openInterest",
            "global_traders_accounts": "/futures/data/globalLongShortAccountRatio",
            "top_traders_positions": "/futures/data/topLongShortPositionRatio",
            "top_traders_accounts": "/futures/data/topLongShortAccountRatio"
        },
        "option": {
            "info": "/eapi/v1/exchangeInfo",
            "24h_statistics": "/eapi/v1/ticker",
            "expiry_record": "/eapi/v1/exerciseHistory",
            "open_interest": "/eapi/v1/openInterest",
            "depth": "/eapi/v1/depth"
        }
    }

class BinanceInsights(BinanceApiConfig, Common_API_Methods):
    """ All the necessary information for inspecting available symbols, managing dynamic api and websockets"""
    
    def binance_get_spot_available_symbols(self):
        """ Retrives available symbols on binance exchange """
        url = self.binance_api_spot_basepoint + self.binance_api_endpoint.get("spot")
        data = self.make_api_request(url)
        return data

ins = BinanceInsights()

print(ins.binance_get_spot_available_symbols())
    
    # 



    # @classmethod
    # def binance_symbols_by_instType(cls, instType):
    #     """ 
    #         spot, perpetual, future, option
    #     """
    #     links = iterate_dict(cls.binance_info_url.get(instType))
    #     d = []
    #     for url in links:
    #         try:
    #             data = cls.simple_request(url).get("symbols")
    #             symbols = [d["symbol"] for d in data]
    #             d.append(symbols)
    #         except:
    #             data = cls.simple_request(url)
    #             symbols = [d["symbol"] for d in data["optionSymbols"]]
    #             d.append(symbols)
    #     d = unnest_list(d)
    #     if instType == "future":
    #         d = [symbol for symbol in d if re.search(r'_[0-9]+', symbol)]
    #     if instType == "perpetual":
    #         d = [symbol for symbol in d if not re.search(r'_[0-9]+', symbol)]
    #     return d
    
    # @classmethod
    # def binance_symbols(cls) -> dict:
    #     """
    #         spot, perpetual, future, option
    #     """
    #     di = {}
    #     for isntType in cls.binance_info_url.keys():
    #         data = cls.binance_symbols_by_instType(isntType)
    #         di[isntType] = data
    #     return di
    
    # @classmethod
    # def binance_info(cls, instType):
    #     """
    #         ex: perpetual.LinearPerpetual
    #     """
    #     url = recursive_dict_access(cls.binance_info_url, instType)
    #     info = cls.simple_request(url)
    #     if instType != "option":
    #         return info.get("symbols")
    #     else:
    #         return info
    
    # @classmethod
    # async def binance_get_option_instruments_by_underlying(cls, underlying_asset):
    #     symbols = []
    #     data = await cls.binance_info_async("option")
    #     for prefix, event, value in ijson.parse(data):
    #         if prefix == "optionSymbols.item.symbol":
    #             symbols.append(value)
    #     symbols = list(set([s.split("-")[1] for s in symbols if underlying_asset in s]))
    #     return symbols

    # @classmethod
    # async def binance_get_inverse_instruments_by_underlying(cls, underlying_asset):
    #     symbols = []
    #     data = await cls.binance_info_async("perpetual.InversePerpetual")
    #     for prefix, event, value in ijson.parse(data):
    #         if prefix == 'symbols.item.symbol' and underlying_asset in value:
    #             symbols.append(value)
    #     return symbols

    # @classmethod
    # async def binance_get_linear_instruments_by_underlying(cls, underlying_asset):
    #     symbols = []
    #     data = await cls.binance_info_async("perpetual.LinearPerpetual")
    #     for prefix, event, value in ijson.parse(data):
    #         if prefix == 'symbols.item.symbol' and underlying_asset in value:
    #             symbols.append(value)
    #     return symbols
    
    # @classmethod
    # async def binance_info_async(cls, instType):
    #     """
    #         ex: perpetual.LinearPerpetual
    #     """
    #     url = recursive_dict_access(cls.binance_info_url, instType)
    #     info = await cls.simple_request_async(url)
    #     return info







# class BinanceApiClient():
#     pass

# class binance_utilis(common_api_websockets_utilis):
    
#     # api gtattattp pair for inverse(only basecoin like btcusd) and ysmbol for linear
    
#     # websocket sends ping every 3 minutes
#     # websocket needs to recieve pong evry 10 minutes
#     # When you receive a ping, you must send a pong with a copy of ping's payload as soon as possible.
#     # Unsolicited pong frames are allowed, but will not prevent disconnection. It is recommended that the payload for these pong frames are empty.
#     # WebSocket connections have a limit of 5 incoming messages per second
#     # A single connection can listen to a maximum of 1024 streams.
#     # There is a limit of 300 connections per attempt every 5 minutes per IP.
    
#     ws_errors = [
#         {"code": 0, "msg": "Unknown property","id": %s},
#         {"code": 1, "msg": "Invalid value type: expected Boolean"},
#         {"code": 2, "msg": "Invalid request: property name must be a string"},
#         {"code": 2, "msg": "Invalid request: request ID must be an unsigned integer"},
#         {"code": 2, "msg": "Invalid request: unknown variant %s, expected one of SUBSCRIBE, UNSUBSCRIBE, LIST_SUBSCRIPTIONS, SET_PROPERTY, GET_PROPERTY at line 1 column 28"},
#         {"code": 2, "msg": "Invalid request: too many parameters"}
#         {"code": 2, "msg": "Invalid request: property name must be a string"}
#         {"code": 2, "msg": "Invalid request: missing field method at line 1 column 73"}
#         {"code": 3, "msg":"Invalid JSON: expected value at line %s column %s"}
        
#     ]
    
#     single_connection_valid_hours = 24

# # ws_endpoint:
# #   spot: wss://stream.binance.com:9443/ws
# #   linear: wss://fstream.binance.com/ws
# #   inverse: wss://dstream.binance.com/ws
# #   option: wss://nbstream.binance.com/eoptions/ws
    
#     spot = {
#         "trades" : "symbol@trade",
#         "depth" : "symbol@depth@100ms",
#     }
#     inverse_linear = {
#         "trades" : "symbol@trade",
#         "depth" : "symbol@depth@100ms",
#     }
    
    
#     def __init__(self):
#         self.ws_payload = None
#         self.ws_id = None
    
#     def create_ws_payload(self, *args):
#         """ creates payload for websocket connection """
#         params = list(*args)
#         self.ws_id = self.generate_random_number_id(10)
#         self.ws_payload = {
#         "method": "SUBSCRIBE",
#         "params": params,
#             "id": self.ws_id
#         }
    
#     def confirm_ws_connection(self, str_data : str):
#         """helper function to confirm connection succeeded"""
#         data = json.loads(str_data)
#         assert data.get("result") is None and data.get("id") == self.ws_id
    
#     def create_ws_unsubscribe_payload(self, *args):
#         """ *args are streams like btcusdt@trades"""
#         params = list(*args)
#         id_ = self.ws_id
#         payload = {
#             "method": "UNSUBSCRIBE",
#             "params": params,
#             "id": id_
#             }
#         return payload
    
#     def binance_list_subsciptions(self):
#         payload = {
#                 "method": "LIST_SUBSCRIPTIONS",
#                 "id": self.ws_id
#                 }
#         return payload

    

