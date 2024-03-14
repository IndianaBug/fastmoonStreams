import requests
import time
import json


class requestHandler():

    @classmethod
    def simple_request(cls, url):
        r = requests.get(url)
        print(r.status_code)
        r = r.json()
        return r

    @classmethod
    def request_with_headers(cls, url, headers, payload=""):
        r = requests.get(url, headers=headers, payload=payload)
        print(r.status_code)
        r = r.json()
        return r
    
class bybitInfo(requestHandler):
    bybit_info_url = {
                        "spot" : "https://api.bybit.com/v5/market/instruments-info?category=spot",
                        "perpetual" : {
                            "LinearPerpetual" : "https://api.bybit.com/v5/market/instruments-info?category=linear",
                            "InverseFutures" : "https://api.bybit.com/v5/market/instruments-info?category=inverse"
                        },
                        "future" : {
                            "LinearPerpetual" : "https://api.bybit.com/v5/market/instruments-info?category=linear",
                            "InverseFutures" : "https://api.bybit.com/v5/market/instruments-info?category=inverse"
                        },
                        "option" : "https://api.bybit.com/v5/market/instruments-info?category=option"
                    }
    bybit_call_example = {
                "spot" : "BTCUSDT",
                "perpetual" : {
                    "LinearPerpetual" : "BTCUSDT",
                    "LinearFutures" : "BTCUSD",
                },
                "future" : {
                    "InverseFutures" : "BTCUSD",
                    "InverseFutures" : "ETHUSDH24",
                },
                "option" : "ETH-3JAN23-1250-P"
            }

    @classmethod
    def symbols_by_instType(cls, isntType):
        """ 
            spot, perpetual, future, option
        """
        urls = cls.bybit_info_url.get(isntType)
        if isinstance(urls, dict):
            symbols_by_type = {}
            for productType, url in urls.items():
                data = cls.simple_request(url).get("result").get("list")
                symbols = [d.get("symbol")  for d in data if d.get("contractType") == productType]
                symbols_by_type[productType] = symbols
                time.sleep(1)
            return symbols_by_type
        else:
            data = cls.simple_request(urls).get("result").get("list")
            symbols = [d.get("symbol")  for d in data]
            return symbols
    
    @classmethod
    def symbols(cls) -> dict:
        """
            spot, perpetual, future, option
        """
        di = {

        }
        for isntType in cls.bybit_info_url.keys():
            data = cls.symbols_by_instType(isntType)
            di[isntType] = data
        return di


    # exchange_infos = {
    # "binance" : {
    #     "spot" : "https://api.binance.com/api/v1/exchangeInfo",
    #     "linear" : "https://fapi.binance.com/fapi/v1/exchangeInfo",
    #     "inverse" : "https://dapi.binance.com/dapi/v1/exchangeInfo",
    #     "option" : "https://eapi.binance.com/eapi/v1/exchangeInfo"
    # },

class binanceInfo(requestHandler):
    binance_info_url = {
                        "spot" : "https://api.binance.com/api/v3/exchangeInfo",
                        "perpetual" : {
                            "LinearPerpetual" : "https://fapi.binance.com/fapi/v1/exchangeInfo",
                            "InverseFutures" : "https://dapi.binance.com/dapi/v1/exchangeInfo"
                        },
                        "future" : {
                            "LinearPerpetual" : "https://fapi.binance.com/fapi/v1/exchangeInfo",
                            "InverseFutures" : "https://dapi.binance.com/dapi/v1/exchangeInfo"
                        },
                        "option" : "https://eapi.binance.com/eapi/v3/exchangeInfo"
                    }
    binance_call_example = {
                "spot" : "BTCUSDT",
                "perpetual" : {
                    "LinearPerpetual" : "BTCUSDT",
                    "InversePerpetual" : "BTCUSD",
                },
                "future" : {
                    "LinearFuture" : "BTCUSD",
                    "InverseFuture" : "ETHUSDH24",
                },
                "option" : "ETH-3JAN23-1250-P"
            }
    contract_typess = {
        "perpetual" : ['PERPETUAL', 'PERPETUAL DELIVERING'],
        "future" : ['CURRENT_QUARTER', 'NEXT_QUARTER']
    }

    @classmethod
    def contract_types(cls, isntType):
        urls = cls.binance_info_url.get(isntType)
        if isinstance(urls, dict):
            symbols_by_type = {}
            for productType, url in urls.items():
                data = cls.simple_request(url).get("symbols")
                symbols = set([d.get("contractType")  for d in data])
                symbols_by_type[productType] = symbols
                time.sleep(1)
            return symbols_by_type
        else:
            print("Options and spot have no different coin Margins")
    
    @classmethod
    def all_contract_type(cls):
        di = {}
        for isntType in cls.binance_info_url.keys():
            data = cls.contract_types(isntType)
            di[isntType] = data
        return di
    
    @classmethod
    def symbols_by_instType(cls, isntType):
        """ 
            spot, perpetual, future, option
        """
        urls = cls.binance_info_url.get(isntType)
        if isinstance(urls, dict):
            symbols_by_type = {}
            for productType, url in urls.items():
                data = cls.simple_request(url).get("symbols")
                symbols = [d.get("symbol")  for d in data if d.get("contractType") in cls.contract_typess.get(isntType)]
                symbols_by_type[productType] = symbols
                time.sleep(1)
            return symbols_by_type
        else:
            data = cls.simple_request(urls).get("symbols")
            symbols = [d.get("symbol")  for d in data]
            return symbols
    
    @classmethod
    def symbols(cls) -> dict:
        """
            spot, perpetual, future, option
        """
        di = {}
        for isntType in cls.binance_info_url.keys():
            data = cls.symbols_by_instType(isntType)
            di[isntType] = data
        return di

class okxInfo(requestHandler):

    okx_info_url = {  
        "spot" : "https://www.okx.com/api/v5/public/instruments?instType=SPOT",
        "perpetual" : "https://www.okx.com/api/v5/public/instruments?instType=SWAP",
        "futures" : "https://www.okx.com/api/v5/public/instruments?instType=FUTURES",
        "option" : "https://www.okx.com/api/v5/public/instruments?instType=OPTION&instFamily=BTC-USD",
    }
    okx_call_example = {
                "spot" : "BTCUSDT",
                "perpetual" : {
                    "LinearPerpetual" : 'BTC-USDT-SWAP',
                    "InverseFutures" : 'BTC-USD-SWAP',
                },
                "future" : {
                    "LinearPerpetual" : "BTC-USD-240315",
                    "InverseFutures" : "BTC-USD-240315",
                },
                "option" : "BTC-USD-241227-30000-P"
            }

    @classmethod
    def symbols_by_instType(cls, isntType):
        """ 
            spot, perpetual, future, option
        """
        urls = cls.okx_info_url.get(isntType)
        data = cls.simple_request(urls).get("data")
        symbols = [d["instId"] for d in data]
        return symbols
    
    @classmethod
    def symbols(cls) -> dict:
        """
            spot, perpetual, future, option
        """
        di = {

        }
        for isntType in cls.okx_info_url.keys():
            data = cls.symbols_by_instType(isntType)
            di[isntType] = data
        return di

class kucoinInfo(requestHandler):
    endpoints = {  
        "spot" : "https://api.kucoin.com",   
        "perpetual" : "https://api-futures.kucoin.com",  
    }
    basepoints = {  
        "spot" : "/api/v2/symbols",    
        "perpetual" : "/api/v1/contracts/active",  
    }
    params = {}
    kucoin_call_example = {
                "spot" : "BTC-USDT",
                "perpetual" : "XBTUSDTM"
            }

    @classmethod
    def symbols_by_instType(cls, isntType):
        """ 
            spot, perpetual, future, option
        """
        endpoint = cls.endpoints.get(isntType)
        basepoint = cls.basepoints.get(isntType)
        url = endpoint + basepoint
        r = cls.simple_request(url)
        data = r.get("data")
        symbols = [d["symbol"] for d in data]
        return symbols
    
    @classmethod
    def symbols(cls) -> dict:
        """
            spot, perpetual, future, option
        """
        di = {

        }
        for isntType in cls.kucoin_call_example.keys():
            data = cls.symbols_by_instType(isntType)
            di[isntType] = data
        return di
    
class bitgetInfo(requestHandler):

    bitget_info_url = {  
        "spot" : "https://api.bitget.com/api/v2/spot/public/symbols",
        "perpetual" : {
            "LinearPerpetual" : {
                "usdt" : "https://api.bitget.com/api/v2/mix/market/tickers?productType=USDT-FUTURES",
                "usdc" : "https://api.bitget.com/api/v2/mix/market/tickers?productType=USDC-FUTURES",
            },
            "InverseFutures" : "https://api.bitget.com/api/v2/mix/market/tickers?productType=COIN-FUTURES"
        } 
    }
    okx_call_example = {
                "spot" : "BTCUSDT",
                "perpetual" : {
                    "LinearPerpetual" : 'BTCUSDT',
                    "InverseFutures" : 'BTC-USD-SWAP',
                },
                "future" : {
                    "LinearPerpetual" : "BTC-USD-240329",
                    "InverseFutures" : "BTC-USD-240315",
                },
                "option" : "BTC-USD-241227-30000-P"
            }

    @classmethod
    def symbols_by_instType(cls, isntType):
        """ 
            spot, perpetua
        """
        urls = cls.bitget_info_url.get(isntType)
        data = cls.simple_request(urls).get("data")
        return [d["symbol"] for d in data]
    
    @classmethod
    def symbols(cls) -> dict:
        """
            spot, perpetual, future, option
        """
        di = {

        }
        for isntType in cls.okx_info_url.keys():
            data = cls.symbols_by_instType(isntType)
            di[isntType] = data
        return di

# print(kucoinInfo.symbols())

print(bitgetInfo.symbols_by_instType("futures"))