import asyncio
import json
import re
from utilis import unnest_list
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
        self.data = {}
        self.pullTimeout = 1

    async def get_binance_instruments(self):
        try:
            expiries = await self.get_expiries(self.underlying_asset)
            self.expiries = expiries
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self):
        while self.running:
            task = asyncio.create_task(self.get_binance_instruments())
            await task
            await asyncio.sleep(24* 60 * 60)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable):
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def aiomethod(self):
        """
            BTC, ETH ...
            latency : seconds to wait before api call
        """
        full = {}
        tasks = []
        for expiration in self.expiries:
            async def pos_optionoi_method(symbol, expiration):
                data = await self.fetcher("option", "oi", symbol=symbol, specialParam=expiration,  special_method="oioption")
                if isinstance(data, str):
                    data = json.loads(data)
                full[expiration] = unnest_list(data)
            tasks.append(pos_optionoi_method(self.underlying_asset, expiration))
        await asyncio.gather(*tasks) 
        self.data = full
    
class binance_aoihttp_posfutureperp_manager():

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
            self.symbols = await self.info("perpetual.LinearPerpetual")
            self.symbols = [x.get("symbol") for x in self.symbols if self.underlying_asset in x.get("symbol") and "USD" in  x.get("symbol")]
        except Exception as e:
            print(f"Error fetching symbols: {e}")
    
    async def update_symbols(self):
        while self.running:
            task = asyncio.create_task(self.get_binance_instruments())
            await task
            await asyncio.sleep(24* 60 * 60)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable):
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def aiomethod(self):
        """
            BTC, ETH ...
            latency : seconds to wait before api call
        """
        full = {}
        tasks = []
        for symbol in self.symbols:
            instType = "future" if bool(re.search(r'\d', symbol.split("_")[-1])) else "perpetual"
            for objective in ["tta", "ttp", "gta"]:
                marginType = binance_instType_help(symbol)
                symbol = symbol if marginType == "Linear" else symbol.replace("_", "").replace("PERP", "")
                async def pos_one_method(instType, objective, symbol):
                    data = await self.fetcher(instType, objective, symbol=symbol, special_method="posfutureperp")
                    if isinstance(data, str):
                        data = json.loads(data)
                    full[f"{symbol}_{objective}"] = data
                tasks.append(pos_one_method(instType, objective, symbol))
        coinm_symbol = self.underlying_asset + "USD"
        for objective in ["tta", "ttp", "gta"]:
            async def pos_two_method(instType, objective, coinm_symbol):
                data = await self.fetcher(instType, objective, symbol=coinm_symbol, special_method="posfutureperp")
                if isinstance(data, str):
                    data = json.loads(data)
                full[coinm_symbol+f"coinmAgg_{objective}"] = data
            tasks.append(pos_two_method("perpetual", objective, coinm_symbol))
        await asyncio.gather(*tasks)  
        self.data = full

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
    
    async def update_symbols(self):
        while self.running:
            task = asyncio.create_task(self.get_binance_instruments())
            await task
            await asyncio.sleep(24* 60 * 60)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable):
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def aiomethod(self):
        full = {}
        tasks = []
        for symbol in self.symbols:
            instType = "future" if bool(re.search(r'\d', symbol.split("_")[-1])) else "perpetual"
            async def fetch_oi_binance_yeye(instType, symbol):
                data = await self.fetcher(instType, "oi", symbol=symbol, special_method="oifutureperp")
                if isinstance(data, str):
                    data = json.loads(data)
                full[f"{symbol}_{instType}"] = data
            tasks.append(fetch_oi_binance_yeye(instType, symbol))    
        await asyncio.gather(*tasks)
        self.data = full

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
    
    async def update_symbols(self):
        while self.running:
            task = asyncio.create_task(self.get_binance_instruments())
            await task
            await asyncio.sleep(24* 60 * 60)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable):
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def aiomethod(self):
        full = {}
        tasks = []
        for symbol in self.symbols:
            instType = "future" if bool(re.search(r'\d', symbol.split("_")[-1])) else "perpetual"
            if not bool(re.search(r'\d', symbol.split("_")[-1])):
                async def fetch_fund_binance_yeye(instType, symbol):
                    data = await self.fetcher(instType, "funding", symbol=symbol, special_method="fundperp")
                    if isinstance(data, str):
                        data = json.loads(data)
                    full[f"{symbol}_{instType}"] = data
                tasks.append(fetch_fund_binance_yeye(instType, symbol))
        await asyncio.gather(*tasks)    
        self.data = full

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
    
    async def update_symbols(self):
        while self.running:
            task = asyncio.create_task(self.get_bybit_instruments_inverse())
            task_2 = asyncio.create_task(self.get_bybit_instruments_linear())
            await task
            await task_2
            await asyncio.sleep(24* 60 * 60)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable):
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def aiomethod(self):
        full = {}
        tasks = []
        for symbol in self.symbols_linear:
            instType = "future" if "-" in symbol else "perpetual"
            async def bybit_oi_async_hihi(instType, symbol):
                data = await self.fetcher(instType, "oi", symbol=symbol, special_method="oifutureperp")
                if isinstance(data, str):
                    data = json.loads(data)
                full[symbol] = data
            tasks.append(bybit_oi_async_hihi(instType, symbol))

        for symbol in self.symbols_inverse:
            instType = "future" if "-" in symbol else "perpetual"
            async def bybit_oi_async_hihihi(instType, symbol):
                data = await self.fetcher(instType, "oi", symbol=symbol, special_method="oifutureperp")
                if isinstance(data, str):
                    data = json.loads(data)
                full[symbol] = data
            tasks.append(bybit_oi_async_hihihi(instType, symbol))
        
        await asyncio.gather(*tasks)
        
        self.data = full

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
    
    async def update_symbols(self):
        while self.running:
            task = asyncio.create_task(self.get_bybit_instruments_inverse())
            task_2 = asyncio.create_task(self.get_bybit_instruments_linear())
            await task
            await task_2
            await asyncio.sleep(24* 60 * 60)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable):
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def aiomethod(self):
        full = {}
        tasks = []

        for symbol in self.symbols_linear:
            try:
                helper = any(char.isdigit() for char in symbol.split("-")[1])
            except:
                helper = False
            if helper is not True:  # unavailable for futures as of april2 2024
                symbol = symbol.replace("PERP", "USD") if "PERP" in symbol else symbol
                instType = "future" if "-" in symbol else "perpetual"
                async def boobs_position_one(symbol, instType):
                    data = await self.fetcher(instType, "gta", symbol=symbol, special_method="posfutureperp")
                    if isinstance(data, str):
                        data = json.loads(data)
                    full["Linear_"+symbol] = data
                tasks.append(boobs_position_one(symbol, instType))

        for symbol in self.symbols_inverse:
            try:
                helper = any(char.isdigit() for char in symbol.split("-")[1])
            except:
                helper = None
            if helper is not True:  # unavailable for futures as of april2 2024
                symbol = symbol.replace("PERP", "USD") if "PERP" in symbol else symbol
                instType = "future" if "-" in symbol else "perpetual"
                async def boobs_position_two(instType, symbol):
                    data = await self.fetcher(instType, "gta", symbol=symbol, special_method="posfutureperp")
                    if isinstance(data, str):
                        data = json.loads(data)
                    full["Inverse_"+symbol] = data
                tasks.append(boobs_position_two(instType, symbol))

        await asyncio.gather(*tasks)
        self.data =  full
    
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
    
    async def update_symbols(self):
        while self.running:
            task = asyncio.create_task(self.get_bybit_instruments_inverse())
            task_2 = asyncio.create_task(self.get_bybit_instruments_linear())
            await task
            await task_2
            await asyncio.sleep(24* 60 * 60)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable):
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def aiomethod(self):
        full = {}
        tasks = []
        for symbol in self.symbols_linear + self.symbols_inverse:
            instType = "future" if "-" in symbol else "perpetual"
            if instType == "perpetual":
                async def big_ass_funded(instType, symbol):
                    data = await self.fetcher(instType, "funding", symbol=symbol, special_method="fundperp")
                    if isinstance(data, str):
                        data = json.loads(data)
                    full[symbol] = data
                tasks.append(big_ass_funded(instType, symbol))
        await asyncio.gather(*tasks)
        self.data = full