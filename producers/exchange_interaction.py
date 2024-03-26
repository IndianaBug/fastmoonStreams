from clients import *


class ExchangeAPIClient():
    """ 
    This class encompasses aiohttp and websockets methods for interacting with exchanges. 
    It inherits from ExchangeAPIClient which combines methods from all ofo the exchanges
    """
    def __init__(self, api_coinbase, secret_coinbase, api_kucoin, secret_kucoin, pass_kucoin):
        self.exchanges = {
            "binance" : binance(),
            "bybit" : bybit(),
            "okx" : okx(),
            "coinbase" : coinbase(api_coinbase, secret_coinbase),
            "kucoin" : kucoin(api_kucoin, secret_kucoin, pass_kucoin),
            "bingx" : bingx(),
            "bitget" : bitget(),
            "deribit" : deribit(),
            "htx" : htx(),
            "mexc" : mexc(),
            "gateio" : gateio(),
        }
        for exchange, client in self.exchanges.items():
            for method_name in dir(client):
                if not method_name.startswith("__") and callable(getattr(client, method_name)):
                    setattr(self, method_name, getattr(client, method_name))
    
    def get_method_of_exchnage(self, type_, exchange, connStr):
        """
            type : ws, api
        """
        method_str = f"{exchange}_build_{type_}_connectionData"
        function = getattr(self, method_str)
        connStr = connStr.split(".")
        instType = connStr.pop(0)
        needSnap = True if connStr.pop(connStr.index("snap"))=="snap" else False
        special_method = True if connStr.pop(connStr.index("spec"))=="spec" else False
        objective = connStr.pop(1)
        symbols = 
        
        
                    
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
            data[itme.split("_")[0]] = key()
        return data
    
    @classmethod
    def get_related_instruments(cls, data, filter_conditions_1, filter_conditions_2, keys_to_remove):
        count=-1
        d = {}
        for f1, f2 in zip(filter_conditions_1, filter_conditions_2):
            count+=1
            filter_condition_1 = lambda x: f1 in x  
            filter_condition_2 = lambda x: f2 in x       
            keys_to_remove = keys_to_remove
            filtered_data = {
                key: {
                    sub_key: [item for item in sub_dict if filter_condition_1(item) and filter_condition_2(item)]
                    for sub_key, sub_dict in inner_dict.items() if sub_key not in keys_to_remove
                }
                for key, inner_dict in data.items()
            }
            filtered_data = {key: {sub_key: sub_dict for sub_key, sub_dict in inner_dict.items() if sub_dict} 
                            for key, inner_dict in filtered_data.items()}
            d[count] = filtered_data
            
        merged_dict = {}

        for d in [d[0], d[1], d[2]]:
            for key, value in d.items():
                if key not in merged_dict:
                    merged_dict[key] = value
                else:
                    for sub_key, sub_value in value.items():
                        if sub_key not in merged_dict[key]:
                            merged_dict[key][sub_key] = sub_value
                        else:
                            merged_dict[key][sub_key] += sub_value
        print(json.dumps(merged_dict, indent=4))
        return merged_dict
