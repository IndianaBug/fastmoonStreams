from OriginHub.ExchangeGateway import *
from consumers import on_message, flow

class ExchangeAPIClient():
    """ 
    This class encompasses aiohttp and websockets methods for interacting with exchanges. 
    It inherits from ExchangeAPIClient which combines methods from all ofo the exchanges
    """
    def __init__(self, api_coinbase, secret_coinbase, api_kucoin, secret_kucoin, pass_kucoin, on_message_kwargs=None):
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
        self.onm = on_message.on_message(**on_message_kwargs) if on_message_kwargs != None else on_message.on_message()

    def build_connection_data_test(self, wss={}, apis={}):
        d = []
        for exchange in wss:
            for ws in wss[exchange]:
                try:
                    connData = self.get_method_connData("ws", exchange, ws)
                except:
                    connData = exchange + " " + ws +" is fucked"
                d.append(connData)
        for exchange in apis:
            for api in apis[exchange]:
                try:
                    connData = self.get_method_connData("api", exchange, api)
                except Exception as e:
                    print(exchange + " " + api +" is fucked")
                    connData = exchange + " " + api +" is fucked"
                d.append(connData)
        return d



    def build_connection_data(self, wss={}, apis={}):
        d = []
        for exchange in wss:
            for ws in wss[exchange]:
                connData = self.get_method_connData("ws", exchange, ws)
                meth = self.populate_with_on_message(connData.get("id_ws"))
                connData["on_message_method_ws"] = meth
                if "id_api_2" in connData:
                    meth = self.populate_with_on_message(connData.get("id_api_2"))
                    connData["on_message_method_api_2"] = meth
                d.append(connData)
        for exchange in apis:
            for api in apis[exchange]:
                connData = self.get_method_connData("api", exchange, api)
                meth = self.populate_with_on_message(connData.get("id_api"))
                connData["on_message_method_api"] = meth
                d.append(connData)
        return d
    
    def get_method_connData(self, type_, exchange, connStr):
        """
            type : ws, api
        """
        method_str = f"{exchange}_build_{type_}_connectionData"
        function = getattr(self, method_str)
        connStr = connStr.split(".")
        instType = connStr.pop(0)
        objective = connStr.pop(0)

        derivate_smd = {
            "oi" : "oifutureperp",
            "gta" : "posfutureperp",
            "tta" : "posfutureperp",
            "funding" : "fundperp",
        }
        special_methods = {
            "perpetual" : derivate_smd,
            "future" : derivate_smd,
            "option" : {
                "oi" : "oioption"
            }
        }
        
        needSnap = True if "snap" in connStr else False
        if needSnap:
            connStr.pop(connStr.index("snap"))

        special_method = special_methods.get(instType).get(objective) if "spec" in connStr else ""
        if special_method:
            connStr.pop(connStr.index("spec"))
        
        pullTimeout = next((int(st) for st in connStr if st.isdigit()), None)
        if pullTimeout is not None:
            connStr.remove(str(pullTimeout))
            
        symbols = connStr
        instTypes = [instType for _ in range(len(symbols))]
        objectives = [objective for _ in range(len(symbols))]

        if type_ == "ws":
            return  function(instTypes, objectives, symbols, needSnap)
        if type_ == "api":
            return  function(instTypes[0], objectives[0], symbols[0], pullTimeout, special_method)
        
        
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
        return merged_dict

    def populate_with_on_message(self, id):
        on_methods = self.onm.get_methods()
        idlist = id.split("_")[:-1]
        # print(on_methods)
        for method in on_methods:
            for ident in idlist:
                if ident in method:
                    T = True
                if ident not in method:
                    T = False
                    break
                if ident == idlist[-1] and T == True:
                    return getattr(self.onm, method)
                
    def populate_with_flow(self, id_):
        if "depth" in id_:
            return flow.booksflow
        if "trades" in id_:
            return flow.tradesflow
        if "option" in id_ and "oi" in id_:
            return flow.Ooiflow
        if "oi" in _id and "opiton" not in id_:
            return flow.oiflow
        if "liquidations" in id_:
            return flow.liquidationsflow
            
            

# c = ExchangeAPIClient("", "", "", "", "")

# print(c.populate_with_on_message("okx_ws_spot_depth_btcusdt"))