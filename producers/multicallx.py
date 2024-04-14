import asyncio
import rapidjson as json
import re
from utilis import *
from functools import partial

from clientpoints.binance import binance_instType_help
from clientpoints.okx import okx_api_instType_map


    
class binance_aoihttp_oioption_manager():

    def __init__ (self, underlying_asset, binance_get_option_expiries_method:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.expiries = []
        self.get_expiries = binance_get_option_expiries_method
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.container = DynamicFixedSizeList_binanceOptionOI([1, 2, 3], 10) #only for initialization
        self.pullTimeout = 1

    async def get_binance_instruments(self):
        try:
            expiries = await self.get_expiries(self.underlying_asset)
            self.expiries = expiries
            self.container.update_expiries(self.expiries)
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_binance_instruments())
            await task
            await asyncio.sleep(update_interval)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.container.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def helper(self, symbol, expiration, special_method):
        data = await self.fetcher("option", "oi", symbol=symbol, specialParam=expiration,  special_method=special_method)
        self.container.append(data)

    async def aiomethod(self):
        """
            BTC, ETH ...
            latency : seconds to wait before api call
        """
        tasks = []
        for expiration in self.expiries:
            tasks.append(self.helper(self.underlying_asset, expiration, "oioption"))
        await asyncio.gather(*tasks) 
    
class binance_aoihttp_posfutureperp_manager():
    """
        I after examining instruments related to BTC, ETHBTC instrument was present but its not suppoused to be. 
        So info API has some mistakes on binance side and it was fixed by filtering all of the symbols that doesnt contain USD
    """

    def __init__ (self, underlying_asset, info_linear:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.linear_symbols = []
        self.inverse_symbol = underlying_asset + "USD"
        self.info_linear_method = info_linear
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1

    async def get_binance_instruments(self):
        try:
            self.linear_symbols = await self.info_linear_method(self.underlying_asset)
            self.linear_symbols = [x for x in self.linear_symbols if self.underlying_asset in x and "USD" in  x]
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_binance_instruments())
            await task
            await asyncio.sleep(update_interval)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def helper_1(self, instType, objective, symbol):
        data = await self.fetcher(instType, objective, symbol=symbol, special_method="posfutureperp")
        if data == "[]" and symbol in self.linear_symbols:
            self.linear_symbols.remove(symbol)
        self.data[f"{symbol}_{objective}"] = data


    async def helper_2(self, instType, objective, coinm_symbol):
        data = await self.fetcher(instType, objective, symbol=coinm_symbol, special_method="posfutureperp")
        self.data[coinm_symbol+f"coinmAgg_{objective}"] = data

    async def aiomethod(self):
        tasks = []
        for symbol in self.linear_symbols:
            instType = "future" if bool(re.search(r'\d', symbol.split("_")[-1])) else "perpetual"
            for objective in ["tta", "ttp", "gta"]:
                marginType = binance_instType_help(symbol)
                symbol = symbol if marginType == "Linear" else symbol.replace("_", "").replace("PERP", "")
                tasks.append(self.helper_1(instType, objective, symbol))
        for objective in ["tta", "ttp", "gta"]:
            tasks.append(self.helper_2("perpetual", objective, self.inverse_symbol))
        await asyncio.gather(*tasks)

        keys = [f"{x}_{o}" for x in self.linear_symbols for o in ["tta", "ttp", "gta"]] + [self.inverse_symbol+f"coinmAgg_{o}" for o in ["tta", "ttp", "gta"]]
        for key in self.data.copy():
            if key not in keys:
                del self.data[key]
        print(self.data.keys())

class binance_aoihttp_oifutureperp_manager():

    def __init__ (self, underlying_asset, info_linear_method:callable, info_inverse_method:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.info_linear_method = info_linear_method
        self.info_inverse_method = info_inverse_method
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1
        self.linear_symbols = []
        self.inverse_symbols = []

    async def get_binance_instruments(self):
        try:
            self.linear_symbols = await self.info_linear_method(self.underlying_asset)
            self.linear_symbols = [x for x in self.linear_symbols if self.underlying_asset in x and "USD" in  x]
            self.inverse_symbols = await self.info_inverse_method(self.underlying_asset)
            self.inverse_symbols = [x for x in self.inverse_symbols if self.underlying_asset in x and "USD" in  x]  
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_binance_instruments())
            await task
            await asyncio.sleep(update_interval)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def helper(self, instType, symbol):
        data = await self.fetcher(instType, "oi", symbol=symbol, special_method="oifutureperp")
        if "code" not in data:
            self.data[f"{symbol}_{instType}"] = data
        else:
            if "USD" in symbol:
                self.inverse_symbols.remove(symbol)
            else:
                self.linear_symbols.remove(symbol)

    async def aiomethod(self):
        tasks = []
        for symbol in self.linear_symbols + self.inverse_symbols:
            instType = "future" if bool(re.search(r'\d', symbol.split("_")[-1])) else "perpetual"
            tasks.append(self.helper(instType, symbol))    
        await asyncio.gather(*tasks)

        all_symbols = self.linear_symbols + self.inverse_symbols

        for key in self.data.copy():
            if len([x for x in all_symbols if x in key]) == 0:
                del self.data[key]
        
class binance_aoihttp_fundperp_manager():

    def __init__ (self, underlying_asset, info_linear_method:callable, info_inverse_method:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.info_linear_method = info_linear_method
        self.info_inverse_method = info_inverse_method
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1
        self.linear_symbols = []
        self.inverse_symbols = []

    async def get_binance_instruments(self):
        try:
            self.linear_symbols = await self.info_linear_method(self.underlying_asset)
            self.linear_symbols = [x for x in self.linear_symbols if self.underlying_asset in x and "USD" in  x and bool(re.search(r'\d', x.split("_")[-1])) is False]
            self.inverse_symbols = await self.info_inverse_method(self.underlying_asset)
            self.inverse_symbols = [x for x in self.inverse_symbols if self.underlying_asset in x and "USD" in  x and bool(re.search(r'\d', x.split("_")[-1])) is False]  
        except Exception as e:
            print(f"Error fetching symbols: {e}")

    async def update_symbols(self, lag, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_binance_instruments())
            await task
            await asyncio.sleep(update_interval)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def fetch_fund_binance_yeye(self, instType, symbol):
        data = await self.fetcher(instType, "funding", symbol=symbol, special_method="fundperp")
        self.data[f"{symbol}_{instType}"] = data

    async def aiomethod(self):
        tasks = []
        for symbol in self.linear_symbols + self.inverse_symbols:
            instType = "future" if bool(re.search(r'\d', symbol.split("_")[-1])) else "perpetual"
            if not bool(re.search(r'\d', symbol.split("_")[-1])):
                tasks.append(self.fetch_fund_binance_yeye(instType, symbol))
        await asyncio.gather(*tasks)    

class bybit_aoihttp_oifutureperp_manager():

    def __init__ (self, underlying_asset, info_linear:callable, info_inverse:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_linear = []
        self.symbols_inverse = []
        self.info_linear = info_linear
        self.info_inverse = info_inverse
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1

    async def get_bybit_instruments(self):
        try:
            self.symbols_inverse = await self.info_inverse(self.underlying_asset)
            self.symbols_linear = await self.info_linear(self.underlying_asset)
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_bybit_instruments())
            await task
            await asyncio.sleep(update_interval)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def h1(self, instType, symbol):
        data = await self.fetcher(instType, "oi", symbol=symbol, special_method="oifutureperp")
        self.data[symbol] = data

    async def h2(self, instType, symbol):
        data = await self.fetcher(instType, "oi", symbol=symbol, special_method="oifutureperp")
        self.data[symbol] = data

    async def aiomethod(self):
        tasks = []
        for symbol in self.symbols_linear:
            instType = "future" if "-" in symbol else "perpetual"
            tasks.append(self.h1(instType, symbol))
        for symbol in self.symbols_inverse:
            instType = "future" if "-" in symbol else "perpetual"
            tasks.append(self.h2(instType, symbol))
        await asyncio.gather(*tasks)

        all_symbols = self.symbols_inverse + self.symbols_linear

        for key in self.data.copy():
            if len([x for x in all_symbols if x in key]) == 0:
                del self.data[key]
        
class bybit_aoihttp_posfutureperp_manager():

    def __init__ (self, underlying_asset, info_linear, info_inverse, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_linear = []
        self.symbols_inverse = []
        self.info_linear = info_linear
        self.info_inverse = info_inverse
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1

    async def get_bybit_instruments(self):
        try:
            self.symbols_inverse = await self.info_inverse(self.underlying_asset)
            self.symbols_linear = await self.info_linear(self.underlying_asset)
            self.symbols_inverse = [s for s in self.symbols_inverse if len(s.split("-")) == 1]
            self.symbols_linear = [s for s in self.symbols_linear if len(s.split("-")) == 1]
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_bybit_instruments())
            await task
            await asyncio.sleep(update_interval) 

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def h1(self, symbol, instType):
        data = await self.fetcher(instType, "gta", symbol=symbol, special_method="posfutureperp")
        self.data["Linear_"+symbol] = data

    async def h2(self, instType, symbol):
        data = await self.fetcher(instType, "gta", symbol=symbol, special_method="posfutureperp")
        self.data["Inverse_"+symbol] = data

    async def aiomethod(self):
        tasks = []
        for symbol in self.symbols_linear:
            symbol = symbol.replace("PERP", "USD") if "PERP" in symbol else symbol
            instType = "future" if "-" in symbol else "perpetual"
            tasks.append(self.h1(symbol, instType))
        for symbol in self.symbols_inverse:
            symbol = symbol.replace("PERP", "USD") if "PERP" in symbol else symbol
            instType = "future" if "-" in symbol else "perpetual"
            tasks.append(self.h2(instType, symbol))
        await asyncio.gather(*tasks)

        all_symbols = self.symbols_inverse + self.symbols_linear

        for key in self.data.copy():
            if len([x for x in all_symbols if x in key]) == 0:
                del self.data[key]
    
class bybit_aoihttp_fundperp_manager():

    def __init__ (self, underlying_asset, info_linear, info_inverse, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_linear = []
        self.symbols_inverse = []
        self.info_linear = info_linear
        self.info_inverse = info_inverse
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1

    async def get_bybit_instruments(self):
        try:
            self.symbols_inverse = await self.info_inverse(self.underlying_asset)
            self.symbols_linear = await self.info_linear(self.underlying_asset)
            self.symbols_inverse = [s for s in self.symbols_inverse if len(s.split("-")) == 1]
            self.symbols_linear = [s for s in self.symbols_linear if len(s.split("-")) == 1]
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_bybit_instruments())
            await task
            await asyncio.sleep(update_interval) 

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def h1(self, instType, symbol):
        data = await self.fetcher(instType, "funding", symbol=symbol, special_method="fundperp")
        self.data[symbol] = data

    async def aiomethod(self):
        tasks = []
        for symbol in self.symbols_linear + self.symbols_inverse:
            instType = "future" if "-" in symbol else "perpetual"
            if instType == "perpetual":
                tasks.append(self.h1(instType, symbol))
        await asyncio.gather(*tasks)

        for k, d in self.data.copy().items():
            if len(d) < 140:
                del self.data[k]
                self.symbols_linear = [item for item in self.symbols_linear if item != k]
                self.symbols_inverse = [item for item in self.symbols_inverse if item != k]
        
class okx_aoihttp_oifutureperp_manager():

    def __init__ (self, underlying_asset, info_perpetual:callable, info_future:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_future = []
        self.symbols_perpetual = []
        self.info_perpetual = info_perpetual
        self.info_future = info_future
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1
        self.symbols_perpetual = []
        self.symbols_future = []

    async def get_okx_instruments(self):
        try:
            self.symbols_future = await self.info_future(self.underlying_asset)
            self.symbols_perpetual = await self.info_perpetual(self.underlying_asset)
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag, update_time=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_okx_instruments())
            await task
            await asyncio.sleep(update_time)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def h1(self, instType, symbol):
        data = await self.fetcher(instType, "oi", symbol)
        self.data[symbol] = data

    async def aiomethod(self):
        tasks = []
        for s in self.symbols_perpetual:
            tasks.append(self.h1("perpetual", s))
        for s in self.symbols_future:
            tasks.append(self.h1("future", s))
        await asyncio.gather(*tasks)

        all_symbols = self.symbols_perpetual + self.symbols_future

        for key in self.data.copy():
            if len([x for x in all_symbols if x == key]) == 0:
                del self.data[key]

class okx_aoihttp_fundperp_manager():

    def __init__ (self, underlying_asset, info_perpetual:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_future = []
        self.symbols_perpetual = []
        self.info_perpetual = info_perpetual
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1
        self.symbols_perpetual = []
        self.symbols_future = []

    async def get_okx_instruments(self):
        try:
            self.symbols_perpetual = await self.info_perpetual(self.underlying_asset)
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_okx_instruments())
            await task
            await asyncio.sleep(update_interval)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def h1(self, symbol):
        response = await self.fetcher("perpetual", "funding", symbol)
        self.data[symbol] = response

    async def aiomethod(self):
        tasks = []
        for symbol in self.symbols_perpetual:
            tasks.append(self.h1(symbol))
        await asyncio.gather(*tasks)

        for key in self.data.copy():
            if len([x for x in self.symbols_perpetual if x == key]) == 0:
                del self.data[key]

class bitget_aoihttp_oifutureperp_manager():

    def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_perpetual = []
        self.info = info
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1


    async def get_bitget_perpetual_symbols(self):
        try:
            self.symbols_perpetual = await self.info(self.underlying_asset)
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_bitget_perpetual_symbols())
            await task
            await asyncio.sleep(update_interval)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def h1(self, symbol):
        data = await self.fetcher("perpetual", "oi", symbol=symbol, special_method="oifutureperp")
        self.data[symbol] = data

    async def aiomethod(self):
        tasks = []
        for margin in self.symbols_perpetual:
            for symbol in self.symbols_perpetual[margin]:
                tasks.append(self.h1(symbol))
        await asyncio.gather(*tasks)

class bitget_aoihttp_fundperp_manager():

    def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_perpetual = []
        self.info = info
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1


    async def get_bitget_perpetual_symbols(self):
        try:
            self.symbols_perpetual = await self.info(self.underlying_asset)
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_bitget_perpetual_symbols())
            await task
            await asyncio.sleep(update_interval)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def h1(self, symbol):
        data = await self.fetcher("perpetual", "funding", symbol=symbol, special_method="fundperp")
        self.data[symbol] = data

    async def aiomethod(self):
        tasks = []
        for margin in self.symbols_perpetual:
            for symbol in self.symbols_perpetual[margin]:
                tasks.append(self.h1(symbol))
        await asyncio.gather(*tasks)

        for key, funddata in self.data.copy().items():
            if "fundingRate" not in funddata:
                for symbol, perpsymb in self.symbols_perpetual.copy().items():
                    if key in perpsymb:
                        self.symbols_perpetual[symbol].remove(key)
                del self.data[key]


class gateio_aoihttp_fundperp_manager():

    def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_perpetual_inverse = []
        self.symbols_perpetual_linear = []
        self.symbols_future = []
        self.info = info
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1

    async def get_gateio_perpetual_inverse_symbols(self):
        try:
            self.symbols_perpetual_inverse = await self.info("perpetual.LinearPerpetual")
            self.symbols_perpetual_inverse = [x.get("name") for x in self.symbols_perpetual_inverse if self.underlying_asset in x.get("name")]
        except Exception as e:
            print(f"Error fetching symbols: {e}")

    async def get_gateio_perpetual_linear_symbols(self):
        try:
            self.symbols_perpetual_linear = await self.info("perpetual.InversePerpetual")
            self.symbols_perpetual_linear = [x.get("name") for x in self.symbols_perpetual_linear if self.underlying_asset in x.get("name")]
        except Exception as e:
            print(f"Error fetching symbols: {e}")

    
    async def update_symbols(self, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_gateio_perpetual_inverse_symbols())
            task_2 = asyncio.create_task(self.get_gateio_perpetual_linear_symbols())
            await task
            await task_2
            await asyncio.sleep(24* 60 * 60)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def h1(self, symbol):
        data = await self.fetcher("perpetual", "funding", symbol)
        if isinstance(data, str): 
            data = json.loads(data)
        self.data[f"{symbol}"] = data

    async def aiomethod(self):
        d = {}
        tasks = []
        for s in self.symbols_perpetual_linear:
            tasks.append(self.h1(s))
        for s in self.symbols_perpetual_inverse:
            tasks.append(self.h1(s))
        await asyncio.gather(*tasks)
        self.data = d

class gateio_aoihttp_oifutureperp_manager():

    def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_perpetual_inverse = []
        self.symbols_perpetual_linear = []
        self.symbols_future = []
        self.info = info
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1

    async def get_gateio_perpetual_inverse_symbols(self):
        try:
            self.symbols_perpetual_inverse = await self.info("perpetual.LinearPerpetual")
            self.symbols_perpetual_inverse = [x.get("name") for x in self.symbols_perpetual_inverse if self.underlying_asset in x.get("name")]
        except Exception as e:
            print(f"Error fetching symbols: {e}")

    async def get_gateio_perpetual_linear_symbols(self):
        try:
            self.symbols_perpetual_linear = await self.info("perpetual.InversePerpetual")
            self.symbols_perpetual_linear = [x.get("name") for x in self.symbols_perpetual_linear if self.underlying_asset in x.get("name")]
        except Exception as e:
            print(f"Error fetching symbols: {e}")

    async def get_gateio_future_symbols(self):
        try:
            self.symbols_future = await self.info("future.InverseFuture")
            self.symbols_future = [x.get("name") for x in self.symbols_future if self.underlying_asset in x.get("name")]
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_gateio_perpetual_inverse_symbols())
            task_2 = asyncio.create_task(self.get_gateio_perpetual_linear_symbols())
            task_3 = asyncio.create_task(self.get_gateio_future_symbols())
            await task
            await task_2
            await task_3
            await asyncio.sleep(24* 60 * 60)  


    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def gateio_positioning_useless_or_not(self, symbol, objective, didi, instType):
        data = await self.fetcher(instType, objective, symbol)
        if isinstance(data, str): 
            data = json.loads(data)
        didi[f"{symbol}"] = data
        
    async def aiomethod(self):
        d = {}
        tasks = []
        for sa in self.symbols_perpetual_linear:
            tasks.append(self.gateio_positioning_useless_or_not(sa, "oi", d, "perpetual"))
        for saa in self.symbols_perpetual_inverse:
            tasks.append(self.gateio_positioning_useless_or_not(saa, "oi", d, "perpetual"))
        for saaa in self.symbols_future:
            tasks.append(self.gateio_positioning_useless_or_not(saaa, "oi", d, "future"))
        await asyncio.gather(*tasks)        
        self.data = d

class gateio_aoihttp_posfutureperp_manager():

    def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_perpetual_inverse = []
        self.symbols_perpetual_linear = []
        self.info = info
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1

    async def get_gateio_perpetual_inverse_symbols(self):
        try:
            self.symbols_perpetual_inverse = await self.info("perpetual.LinearPerpetual")
            self.symbols_perpetual_inverse = [x.get("name") for x in self.symbols_perpetual_inverse if self.underlying_asset in x.get("name")]
        except Exception as e:
            print(f"Error fetching symbols: {e}")

    async def get_gateio_perpetual_linear_symbols(self):
        try:
            self.symbols_perpetual_linear = await self.info("perpetual.InversePerpetual")
            self.symbols_perpetual_linear = [x.get("name") for x in self.symbols_perpetual_linear if self.underlying_asset in x.get("name")]
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_gateio_perpetual_inverse_symbols())
            task_2 = asyncio.create_task(self.get_gateio_perpetual_linear_symbols())
            await task
            await task_2
            await asyncio.sleep(24* 60 * 60)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def gateio_positioning_useless_or_not(self, symbol, objective, didi):
        data = await self.fetcher("perpetual", objective, symbol)
        if isinstance(data, str): 
            data = json.loads(data)
        didi[f"{symbol}"] = data

    async def aiomethod(self):
        d = {}
        tasks = []
        for s in self.symbols_perpetual_linear:
            tasks.append(self.gateio_positioning_useless_or_not(s, "tta", d))
        for s in self.symbols_perpetual_inverse:
            tasks.append(self.gateio_positioning_useless_or_not(s, "tta", d))
        await asyncio.gather(*tasks)
        self.data = d

class htx_aiohttp_oifutureperp_manager():

    def __init__(self, underlying_asset, inverse_future_contract_types_htx, htx_aiohttpFetch):
        self.inverse_future_contract_types_htx = inverse_future_contract_types_htx
        self.htx_aiohttpFetch = htx_aiohttpFetch
        self.data = {}
        self.running = True
        self.pullTimeout = 1
        self.underlying_asset = underlying_asset

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def htx_fetch_oi_helper(self, instType, objective, underlying_asset, asset_specification, state_dictionary):
        response = await self.htx_aiohttpFetch(instType, objective, f"{underlying_asset}{asset_specification}")
        if isinstance(response, str):
            response = json.loads(response)        
        state_dictionary[f"{underlying_asset}{asset_specification}"] = response

    async def htx_fetch_oi_helper_2(self, instType, objective, underlying_asset, asset_specification, state_dictionary, ctype):
        response = await self.htx_aiohttpFetch(instType, objective, f"{underlying_asset}{asset_specification}", contract_type=ctype)
        if isinstance(response, str):
            response = json.loads(response)
        state_dictionary[f"{underlying_asset}{asset_specification}"] = response

    async def aiomethod(self):
        tasks = []
        tasks.append(self.htx_fetch_oi_helper("perpetual", "oiall", self.underlying_asset, "-USDT.LinearPerpetual", self.data))
        tasks.append(self.htx_fetch_oi_helper("perpetual", "oi", self.underlying_asset, "-USD", self.data))
        for ctype in self.inverse_future_contract_types_htx:
            tasks.append(self.htx_fetch_oi_helper_2("future", "oi", self.underlying_asset, ".InverseFuture", self.data, ctype))
        await asyncio.gather(*tasks)

class htx_aiohttp_fundperp_manager():

    def __init__(self, underlying_asset, inverse_future_contract_types_htx, htx_aiohttpFetch):
        self.inverse_future_contract_types_htx = inverse_future_contract_types_htx
        self.htx_aiohttpFetch = htx_aiohttpFetch
        self.data = {}
        self.running = True
        self.pullTimeout = 1
        self.underlying_asset = underlying_asset

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def htx_fetch_fundperp_helper(self, instType, objective, underlying_asset, asset_specification, state_dictionary, marginCoinCoinCoin):
        l = await self.htx_aiohttpFetch(instType, objective, f"{underlying_asset}{asset_specification}")
        if isinstance(l, str):
            l = json.loads(l)
        state_dictionary[marginCoinCoinCoin] = l

    async def aiomethod(self):
        tasks = []
        tasks.append(self.htx_fetch_fundperp_helper("perpetual", "funding", self.underlying_asset, "-USDT", self.data, "usdt"))
        tasks.append(self.htx_fetch_fundperp_helper("perpetual", "funding", self.underlying_asset, "-USD", self.data, "usd"))
        await asyncio.gather(*tasks)
    
class htx_aiohttp_posfutureperp_manager():

    def __init__(self, underlying_asset, inverse_future_contract_types_htx, htx_aiohttpFetch):
        self.inverse_future_contract_types_htx = inverse_future_contract_types_htx
        self.htx_aiohttpFetch = htx_aiohttpFetch
        self.data = {}
        self.running = True
        self.pullTimeout = 1
        self.underlying_asset = underlying_asset

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def htx_fetch_pos_helper(self, instType, objective, underlying_asset, ltype, state_dictionary):
        tta = await self.htx_aiohttpFetch(instType, objective, f"{underlying_asset}-{ltype}")
        if isinstance(tta, str):
            tta = json.loads(tta)
        state_dictionary[f"{underlying_asset}_{ltype}_{objective}"] = tta

    async def htx_fetch_pos_helper_2(self, instType, underlying_asset, obj, state_dictionary):
        tta = await self.htx_aiohttpFetch(instType, obj, f"{underlying_asset}.InverseFuture")
        if isinstance(tta, str):
            tta = json.loads(tta)
        state_dictionary[f"{underlying_asset}_InverseFuture_tta"] = tta
        
    async def aiomethod(self):
        tasks = []
        for ltype in ["USDT", "USD", "USDT-FUTURES"]:
            for obj in ["tta", "ttp"]:
                tasks.append(self.htx_fetch_pos_helper("perpetual", obj, self.underlying_asset, ltype, self.data))
        for obj in ["tta", "ttp"]:
            tasks.append(self.htx_fetch_pos_helper_2("future", self.underlying_asset, obj, self.data))
        await asyncio.gather(*tasks)

