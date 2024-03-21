coinbaseSecret = '-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIDOVctxJpAI/hHtbUN9VrHej4bWPRuT9um9FoBlTgiyaoAoGCCqGSM49\nAwEHoUQDQgAEJt8JWIh8CHm045POImBF0ZvVuX5FbQjIDhIT82hE5r1+vb8cSQ3M\nfEjriBy1/ZD3EywPNxyGe6nO/Wsq0M8hXQ==\n-----END EC PRIVATE KEY-----\n'
coinbaseAPI = 'organizations/b6a02fc1-cbb0-4658-8bb2-702437518d70/apiKeys/697a8516-f2e2-4ec9-a593-464338d96f21'
import re
from typing import List, Union
from exchangeinfo import *
from utilis import filter_nested_dict

class infoexchange(
    binanceInfo, bybitInfo, okxInfo, kucoinInfo,
    bitgetInfo, bingxInfo, mexcInfo, deribitInfo, 
    coinbaseInfo, htxInfo, gateioInfo
    ):
    """
        Coinbase have completely different sybols for futures
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exchanges = ["binance", "okx", "bybit", "htx", "coinbase", "deribit", "bitget", "bingx", "gateio", "kucoin", "mexc"]

    
    def get_methods(self):
        return [method for method in dir(self) if callable(getattr(self, method)) and not method.startswith("__")]

    def retrieve_all_instruments(self):
        print("Please wait 30 seconds untill the lates data is fetched.")
        pattern = r'^\w+_symbols$'
        methods = self.get_methods()
        functions_names = [method for method in methods if re.match(pattern, method)]
        functions = [getattr(self, method) for method in functions_names]
        data = {}
        for key, itme in zip(functions, functions_names):
            try:
                data[itme.split("_")[0]] = key()
            except:
                print(f"Unfortunatelly, all instruments of {itme.split('_')[0]} are unavailable due to code error, refactor the code")
        return data
    
    @classmethod
    def filter_nested_dict(cls, nested_dict, condition):
        for key, value in nested_dict.items():
            if isinstance(value, dict):
                nested_dict[key] = filter_nested_dict(value, condition)
            elif isinstance(value, list):
                nested_dict[key] = [item for item in value if condition(item)]
        return nested_dict
    
    @classmethod
    def delete_keys_with_name(cls, dictionary, name):
        if isinstance(dictionary, dict):
            for key, value in list(dictionary.items()):
                if key == name:
                    del dictionary[key]
                elif isinstance(value, dict):
                    cls.delete_keys_with_name(value, name)
                elif isinstance(value, list):
                    for item in value:
                        cls.delete_keys_with_name(item, name)
        return dictionary

    def retry_related_instruments(self, data, basecoin, quote, omit_insdtType: Union[List[str], str] = None, *args):
        def basecoin_condition(string):
            return basecoin in string.lower()
        filtered_data = self.filter_nested_dict(data, basecoin_condition)
        def quote_condition(string):
            return quote in string.lower()
        filtered_data = self.filter_nested_dict(data, quote_condition)
        if omit_insdtType != None:
            if isinstance(omit_insdtType, str):
                filtered_data = self.delete_keys_with_name(filtered_data, omit_insdtType)
            else:
                for insType in omit_insdtType:
                    filtered_data = self.delete_keys_with_name(filtered_data, insType)
        filtered_data = {key: value for key, value in data.items() if any(value.values())}
        return filtered_data
    
    def get_related_instruments(self, basecoin, quote, omit_insdtType: Union[List[str], str] = None, *args):
        data = self.retrieve_all_instruments()
        filtered_data = self.retry_related_instruments(data, basecoin, quote, omit_insdtType)
        exchange_by_instrument_type = {}
        for exchange, instruments in filtered_data.items():
            for instrument_type, instrument_list in instruments.items():
                for instrument in instrument_list:
                    if instrument_type not in exchange_by_instrument_type:
                        exchange_by_instrument_type[instrument_type] = {}
                    if exchange not in exchange_by_instrument_type[instrument_type]:
                        exchange_by_instrument_type[instrument_type][exchange] = []
                    exchange_by_instrument_type[instrument_type][exchange].append(instrument)
        for instrument_type, exchanges in exchange_by_instrument_type.items():
            print(f'Instrument Type: {instrument_type}')
            for exchange, instruments in exchanges.items():
                print(f'\tExchange: {exchange}')
                print(f'\t\tInstruments: {", ".join(instruments)}')


info = infoexchange(coinbaseAPI, coinbaseSecret)
a = info.gateio_symbols_by_instType("option")


print(a)