coinbaseSecret = '-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIDOVctxJpAI/hHtbUN9VrHej4bWPRuT9um9FoBlTgiyaoAoGCCqGSM49\nAwEHoUQDQgAEJt8JWIh8CHm045POImBF0ZvVuX5FbQjIDhIT82hE5r1+vb8cSQ3M\nfEjriBy1/ZD3EywPNxyGe6nO/Wsq0M8hXQ==\n-----END EC PRIVATE KEY-----\n'
coinbaseAPI = 'organizations/b6a02fc1-cbb0-4658-8bb2-702437518d70/apiKeys/697a8516-f2e2-4ec9-a593-464338d96f21'
import re

from infoByExchnage import *


class infoexchange(
    binanceInfo, bybitInfo, okxInfo, kucoinInfo,
    bitgetInfo, bingxInfo, mexcInfo, deribitInfo, 
    coinbaseInfo, htxInfo, # gateioInfo
    ):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exchanges = ["binance", "okx", "bybit", "htx", "coinbase", "deribit", "bitget", "bingx", "gateio", "kucoin", "mexc"]

    
    def get_methods(self):
        return [method for method in dir(self) if callable(getattr(self, method)) and not method.startswith("__")]

    def retrieve_related_instruments(self, keyword):
        pattern = r'^\w+_symbols$'
        methods = self.get_methods()
        functions_names = [method for method in methods if re.match(pattern, method)]
        functions = [getattr(self, method) for method in functions_names]
        data = {}
        for key, itme in zip(functions, functions_names):
            try:
                data[itme] = key()
            except:
                print(itme)
        # data = {name : f() for f, name in zip(functions, functions_names)}
        return data

info = infoexchange(coinbaseAPI, coinbaseSecret)
a = info.retrieve_related_instruments("a")
info.coinbase_symbols()

# file_path = "C:\coding\SatoshiVault\producers"
# with open(file_path, "w") as json_file:
#     json.dump(a, json_file, indent=4)
