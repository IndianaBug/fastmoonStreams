import asyncio
import rapidjson as json
import re
from utilis import unnest_list, DynamicFixedSizeList_binanceOptionOI
from functools import partial

from clientpoints.binance import binance_instType_help


    
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
    
    async def update_symbols(self, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_binance_instruments())
            await task
            await asyncio.sleep(24* 60 * 60)  

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
            self.symbols = await self.info_linear_method(self.underlying_asset)
            self.symbols = [x.get("symbol") for x in self.symbols if self.underlying_asset in x.get("symbol") and "USD" in  x.get("symbol")] 
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_binance_instruments())
            await task
            await asyncio.sleep(24* 60 * 60)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def helper_1(self, instType, objective, symbol):
        data = await self.fetcher(instType, objective, symbol=symbol, special_method="posfutureperp")
        self.data[f"{symbol}_{objective}"] = data

    async def helper_2(self, instType, objective, coinm_symbol):
        data = await self.fetcher(instType, objective, symbol=coinm_symbol, special_method="posfutureperp")
        self.data[coinm_symbol+f"coinmAgg_{objective}"] = data

    async def aiomethod(self):
        tasks = []
        for symbol in self.symbols:
            instType = "future" if bool(re.search(r'\d', symbol.split("_")[-1])) else "perpetual"
            for objective in ["tta", "ttp", "gta"]:
                marginType = binance_instType_help(symbol)
                symbol = symbol if marginType == "Linear" else symbol.replace("_", "").replace("PERP", "")
                tasks.append(self.helper_1(instType, objective, symbol))
        for objective in ["tta", "ttp", "gta"]:
            tasks.append(self.helper_2("perpetual", objective, self.inverse_symbol))
        await asyncio.gather(*tasks) 
        print(self.data) 

class binance_aoihttp_oifutureperp_manager():

    def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols = []
        self.info = info
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1

    async def get_binance_instruments(self):
        try:
            self.symbols = await self.info(self.underlying_asset)
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_binance_instruments())
            await task
            await asyncio.sleep(24* 60 * 60)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def helper(self, instType, symbol):
        data = await self.fetcher(instType, "oi", symbol=symbol, special_method="oifutureperp")
        if isinstance(data, str):
            data = json.loads(data)
        self.data[f"{symbol}_{instType}"] = data

    async def aiomethod(self):
        tasks = []
        for symbol in self.symbols:
            instType = "future" if bool(re.search(r'\d', symbol.split("_")[-1])) else "perpetual"
            tasks.append(self.helper(instType, symbol))    
        await asyncio.gather(*tasks)

class binance_aoihttp_fundperp_manager():

    def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols = []
        self.info = info
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1

    async def get_binance_instruments(self):
        try:
            self.symbols = await self.info(self.underlying_asset)
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_binance_instruments())
            await task
            await asyncio.sleep(24* 60 * 60)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def fetch_fund_binance_yeye(self, instType, symbol):
        data = await self.fetcher(instType, "funding", symbol=symbol, special_method="fundperp")
        if isinstance(data, str):
            data = json.loads(data)
        self.data[f"{symbol}_{instType}"] = data

    async def aiomethod(self):
        tasks = []
        for symbol in self.symbols:
            instType = "future" if bool(re.search(r'\d', symbol.split("_")[-1])) else "perpetual"
            if not bool(re.search(r'\d', symbol.split("_")[-1])):
                tasks.append(self.fetch_fund_binance_yeye(instType, symbol))
        await asyncio.gather(*tasks)    

class bybit_aoihttp_oifutureperp_manager():

    def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_linear = []
        self.symbols_inverse = []
        self.info = info
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1

    async def get_bybit_instruments_inverse(self):
        try:
            self.symbols_inverse = await self.info("Linear", self.underlying_asset)
        except Exception as e:
            print(f"Error fetching symbols: {e}")

    async def get_bybit_instruments_linear(self):
        try:
            self.symbols_linear = await self.info("Inverse", self.underlying_asset)
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_bybit_instruments_inverse())
            task_2 = asyncio.create_task(self.get_bybit_instruments_linear())
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

    async def h1(self, instType, symbol):
        data = await self.fetcher(instType, "oi", symbol=symbol, special_method="oifutureperp")
        if isinstance(data, str):
            data = json.loads(data)
        self.data[symbol] = data

    async def h2(self, instType, symbol):
        data = await self.fetcher(instType, "oi", symbol=symbol, special_method="oifutureperp")
        if isinstance(data, str):
            data = json.loads(data)
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
        
class bybit_aoihttp_posfutureperp_manager():

    def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_linear = []
        self.symbols_inverse = []
        self.info = info
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1

    async def get_bybit_instruments_inverse(self):
        try:
            self.symbols_inverse = await self.info("Linear", self.underlying_asset)
        except Exception as e:
            print(f"Error fetching symbols: {e}")

    async def get_bybit_instruments_linear(self):
        try:
            self.symbols_linear = await self.info("Inverse", self.underlying_asset)
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_bybit_instruments_inverse())
            task_2 = asyncio.create_task(self.get_bybit_instruments_linear())
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

    async def h1(self, symbol, instType):
        data = await self.fetcher(instType, "gta", symbol=symbol, special_method="posfutureperp")
        if isinstance(data, str):
            data = json.loads(data)
        self.data["Linear_"+symbol] = data

    async def h2(self, instType, symbol):
        data = await self.fetcher(instType, "gta", symbol=symbol, special_method="posfutureperp")
        if isinstance(data, str):
            data = json.loads(data)
        self.data["Inverse_"+symbol] = data

    async def aiomethod(self):
        tasks = []
        for symbol in self.symbols_linear:
            try:
                helper = any(char.isdigit() for char in symbol.split("-")[1])
            except:
                helper = False
            if helper is not True:
                symbol = symbol.replace("PERP", "USD") if "PERP" in symbol else symbol
                instType = "future" if "-" in symbol else "perpetual"
                tasks.append(self.h1(symbol, instType))
        for symbol in self.symbols_inverse:
            try:
                helper = any(char.isdigit() for char in symbol.split("-")[1])
            except:
                helper = None
            if helper is not True:  # unavailable for futures as of april2 2024
                symbol = symbol.replace("PERP", "USD") if "PERP" in symbol else symbol
                instType = "future" if "-" in symbol else "perpetual"
                tasks.append(self.h2(instType, symbol))
        await asyncio.gather(*tasks)
    
class bybit_aoihttp_fundperp_manager():

    def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_linear = []
        self.symbols_inverse = []
        self.info = info
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1

    async def get_bybit_instruments_inverse(self):
        try:
            self.symbols_inverse = await self.info("Linear", self.underlying_asset)
        except Exception as e:
            print(f"Error fetching symbols: {e}")

    async def get_bybit_instruments_linear(self):
        try:
            self.symbols_linear = await self.info("Inverse", self.underlying_asset)
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_bybit_instruments_inverse())
            task_2 = asyncio.create_task(self.get_bybit_instruments_linear())
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

    async def h1(self, instType, symbol):
        data = await self.fetcher(instType, "funding", symbol=symbol, special_method="fundperp")
        if isinstance(data, str):
            data = json.loads(data)
        self.data[symbol] = data

    async def aiomethod(self):
        tasks = []
        for symbol in self.symbols_linear + self.symbols_inverse:
            instType = "future" if "-" in symbol else "perpetual"
            if instType == "perpetual":
                tasks.append(self.h1(instType, symbol))
        await asyncio.gather(*tasks)

class okx_aoihttp_oifutureperp_manager():

    def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_future = []
        self.symbols_perpetual = []
        self.info = info
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1
        self.marginCoinsF = []
        self.marginCoinsF = []
        self.marginCoinsP = []
        self.marginCoinsP = []

    async def get_bybit_instruments_inverse(self):
        try:
            self.symbols_future = await self.info("future")
        except Exception as e:
            print(f"Error fetching symbols: {e}")

    async def get_bybit_instruments_linear(self):
        try:
            self.symbols_perpetual = await self.info("perpetual")
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_bybit_instruments_inverse())
            task_2 = asyncio.create_task(self.get_bybit_instruments_linear())
            await task
            await task_2
            self.marginCoinsF = [x for x in self.symbols_future if self.underlying_asset in x]
            self.marginCoinsF = list(set([x.split("-")[1] for x in self.marginCoinsF]))
            self.marginCoinsP = [x for x in self.symbols_perpetual if self.underlying_asset in x]
            self.marginCoinsP = list(set([x.split("-")[1] for x in self.marginCoinsP]))
            await asyncio.sleep(24* 60 * 60)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def h1(self, underlying_symbol, marginCoin):
        futures = await self.fetcher("future", "oi", f"{underlying_symbol}-{marginCoin}")
        if isinstance(futures, str):
            futures = json.loads(futures)
        else:
            pass
        self.data[f"future_{underlying_symbol}-{marginCoin}"] = futures

    async def h2(self, underlying_symbol, marginCoin):
        perp = await self.fetcher("perpetual", "oi", f"{underlying_symbol}-{marginCoin}")
        if isinstance(perp, str):
            perp = json.loads(perp)
        else:
            pass
        self.data[f"perpetual_{underlying_symbol}-{marginCoin}"] = perp

    async def aiomethod(self):
        tasks = []
        for marginCoin in self.marginCoinsF:
            tasks.append(self.h1(self.underlying_asset, marginCoin))
        for marginCoin in self.marginCoinsP:
            tasks.append(self.h2(self.underlying_asset, marginCoin))
        await asyncio.gather(*tasks)

class okx_aoihttp_fundperp_manager():

    def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_future = []
        self.symbols_perpetual = []
        self.info = info
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1

    async def get_okx_perpetual_symbols(self):
        try:
            self.symbols_perpetual = await self.info("perpetual")
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_okx_perpetual_symbols())
            await task
            await asyncio.sleep(24* 60 * 60)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def h1(self, symbol):
        response = await self.fetcher("perpetual", "funding", symbol)
        if isinstance(response, str):
            response = json.loads(response)
        self.data[symbol] = response

    async def aiomethod(self):
        symbols = [x for x in self.symbols_perpetual if self.underlying_asset in x]
        tasks = []
        for symbol in symbols:
            tasks.append(self.h1(symbol))
        await asyncio.gather(*tasks)

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
            self.symbols_perpetual = await self.info("perpetual")
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_bitget_perpetual_symbols())
            await task
            await asyncio.sleep(24* 60 * 60)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def h1(self, symbol):
        data = await self.fetcher("perpetual", "oi", symbol=symbol, special_method="oifutureperp")
        if isinstance(data, str):
            data = json.loads(data)
        else:
            pass
        self.data[symbol] = data

    async def aiomethod(self):
        symbols =  [x for x in self.symbols_perpetual if self.underlying_asset in x]
        tasks = []
        for symbol in symbols:
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
            self.symbols_perpetual = await self.info("perpetual")
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_bitget_perpetual_symbols())
            await task
            await asyncio.sleep(24* 60 * 60)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable, lag):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def h1(self, symbol):
        data = await self.fetcher("perpetual", "funding", symbol=symbol, special_method="fundfutureperp")
        if isinstance(data, str):
            data = json.loads(data)
        else:
            pass
        self.data[symbol] = data

    async def aiomethod(self):
        symbols =  [x for x in self.symbols_perpetual if self.underlying_asset in x]
        tasks = []
        for symbol in symbols:
            tasks.append(self.h1(symbol))
        await asyncio.gather(*tasks)

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

