import requests

class ExchangeAPIClient:

    def make_api_request(self, base_url, endpoint, repeat_response_code, max_retries, params=None, headers=None,):
        """
            if you recieved repeat_response_code, will try to fetch again with decreased parameters
        """
        url = base_url + endpoint
        for _ in range(max_retries):
            response = requests.get(url, params=params, headers=headers)
            if response.status_code == 200:
                return response.json()  
            else:
                print("Error:", response.status_code)
                return None

class BinanceAPIClient(ExchangeAPIClient):
    """
        Abstraction for binance API calls for depth, funding, oi, tta, ttp and gta
    """
    def __init__(self, instrument : str, insType : str, obj : str, maximum_retries : int = 10, books_dercemet : int = 500):
        """
            instrument : BTCUSDT ..
            insType : spot, mfuture, cfuture
            obj : depth, fundingm oi, tta, ttp, gta
            cInstruments : futures coin-c marginated instruments
            Maxium retries of an API with different parameters in case API call is impossible. Useful when you cant catch the limit
            books_dercemet : the derement of books length in case of api call being unsuccessful
        """
        self.instrument = instrument
        self.insType = insType
        self.obj = obj
        self.maximum_retries = maximum_retries
        self.books_dercemet = books_dercemet
        self.endpoints = {
                "spot" : "https://api.binance.com",
                "perp" : {
                    "mfutures" : "https://fapi.binance.com",
                    "cfutures" : "https://dapi.binance.com",
                }
            }
        self.basepoints = {
                "spot" : {
                    "depth" : "/api/v3/depth",
                },
                "perp" : {
                    "mfutures" : {
                        "depth" : "/fapi/v1/depth",
                        "funding" : "/fapi/v1/fundingRate",
                        "oi" : "/fapi/v1/openInterest",
                        "tta" : "/futures/data/topLongShortAccountRatio",
                        "ttp" : "/futures/data/topLongShortPositionRatio",
                        "gta" : "/futures/data/globalLongShortAccountRatio",
                    },
                    "cfutures" : {
                        "depth" : "/dapi/v1/depth",
                        "funding" : "/dapi/v1/fundingRate",
                        "oi" : "/dapi/v1/openInterest",
                        "tta" : "/futures/data/topLongShortAccountRatio",
                        "ttp" : "/futures/data/topLongShortPositionRatio",
                        "gta" : "/futures/data/globalLongShortAccountRatio",
                    },
                }
            }
        self.params = {
            "depth" : {
                    "symbol": {"type": str, "default": ""},
                    "limit": {"type": int, "default": 100}
                },
            "funding" : {
                    "symbol": {"type": str, "default": ""},
                    "limit": {"type": int, "default": 100}
                },
            "oi" : {
                    "symbol": {"type": str, "default": ""}
                },
            "tta_ttp_gta" : {
                "mfutures" : {
                    "symbol": {"type": str, "default": ""},
                    "period": {"type": str, "default": "5m"},
                    "limit": {"type": int, "default": 1},
                            },
                "cfutures" : {
                    "pair": {"type": str, "default": ""},
                    "period": {"type": str, "default": "5m"},
                    "limit": {"type": int, "default": 1},
                            },
            }
        }

    @classmethod
    def 
                for _ in range(maximum_retries):
                response = requests.get(url)
                response = response.json()
                if 'code' in response:    
                    if response.get('code', None) == -1130:
                        snaplength = snaplength - 500
                        url = "&".join([url, f"limit={snaplength}"])
                else:
                    break






APIendpoints = {
    "binance" : {
        "spot" : "https://api.binance.com",
        "perp" : {
            "mfutures" : "https://fapi.binance.com",
            "cfutures" : "https://dapi.binance.com",
        }
    },
    "kucoin" : {
        "spot" : "https://api.kucoin.com", 
        "perp" : "https://api-futures.kucoin.com",
    },
    "mexc" : {
        "spot" : "https://api.mexc.com", 
        "perp" : "https://contract.mexc.com",
    },
    "htx" : {
        "spot" : "https://api.huobi.pro",
        "perp" : "https://api.hbdm.com",
    },
    "bybit" :  "https://api.bybit.com",
    "coinbase" : "api.coinbase.com",
    "gateio" : "https://api.gateio.ws",
    "bitget" : "https://api.bitget.com",
    "deribit" : "wss://test.deribit.com",
    "bingx" : "https://open-api.bingx.com",
    "okx" : "https://www.okx.com",
}

APIbasepoints = {
    "binance" : {
        "spot" : {
            "depth" : "/api/v3/depth",
        },
        "perp" : {
            "mfutures" : {
                "depth" : "/fapi/v1/depth",
            },
            "cfutures" : {
                "depth" : "/dapi/v1/depth",

            },
        }
    },
    "kucoin" : {
        "spot" : "https://api.kucoin.com", 
        "perp" : "https://api-futures.kucoin.com",
    },
    "mexc" : {
        "spot" : "https://api.mexc.com", 
        "perp" : "https://contract.mexc.com",
    },
    "htx" : {
        "spot" : "https://api.huobi.pro",
        "perp" : "https://api.hbdm.com",
    },
    "bybit" :  {
        "depth" : "/v5/market/orderbook",
    },
    "coinbase" : "api.coinbase.com",
    "gateio" : "https://api.gateio.ws",
    "bitget" : "https://api.bitget.com",
    "deribit" : "wss://test.deribit.com",
    "bingx" : "https://open-api.bingx.com",
    "okx" : "https://www.okx.com",
}




APIparams = {
    "binance" : {
        "spot" : {
            "depth" : {
                "symbol" : "",
                "limit" : int("")
            }
        },
        "perp" : {
            "mfutures" : {
                "depth" : "/fapi/v1/depth"
            },
            "cfutures" : {
                "depth" : "/dapi/v1/depth",

            },
        }
    },
}