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

        marginCoinsF = [x for x in self.symbols_future if self.underlying_asset in x]
        marginCoinsF = list(set([x.split("-")[1] for x in marginCoinsF]))
        marginCoinsP = [x for x in self.symbols_perpetual if self.underlying_asset in x]
        marginCoinsP = list(set([x.split("-")[1] for x in marginCoinsP]))
        data = {}
        tasks = []
        for marginCoin in marginCoinsF:
            async def okx_oioiioooo(underlying_symbol, marginCoin):
                futures = await self.fetcher("future", "oi", f"{underlying_symbol}-{marginCoin}")
                if isinstance(futures, str):
                    futures = json.loads(futures)
                else:
                    pass
                data[f"future_{underlying_symbol}-{marginCoin}"] = futures
            tasks.append(okx_oioiioooo(self.underlying_asset, marginCoin))
        for marginCoin in marginCoinsP:
            async def okx_oioiioooo_two(underlying_symbol, marginCoin):
                perp = await self.fetcher("perpetual", "oi", f"{underlying_symbol}-{marginCoin}")
                if isinstance(perp, str):
                    perp = json.loads(perp)
                else:
                    pass
                data[f"perpetual_{underlying_symbol}-{marginCoin}"] = perp
            tasks.append(okx_oioiioooo_two(self.underlying_asset, marginCoin))
        await asyncio.gather(*tasks)
        self.data = data

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
    
    async def update_symbols(self):
        while self.running:
            task = asyncio.create_task(self.get_okx_perpetual_symbols())
            await task
            await asyncio.sleep(24* 60 * 60)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable):
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def aiomethod(self):
        symbols = [x for x in self.symbols_perpetual if self.underlying_asset in x]
        data = {}
        tasks = []
        for symbol in symbols:
            async def okx_funding_for_silicone(symbol):
                response = await self.fetcher("perpetual", "funding", symbol)
                if isinstance(response, str):
                    response = json.loads(response)
                data[symbol] = response
            tasks.append(okx_funding_for_silicone(symbol))
        await asyncio.gather(*tasks)
        self.data = data

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
    
    async def update_symbols(self):
        while self.running:
            task = asyncio.create_task(self.get_bitget_perpetual_symbols())
            await task
            await asyncio.sleep(24* 60 * 60)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable):
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def aiomethod(self):
        symbols =  [x for x in self.symbols_perpetual if self.underlying_asset in x]
        full = {}
        tasks = []
        for symbol in symbols:
            async def bitget_kinda_good_but_not(symbol):
                data = await self.fetcher("perpetual", "oi", symbol=symbol, special_method="oifutureperp")
                if isinstance(data, str):
                    data = json.loads(data)
                else:
                    pass
                full[symbol] = data
            tasks.append(bitget_kinda_good_but_not(symbol))
        await asyncio.gather(*tasks)
        self.data = full

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
    
    async def update_symbols(self):
        while self.running:
            task = asyncio.create_task(self.get_bitget_perpetual_symbols())
            await task
            await asyncio.sleep(24* 60 * 60)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable):
        while self.running:
            task = asyncio.create_task(self.aiomethod())
            await task
            await insert_method(self.data, connection_data, on_message_method_api)
            await asyncio.sleep(self.pullTimeout)

    async def aiomethod(self):
        symbols =  [x for x in self.symbols_perpetual if self.underlying_asset in x]
        full = {}
        tasks = []
        for symbol in symbols:
            async def bitget_runs_by_a_woman_and_is_successful_lol(symbol):
                data = await self.fetcher("perpetual", "funding", symbol=symbol, special_method="fundfutureperp")
                if isinstance(data, str):
                    data = json.loads(data)
                else:
                    pass
                full[symbol] = data
            tasks.append(bitget_runs_by_a_woman_and_is_successful_lol(symbol))
        await asyncio.gather(*tasks)
        self.data = full

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

    
    async def update_symbols(self):
        while self.running:
            task = asyncio.create_task(self.get_gateio_perpetual_inverse_symbols())
            task_2 = asyncio.create_task(self.get_gateio_perpetual_linear_symbols())
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
        d = {}
        tasks = []
        async def gatefundplzfunme(symbol):
            data = await self.fetcher("perpetual", "funding", symbol)
            if isinstance(data, str): 
                data = json.loads(data)
            d[f"{symbol}"] = data
        for s in self.symbols_perpetual_linear:
            tasks.append(gatefundplzfunme(s))
        for s in self.symbols_perpetual_inverse:
            tasks.append(gatefundplzfunme(s))
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
    
    async def update_symbols(self):
        while self.running:
            task = asyncio.create_task(self.get_gateio_perpetual_inverse_symbols())
            task_2 = asyncio.create_task(self.get_gateio_perpetual_linear_symbols())
            task_3 = asyncio.create_task(self.get_gateio_future_symbols())
            await task
            await task_2
            await task_3
            await asyncio.sleep(24* 60 * 60)  


    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable):
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

class htx_aoihttp_posfutureperp_manager():


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
    
    async def update_symbols(self):
        while self.running:
            task = asyncio.create_task(self.get_gateio_perpetual_inverse_symbols())
            task_2 = asyncio.create_task(self.get_gateio_perpetual_linear_symbols())
            await task
            await task_2
            await asyncio.sleep(24* 60 * 60)  

    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable):
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
    
    async def update_symbols(self):
        while self.running:
            task = asyncio.create_task(self.get_gateio_perpetual_inverse_symbols())
            task_2 = asyncio.create_task(self.get_gateio_perpetual_linear_symbols())
            task_3 = asyncio.create_task(self.get_gateio_future_symbols())
            await task
            await task_2
            await task_3
            await asyncio.sleep(24* 60 * 60)  


    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable):
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

class htx_aoihttp_posfutureperp_manager():

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
    
    async def update_symbols(self):
        while self.running:
            task = asyncio.create_task(self.get_gateio_perpetual_inverse_symbols())
            task_2 = asyncio.create_task(self.get_gateio_perpetual_linear_symbols())
            task_3 = asyncio.create_task(self.get_gateio_future_symbols())
            await task
            await task_2
            await task_3
            await asyncio.sleep(24* 60 * 60)  


    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable):
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

class htx_aoihttp_fundperp_manager():

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
    
    async def update_symbols(self):
        while self.running:
            task = asyncio.create_task(self.get_gateio_perpetual_inverse_symbols())
            task_2 = asyncio.create_task(self.get_gateio_perpetual_linear_symbols())
            task_3 = asyncio.create_task(self.get_gateio_future_symbols())
            await task
            await task_2
            await task_3
            await asyncio.sleep(24* 60 * 60)  


    async def fetch_data(self, connection_data, on_message_method_api, insert_method:callable):
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