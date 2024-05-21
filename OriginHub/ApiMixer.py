import asyncio
import re
from .utilis import *
from .clientpoints_.binance import binance_instType_help
from typing import Callable, Any
import sys
from logging.handlers import RotatingFileHandler
import backoff
from .errors import aiohttp_recoverable_errors 
from pathlib import Path
import time
from functools import wraps, partial
base_path = Path(__file__).parent.parent
log_file_bytes = 10*1024*1024,
log_file_backup_count = 5,

class logger_instance():
    """ omit """
    def exception(self, *args, **kwargs):
        pass

class CommonFunctionality:
    
    """ Common functionalities class betweem apimixers"""
    
    def __init__(self, underlying_asset="BTC", connection_data={}, max_reconnect_retries=8, fetcher:callable=lambda:0, send_message_to_topic:callable=lambda x,y:0):
        
        self.underlying_asset = underlying_asset
        self.max_reconnect_retries = max_reconnect_retries
        self.connection_data = connection_data
        self.underlying_asset = ""
        self.fetcher = fetcher
        self.send_message_to_topic = send_message_to_topic
        self.logger = logger_instance()

        self._instruments_to_remove = {"option":[], "linear":[], "inverse":[], "perpetual":[], "future":[]}
        self._instruments_to_add = {"option":[], "linear":[], "inverse":[], "perpetual":[], "future":[]}
        self._instruments = {"option":[], "linear":[], "inverse":[], "perpetual":[], "future":[]}
        self._objectives = []
        self._tasks = {}
        self.running = {"coroutine_orchestrator" : False, "calibrate_instruments" : False}

        
        
    def start_orchestrator(self):
        """ starts caroutins """
        self.running["coroutine_orchestrator"] = True
        
    def stop_orchestrator(self):
        """ stops caroutines """
        self.running["coroutine_orchestrator"] = False
    
    async def _hault_orchestrator_coroutine(self):
        """ stops caroutines """
        self.running["coroutine_orchestrator"] = False
        task_to_remove =  self._tasks.get("coroutine_orchestrator", None)
        task_to_remove.cancel()
        try:
            await task_to_remove
        except asyncio.CancelledError as e:
            self.logger.exception("Couldn't cancel caroutine of %s, message: %s", "coroutine_orchestrator", e, exc_info=True)
        del self._tasks["coroutine_orchestrator"]
        
    def _start_coroutine(self, id_instrument):
        """ starts caroutins """
        self.running[id_instrument] = True
        
    def _stop_coroutine(self, id_instrument):
        """ stops caroutines """
        self.running[id_instrument] = False
        
    async def _hault_coroutine(self, id_instrument):
        """ stops caroutines """
        self.running[id_instrument] = False
        task_to_remove =  self._tasks.get(id_instrument, None)
        task_to_remove.cancel()
        try:
            await task_to_remove
        except asyncio.CancelledError as e:
            self.logger.exception("Couldn't cancel caroutine of %s, message: %s", id_instrument, e, exc_info=True)
        del self._tasks[id_instrument]
                
    @staticmethod
    def errors_aiohttp(func):
        """ logs errors of a single aiohttp method"""
        @wraps(func)
        async def inner_wrapper_task_generator(self, *args, **kwargs):
            id_ = self.connection_data.get("id")
            try:
                return await func(self, *args, **kwargs)
            except asyncio.TimeoutError as e:
                self.logger.exception("Couldnt create tasks, Unexpected error in %s, %s, error message:%s", func.__name__, id_, e)
            except asyncio.CancelledError as e:
                self.logger.exception("Operation was cancelled %s, %s, error message:%s", func.__name__, id_, e)
            except ValueError as e:
                self.logger.exception("ValueError in %s, %s, error message:%s", func.__name__, id_, e)
            except KeyError as e:
                self.logger.exception("KeyError in %s, %s, error message:%s", func.__name__, id_, e)
            except ConnectionError as e:
                self.logger.exception(f"ConnectionError in {func.__name__}: {e}")
                self.logger.exception("ConnectionError, error message:%s",  e)
            except IndexError as e:
                self.logger.exception("IndexError in %s, %s, error message:%s", func.__name__, id_, e)
            except TypeError as e:
                self.logger.exception("TypeError in  %s, %s, error message:%s", func.__name__, id_, e)
            except AttributeError as e:
                self.logger.exception("AttributeError in %s, %s, error message:%s", func.__name__, id_, e)
            except RuntimeError as e:
                self.logger.exception("RuntimeError in %s, %s, error message:%s", func.__name__, id_, e)
            except Exception as e:
                self.logger.exception("Operation was cancelled %s, %s, error message:%s", func.__name__, id_, e)
                raise
        return inner_wrapper_task_generator

    @staticmethod
    def backoff_exception_(func):
        """ 
            wrapper for aiohttp tasks
            necessary attributes must be passed from SupplyEngine class
        """
        @wraps(func)
        async def inner_coroutine_manager(self, *args, **kwargs):
            connection_start_time = time.time()
            id_api = self.connection_data.get("id_api")
            try:
                await func(self, *args, **kwargs) # inside must be infinite iterator
            except aiohttp_recoverable_errors as e:
                self.logger.exception("Error from %s: %s", id_api, e, exc_info=True)
                if "CONNECTION_DURATION" in self.producer_metrics:
                    duration = time.time() - connection_start_time
                    self.CONNECTION_DURATION.labels(websocket_id=id_api).set(duration)
                if "ERRORS_DISCONNECTS" in self.producer_metrics:
                    self.ERRORS_DISCONNECTS.labels(websocket_id=id_api).inc()
                raise
            except Exception as e:
                if "ERRORS_DISCONNECTS" in self.producer_metrics:
                    self.ERRORS_DISCONNECTS.labels(websocket_id=id_api).inc()
                self.stop_orchestrator()
                for task in self._tasks.keys():
                    await self._hault_coroutine(task)
                self.logger.exception("Error from %s: %s. The coroutine was completely closed or broken", id_api, e, exc_info=True)
                
        def wrapper(self, *args, **kwargs):
            return backoff.on_exception(
                backoff.expo,
                aiohttp_recoverable_errors,
                max_tries=self.max_reconnect_retries,
                max_time=300
            )(inner_coroutine_manager)(self, *args, **kwargs)

        return wrapper
        
    @backoff_exception_
    async def start_coroutines_orchestrator(self, lag, *args, **kwargs):
        """ 
            manages fetching coroutines.
            method _calibrate_instruments writes instruments to del/add into variables self._instruments_to_add, self._instruments_to_remove
            based on active instruments, the dict self._tasks is updated
        """
        
        objective = self.connection_data.get("objective")
        exchange = self.connection_data.get("exchange")
        instrument_calibration_timeout = self.connection_data.get("instrument_calibration_timeout", 60*60)
        special_method = self.connection_data.get("is_special")
        
        update_symbol_task = asyncio.create_task(getattr(self, "_calibrate_instruments")(instrument_calibration_timeout))
        id_instrument_calibration = f"{exchange}_{special_method}_{self.underlying_asset}_calibrate_instruments"
        self._tasks[id_instrument_calibration] = update_symbol_task 
        await asyncio.sleep(5 + lag)
                
        self.start_orchestrator()
        while self.running.get("coroutine_orchestrator") is True:
                        
            # Add new tasks
            for margin_type in self._instruments_to_add:
                
                for instrument in self._instruments_to_add.get(margin_type):
                    
                    for objective in self._objectives:
                    
                        id_instrument = f"{exchange}_{special_method}_{self.underlying_asset}_{instrument}_{objective}"

                        if not self._tasks.get(id_instrument, None):                        
                            
                            method = getattr(self, "_asyncronous_data_stream")
                            method = partial(
                                method, id_instrument=id_instrument, exchange=exchange, margin_type=margin_type, objective=objective, instrument=instrument,
                                special_param=instrument, special_method=special_method
                                )
                            task = asyncio.create_task(method(), name=id_instrument)
                            self._tasks[id_instrument] = task

            # Remove expired tasks
            for margin_type in self._instruments_to_remove:

                for instrument in self._instruments_to_remove.get(margin_type):
                    
                    for objective in self._objectives:

                        id_instrument = f"{exchange}_{special_method}_{self.underlying_asset}_{instrument}_{objective}"
                                                
                        task_to_remove = next((task_name for task_name, task in self._tasks.items() if task_name == id_instrument), None)
                        
                        if task_to_remove:
                            self._hault_coroutine(id_instrument)

            await asyncio.sleep(instrument_calibration_timeout)
            
    def _build_fetching_method(self, exchange, margin_type, objective, instrument, special_param, special_method):
        """ helper of asyncronous_data_stream"""
        # Binance
        if exchange == "binance" and margin_type == "option" and objective == "oi":
            fetch_method = partial(self.fetcher, "option", "oi", symbol=self.underlying_asset, specialParam=special_param,  special_method=special_method)
        if exchange == "binance" and objective in ["tta", "ttp", "gta"] and special_method == "posfutureperp":
            if margin_type == "linear":
                inst_type = "future" if bool(re.search(r'\d', instrument.split("_")[-1])) else "perpetual"
                fetch_method = partial(self.fetcher, inst_type, objective, symbol=instrument,  special_method="posfutureperp")
            if margin_type == "inverse":
                fetch_method = partial(self.fetcher, "perpetual", objective, symbol=self.underlying_asset+"USD",  special_method="posfutureperp")
        if exchange == "binance" and objective == "oi" and special_method == "oifutureperp":
            inst_type = "future" if bool(re.search(r'\d', instrument.split("_")[-1])) else "perpetual"
            fetch_method = partial(self.fetcher, inst_type, "oi", symbol=instrument,  special_method="oifutureperp")
        if exchange == "binance" and special_method == "fundperp":
            fetch_method = partial(self.fetcher, "perpetual", "funding", symbol=instrument, special_method="fundperp")
        
        # Bybit
        if exchange == "bybit" and special_method == "oifutureperp":
            inst_type = "future" if "-" in instrument else "perpetual"
            fetch_method = partial(self.fetcher, inst_type, "oi", symbol=instrument, special_method="oifutureperp")
        if exchange == "bybit" and special_method == "posfutureperp": 
            instrument = instrument.replace("PERP", "USD") if "PERP" in instrument else instrument
            inst_type = "future" if "-" in instrument else "perpetual"
            fetch_method = partial(self.fetcher, inst_type, "gta", symbol=instrument, special_method="posfutureperp")
        if exchange == "bybit" and special_method == "fundperp": 
            fetch_method = partial(self.fetcher, "perpetual", "funding", symbol=instrument, special_method="fundperp")
            
        # Okx
        if exchange == "okx" and objective == "oi": 
            fetch_method = partial(self.fetcher, margin_type, "oi", instrument)
        if exchange == "okx" and objective == "funding": 
            fetch_method = partial(self.fetcher, margin_type, "funding", instrument)
            
        # Bitget
        if exchange == "bitget" and objective == "oi": 
            fetch_method = partial(self.fetcher, "perpetual", "oi", symbol=instrument, special_method="oifutureperp")
        if exchange == "bitget" and objective == "funding": 
            fetch_method = partial(self.fetcher, "perpetual", "funding", symbol=instrument, special_method="fundperp")
        return fetch_method
    
    
    async def _cancel_empty_coroutines(self, message, id_instrument, exchange):
        message_encoded = message.encode("utf-8")
        size = sys.getsizeof(message_encoded)
        if exchange == "binance" and size < 40:
            await self._hault_coroutine(id_instrument)

    @errors_aiohttp
    async def _asyncronous_data_stream(self, id_instrument, exchange, margin_type, objective, instrument, special_param, special_method):

        """Creates fetching coroutine for a specific symbol"""
        self._start_coroutine(id_instrument)
        topic_name = self.connection_data.get("topic_name")
        pull_timeout = self.connection_data.get("pullTimeout")
        fetch_method = self._build_fetching_method(exchange, margin_type, objective, instrument, special_param, special_method)
        
        symbol_check_tries = 0
        
        while self.running.get(id_instrument):
            data = await fetch_method()
            await self.send_message_to_topic(topic_name, data)
            # -------
            message_encoded = data.encode("utf-8")
            print(sys.getsizeof(message_encoded), id_instrument)
            # -------
            
            # Can I close this coroutine from here
            if symbol_check_tries < 5:
                await self._cancel_empty_coroutines(data, id_instrument, exchange)
                symbol_check_tries += 1
             
            
            await asyncio.sleep(pull_timeout)
            
            

class binance_aoihttp_oioption_manager(CommonFunctionality):
    
    def __init__ (self, underlying_asset, binance_get_option_expiries_method:callable, aiohttpfetch:callable):
        super().__init__()
        self.underlying_asset = underlying_asset
        self.get_expiries = binance_get_option_expiries_method
        self.fetcher = aiohttpfetch
        self._objectives = ["oi"]

    @CommonFunctionality.errors_aiohttp
    async def _calibrate_instruments(self, symbols_update_interval):
        """ updates ixisting option instruments"""
        self.running["calibrate_instruments"] = True
        while self.running["calibrate_instruments"]:
            expiries = await self.get_expiries(self.underlying_asset)
            old_expiries = self._instruments.get("option", [])
            instruments_to_remove = list(set(old_expiries) - set(expiries)) 
            instruments_to_add = list(set(expiries) - set(old_expiries))         
            self._instruments["option"] = expiries
            self._instruments_to_remove["option"] = instruments_to_remove
            self._instruments_to_add["option"] = instruments_to_add
            await asyncio.sleep(symbols_update_interval)

class binance_aoihttp_posfutureperp_manager(CommonFunctionality):
    
    def __init__ (self, underlying_asset, info_linear:callable, aiohttpfetch:callable):
        super().__init__()
        self.underlying_asset = underlying_asset
        self.get_symbols_linearmargin = info_linear
        self.fetcher = aiohttpfetch
        self._objectives = ["tta", "ttp", "gta"]
        self._inverse_count = 0

    @CommonFunctionality.errors_aiohttp
    async def _calibrate_instruments(self, symbols_update_interval):
        """ there are no unique positions for every symbol from inverse margin. The positioning is encapsulated simply within underlyingasset_USD"""
        self.running["calibrate_instruments"] = True
        while self.running["calibrate_instruments"]:
            # current linear symbols
            currect_symbols_linearmargin = await self.get_symbols_linearmargin(self.underlying_asset)
            currect_symbols_linearmargin = [x for x in currect_symbols_linearmargin if self.underlying_asset in x and "USD" in  x]
            
            old_symbols_linearmargin = self._instruments.get("linear", [])
            instruments_to_remove = list(set(old_symbols_linearmargin) - set(currect_symbols_linearmargin)) 
            instruments_to_add = list(set(currect_symbols_linearmargin) - set(old_symbols_linearmargin))         
            self._instruments["linear"] = currect_symbols_linearmargin
            self._instruments_to_remove["linear"] = instruments_to_remove
            self._instruments_to_add["linear"] = instruments_to_add
            self._instruments_to_add["inverse"].append(self.underlying_asset+"USD")
                        
            if self._inverse_count == 1:
                self._instruments_to_add["inverse"] = []
            if self._inverse_count == 0:
                self._inverse_count += 1
            await asyncio.sleep(symbols_update_interval)
            
class binance_aoihttp_oifutureperp_manager(CommonFunctionality):
    
    """ Unique symbol update method """

    def __init__ (self, underlying_asset, info_linear:callable, info_inverse:callable, aiohttpfetch:callable):
        super().__init__()
        self.underlying_asset = underlying_asset
        self.get_symbols_linearmargin = info_linear
        self.get_symbols_inversemargin = info_inverse
        self.fetcher = aiohttpfetch
        self._objectives = ["oi"]

    @CommonFunctionality.errors_aiohttp
    async def _calibrate_instruments(self, symbols_update_interval):
        """ there are no unique positions for every symbol from inverse margin. The positioning is encapsulated simply within underlyingasset_USD"""
        self.running["calibrate_instruments"] = True
        while self.running["calibrate_instruments"]:
            # current linear symbols
            currect_symbols_linearmargin = await self.get_symbols_linearmargin(self.underlying_asset)
            currect_symbols_linearmargin = [x for x in currect_symbols_linearmargin if self.underlying_asset in x and "USD" in  x]
            
            old_symbols_linearmargin = self._instruments.get("linear", [])
            instruments_to_remove = list(set(old_symbols_linearmargin) - set(currect_symbols_linearmargin)) 
            instruments_to_add = list(set(currect_symbols_linearmargin) - set(old_symbols_linearmargin))         
            self._instruments["linear"] = currect_symbols_linearmargin
            self._instruments_to_remove["linear"] = instruments_to_remove
            self._instruments_to_add["linear"] = instruments_to_add
            
            currect_symbols_inversemargin = await self.get_symbols_inversemargin(self.underlying_asset)
            currect_symbols_inversemargin = [x for x in currect_symbols_inversemargin if self.underlying_asset in x and "USD" in  x]  
            
            old_symbols_inversemargin = self._instruments.get("inverse", [])
            instruments_to_remove = list(set(old_symbols_inversemargin) - set(currect_symbols_inversemargin)) 
            instruments_to_add = list(set(currect_symbols_inversemargin) - set(old_symbols_inversemargin))         
            self._instruments["inverse"] = currect_symbols_inversemargin
            self._instruments_to_remove["inverse"] = instruments_to_remove
            self._instruments_to_add["inverse"] = instruments_to_add
                        
            await asyncio.sleep(symbols_update_interval)
            
class binance_aoihttp_fundperp_manager(CommonFunctionality):
    
    def __init__ (self, underlying_asset, info_inverse:callable, info_linear:callable, aiohttpfetch:callable):
        super().__init__()
        self.underlying_asset = underlying_asset
        self.get_symbols_linearmargin = info_linear
        self.get_symbols_inversemargin = info_inverse
        self.fetcher = aiohttpfetch
        self._objectives = ["funding"]

    @CommonFunctionality.errors_aiohttp
    async def _calibrate_instruments(self, symbols_update_interval):
        """ there are no unique positions for every symbol from inverse margin. The positioning is encapsulated simply within underlyingasset_USD"""
        self.running["calibrate_instruments"] = True
        while self.running["calibrate_instruments"]:
            # current linear symbols
            current_symbols_linearmargin = await self.get_symbols_linearmargin(self.underlying_asset)
            current_symbols_linearmargin = [x for x in current_symbols_linearmargin if self.underlying_asset in x and "USD" in  x]
            current_symbols_linearmargin = [x for x in current_symbols_linearmargin if not bool(re.search(r'\d', x.split("_")[-1]))]
            
            
            old_symbols_linearmargin = self._instruments.get("linear", [])
            instruments_to_remove = list(set(old_symbols_linearmargin) - set(current_symbols_linearmargin)) 
            instruments_to_add = list(set(current_symbols_linearmargin) - set(old_symbols_linearmargin))         
            self._instruments["linear"] = current_symbols_linearmargin
            self._instruments_to_remove["linear"] = instruments_to_remove
            self._instruments_to_add["linear"] = instruments_to_add
            
            current_symbols_inversemargin = await self.get_symbols_inversemargin(self.underlying_asset)
            current_symbols_inversemargin = [x for x in current_symbols_inversemargin if self.underlying_asset in x and "USD" in  x]
            current_symbols_inversemargin = [x for x in current_symbols_inversemargin if not bool(re.search(r'\d', x.split("_")[-1]))]  
            
            old_symbols_inversemargin = self._instruments.get("inverse", [])
            instruments_to_remove = list(set(old_symbols_inversemargin) - set(current_symbols_inversemargin)) 
            instruments_to_add = list(set(current_symbols_inversemargin) - set(old_symbols_inversemargin))         
            self._instruments["inverse"] = current_symbols_inversemargin
            self._instruments_to_remove["inverse"] = instruments_to_remove
            self._instruments_to_add["inverse"] = instruments_to_add
                                    
            await asyncio.sleep(symbols_update_interval)
                
class bybit_aoihttp_oifutureperp_manager(CommonFunctionality):
    
    def __init__ (self, underlying_asset, info_linear:callable, info_inverse:callable, aiohttpfetch:callable):
        super().__init__()
        self.underlying_asset = underlying_asset
        self.get_symbols_linearmargin = info_linear
        self.get_symbols_inversemargin = info_inverse
        self.fetcher = aiohttpfetch
        self._objectives = ["oi"]

    @CommonFunctionality.errors_aiohttp
    async def _calibrate_instruments(self, symbols_update_interval):
        """ there are no unique positions for every symbol from inverse margin. The positioning is encapsulated simply within underlyingasset_USD"""
        self.running["calibrate_instruments"] = True
        while self.running["calibrate_instruments"]:
            # current linear symbols
            current_symbols_linearmargin = await self.get_symbols_linearmargin(self.underlying_asset)
            
            old_symbols_linearmargin = self._instruments.get("linear", [])
            instruments_to_remove = list(set(old_symbols_linearmargin) - set(current_symbols_linearmargin)) 
            instruments_to_add = list(set(current_symbols_linearmargin) - set(old_symbols_linearmargin))         
            self._instruments["linear"] = current_symbols_linearmargin
            self._instruments_to_remove["linear"] = instruments_to_remove
            self._instruments_to_add["linear"] = instruments_to_add
            
            current_symbols_inversemargin = await self.get_symbols_inversemargin(self.underlying_asset)
            
            old_symbols_inversemargin = self._instruments.get("inverse", [])
            instruments_to_remove = list(set(old_symbols_inversemargin) - set(current_symbols_inversemargin)) 
            instruments_to_add = list(set(current_symbols_inversemargin) - set(old_symbols_inversemargin))         
            self._instruments["inverse"] = current_symbols_inversemargin
            self._instruments_to_remove["inverse"] = instruments_to_remove
            self._instruments_to_add["inverse"] = instruments_to_add
                                                
            await asyncio.sleep(symbols_update_interval)                

class bybit_aoihttp_posfutureperp_manager(CommonFunctionality):
    
    def __init__ (self, underlying_asset, info_linear:callable, info_inverse:callable, aiohttpfetch:callable):
        super().__init__()
        self.underlying_asset = underlying_asset
        self.get_symbols_linearmargin = info_linear
        self.get_symbols_inversemargin = info_inverse
        self.fetcher = aiohttpfetch
        self._objectives = ["gta"]

    @CommonFunctionality.errors_aiohttp
    async def _calibrate_instruments(self, symbols_update_interval):
        """ there are no unique positions for every symbol from inverse margin. The positioning is encapsulated simply within underlyingasset_USD"""
        self.running["calibrate_instruments"] = True
        while self.running["calibrate_instruments"]:
            # current linear symbols
            current_symbols_linearmargin = await self.get_symbols_linearmargin(self.underlying_asset)
            current_symbols_linearmargin = [s for s in current_symbols_linearmargin if len(s.split("-")) == 1]
            
            old_symbols_linearmargin = self._instruments.get("linear", [])
            instruments_to_remove = list(set(old_symbols_linearmargin) - set(current_symbols_linearmargin)) 
            instruments_to_add = list(set(current_symbols_linearmargin) - set(old_symbols_linearmargin))         
            self._instruments["linear"] = current_symbols_linearmargin
            self._instruments_to_remove["linear"] = instruments_to_remove
            self._instruments_to_add["linear"] = instruments_to_add
            
            current_symbols_inversemargin = await self.get_symbols_inversemargin(self.underlying_asset)
            current_symbols_inversemargin = [s for s in current_symbols_inversemargin if len(s.split("-")) == 1]
            
            old_symbols_inversemargin = self._instruments.get("inverse", [])
            instruments_to_remove = list(set(old_symbols_inversemargin) - set(current_symbols_inversemargin)) 
            instruments_to_add = list(set(current_symbols_inversemargin) - set(old_symbols_inversemargin))         
            self._instruments["inverse"] = current_symbols_inversemargin
            self._instruments_to_remove["inverse"] = instruments_to_remove
            self._instruments_to_add["inverse"] = instruments_to_add
                                                
            await asyncio.sleep(symbols_update_interval)   

class bybit_aoihttp_fundperp_manager(CommonFunctionality):
    
    def __init__ (self, underlying_asset, info_linear:callable, info_inverse:callable, aiohttpfetch:callable):
        super().__init__()
        self.underlying_asset = underlying_asset
        self.get_symbols_linearmargin = info_linear
        self.get_symbols_inversemargin = info_inverse
        self.fetcher = aiohttpfetch
        self._objectives = ["funding"]

    @CommonFunctionality.errors_aiohttp
    async def _calibrate_instruments(self, symbols_update_interval):
        """ there are no unique positions for every symbol from inverse margin. The positioning is encapsulated simply within underlyingasset_USD"""
        self.running["calibrate_instruments"] = True
        while self.running["calibrate_instruments"]:
            # current linear symbols
            current_symbols_linearmargin = await self.get_symbols_linearmargin(self.underlying_asset)
            current_symbols_linearmargin = [s for s in current_symbols_linearmargin if len(s.split("-")) == 1]
            current_symbols_linearmargin_insttype = ["future" if "-" in symbol else "perpetual" for symbol in current_symbols_linearmargin]
            current_symbols_linearmargin = [symbol for symbol, insttype in zip(current_symbols_linearmargin, current_symbols_linearmargin_insttype) if insttype == "perpetual"]
            
            old_symbols_linearmargin = self._instruments.get("linear", [])
            instruments_to_remove = list(set(old_symbols_linearmargin) - set(current_symbols_linearmargin)) 
            instruments_to_add = list(set(current_symbols_linearmargin) - set(old_symbols_linearmargin))         
            self._instruments["linear"] = current_symbols_linearmargin
            self._instruments_to_remove["linear"] = instruments_to_remove
            self._instruments_to_add["linear"] = instruments_to_add
            
            current_symbols_inversemargin = await self.get_symbols_inversemargin(self.underlying_asset)
            current_symbols_inversemargin = [s for s in current_symbols_inversemargin if len(s.split("-")) == 1]
            current_symbols_inversemargin_insttype = ["future" if "-" in symbol else "perpetual" for symbol in current_symbols_inversemargin]
            current_symbols_inversemargin = [symbol for symbol, insttype in zip(current_symbols_inversemargin, current_symbols_inversemargin_insttype) if insttype == "perpetual"]
            
            old_symbols_inversemargin = self._instruments.get("inverse", [])
            instruments_to_remove = list(set(old_symbols_inversemargin) - set(current_symbols_inversemargin)) 
            instruments_to_add = list(set(current_symbols_inversemargin) - set(old_symbols_inversemargin))         
            self._instruments["inverse"] = current_symbols_inversemargin
            self._instruments_to_remove["inverse"] = instruments_to_remove
            self._instruments_to_add["inverse"] = instruments_to_add
                                                
            await asyncio.sleep(symbols_update_interval)   

class okx_aoihttp_oifutureperp_manager(CommonFunctionality):
    
    def __init__ (self, underlying_asset, info_perpetual:callable, info_future:callable, aiohttpfetch:callable):
        super().__init__()
        self.underlying_asset = underlying_asset
        self.get_symbols_perpetual = info_perpetual
        self.get_symbols_future = info_future
        self.fetcher = aiohttpfetch
        self._objectives = ["oi"]

    @CommonFunctionality.errors_aiohttp
    async def _calibrate_instruments(self, symbols_update_interval):
        """ there are no unique positions for every symbol from inverse margin. The positioning is encapsulated simply within underlyingasset_USD"""
        self.running["calibrate_instruments"] = True
        while self.running["calibrate_instruments"]:
            # current linear symbols
            current_symbols_perpetual = await self.get_symbols_perpetual(self.underlying_asset)
            old_symbols_perpetual = self._instruments.get("perpetual", [])
            instruments_to_remove = list(set(old_symbols_perpetual) - set(current_symbols_perpetual)) 
            instruments_to_add = list(set(current_symbols_perpetual) - set(old_symbols_perpetual))         
            self._instruments["perpetual"] = current_symbols_perpetual
            self._instruments_to_remove["perpetual"] = instruments_to_remove
            self._instruments_to_add["perpetual"] = instruments_to_add
            
            current_symbols_future = await self.get_symbols_future(self.underlying_asset)
            old_symbols_future = self._instruments.get("future", [])
            instruments_to_remove = list(set(old_symbols_future) - set(current_symbols_future)) 
            instruments_to_add = list(set(current_symbols_future) - set(old_symbols_future))         
            self._instruments["future"] = current_symbols_future
            self._instruments_to_remove["future"] = instruments_to_remove
            self._instruments_to_add["future"] = instruments_to_add
                                                            
            await asyncio.sleep(symbols_update_interval)
            
class okx_aoihttp_fundperp_manager(CommonFunctionality):
    
    def __init__ (self, underlying_asset, info_perpetual:callable, aiohttpfetch:callable):
        super().__init__()
        self.underlying_asset = underlying_asset
        self.get_symbols_perpetual = info_perpetual
        self.fetcher = aiohttpfetch
        self._objectives = ["oi"]

    @CommonFunctionality.errors_aiohttp
    async def _calibrate_instruments(self, symbols_update_interval):
        """ there are no unique positions for every symbol from inverse margin. The positioning is encapsulated simply within underlyingasset_USD"""
        self.running["calibrate_instruments"] = True
        while self.running["calibrate_instruments"]:
            # current linear symbols
            current_symbols_perpetual = await self.get_symbols_perpetual(self.underlying_asset)
            old_symbols_perpetual = self._instruments.get("perpetual", [])
            instruments_to_remove = list(set(old_symbols_perpetual) - set(current_symbols_perpetual)) 
            instruments_to_add = list(set(current_symbols_perpetual) - set(old_symbols_perpetual))         
            self._instruments["perpetual"] = current_symbols_perpetual
            self._instruments_to_remove["perpetual"] = instruments_to_remove
            self._instruments_to_add["perpetual"] = instruments_to_add
                                                            
            await asyncio.sleep(symbols_update_interval)
            
class bitget_aoihttp_oifutureperp_manager(CommonFunctionality):
    
    def __init__ (self, underlying_asset, info_perpetual:callable, aiohttpfetch:callable):
        super().__init__()
        self.underlying_asset = underlying_asset
        self.get_symbols_perpetual = info_perpetual
        self.fetcher = aiohttpfetch
        self._objectives = ["oi"]

    @CommonFunctionality.errors_aiohttp
    async def _calibrate_instruments(self, symbols_update_interval):
        """ there are no unique positions for every symbol from inverse margin. The positioning is encapsulated simply within underlyingasset_USD"""
        self.running["calibrate_instruments"] = True
        while self.running["calibrate_instruments"]:
            # current linear symbols
            symbols_by_margin = await self.get_symbols_perpetual(self.underlying_asset)
            current_symbols_perpetual = [y for x in symbols_by_margin.values() for y in x]
            
            old_symbols_perpetual = self._instruments.get("perpetual", [])
            instruments_to_remove = list(set(old_symbols_perpetual) - set(current_symbols_perpetual)) 
            instruments_to_add = list(set(current_symbols_perpetual) - set(old_symbols_perpetual))         
            self._instruments["perpetual"] = current_symbols_perpetual
            self._instruments_to_remove["perpetual"] = instruments_to_remove
            self._instruments_to_add["perpetual"] = instruments_to_add
                                                            
            await asyncio.sleep(symbols_update_interval)
        
class bitget_aoihttp_fundperp_manager(CommonFunctionality):
    
    def __init__ (self, underlying_asset, info_perpetual:callable, aiohttpfetch:callable):
        super().__init__()
        self.underlying_asset = underlying_asset
        self.get_symbols_perpetual = info_perpetual
        self.fetcher = aiohttpfetch
        self._objectives = ["funding"]

    @CommonFunctionality.errors_aiohttp
    async def _calibrate_instruments(self, symbols_update_interval):
        """ there are no unique positions for every symbol from inverse margin. The positioning is encapsulated simply within underlyingasset_USD"""
        self.running["calibrate_instruments"] = True
        while self.running["calibrate_instruments"]:
            # current linear symbols
            symbols_by_margin = await self.get_symbols_perpetual(self.underlying_asset)
            current_symbols_perpetual = [y for x in symbols_by_margin.values() for y in x]
            
            old_symbols_perpetual = self._instruments.get("perpetual", [])
            instruments_to_remove = list(set(old_symbols_perpetual) - set(current_symbols_perpetual)) 
            instruments_to_add = list(set(current_symbols_perpetual) - set(old_symbols_perpetual))         
            self._instruments["perpetual"] = current_symbols_perpetual
            self._instruments_to_remove["perpetual"] = instruments_to_remove
            self._instruments_to_add["perpetual"] = instruments_to_add
                                                            
            await asyncio.sleep(symbols_update_interval)



# class bitget_aoihttp_fundperp_manager(CommonFunctionality):

#     def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
#         self.running = True
#         self.underlying_asset = underlying_asset
#         self.symbols_perpetual = []
#         self.info = info
#         self.fetcher = aiohttpfetch
#         self.symbol_update_task = True
#         self.data = {}
#         self.pullTimeout = 1
#         self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
#         self.topic_name = ""

#     async def get_bitget_perpetual_symbols(self):
#         self.symbols_perpetual = await self.info(self.underlying_asset)
    
#     async def update_symbols(self, lag=0, update_interval=60*24):
#         await asyncio.sleep(lag)
#         while self.running:
#             task = asyncio.create_task(self.get_bitget_perpetual_symbols())
#             await task
#             await asyncio.sleep(update_interval)  

#     async def h1(self, symbol):
#         data = await self.fetcher("perpetual", "funding", symbol=symbol, special_method="fundperp")
#         self.data[symbol] = data

#     @CommonFunctionality.log_exceptions
#     async def aiomethod(self):
#         tasks = []
#         for margin in self.symbols_perpetual:
#             for symbol in self.symbols_perpetual[margin]:
#                 tasks.append(self.h1(symbol))
#         await asyncio.gather(*tasks)

#         for key, funddata in self.data.copy().items():
#             if "fundingRate" not in funddata:
#                 for symbol, perpsymb in self.symbols_perpetual.copy().items():
#                     if key in perpsymb:
#                         self.symbols_perpetual[symbol].remove(key)
#                 del self.data[key]

# class gateio_aoihttp_fundperp_manager(CommonFunctionality):

#     def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
#         self.running = True
#         self.underlying_asset = underlying_asset
#         self.linear_symbols = []
#         self.inverse_symbols = []
#         self.info = info
#         self.fetcher = aiohttpfetch
#         self.symbol_update_task = True
#         self.data = {}
#         self.pullTimeout = 1
#         self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
#         self.topic_name = ""


#     async def get_symbols(self):
#         linear_perpetual, inverse_perpetual, futures = await self.info(self.underlying_asset)
#         self.linear_symbols = linear_perpetual
#         self.inverse_symbols = inverse_perpetual

#     async def update_symbols(self, lag=0, update_interval=60*24):
#         await asyncio.sleep(lag)
#         while self.running:
#             task = asyncio.create_task(self.get_symbols())
#             await task
#             await asyncio.sleep(update_interval)  

#     async def h1(self, symbol):
#         data = await self.fetcher("perpetual", "funding", symbol)
#         self.data[f"{symbol}"] = data

#     @CommonFunctionality.log_exceptions
#     async def aiomethod(self):
#         tasks = []
#         for s in self.inverse_symbols:
#             tasks.append(self.h1(s))
#         for s in self.linear_symbols:
#             tasks.append(self.h1(s))
#         await asyncio.gather(*tasks)

# class gateio_aoihttp_oifutureperp_manager(CommonFunctionality):

#     def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
#         self.running = True
#         self.underlying_asset = underlying_asset
#         self.linear_symbols = []
#         self.inverse_symbols = []
#         self.future_symbols = []
#         self.info = info
#         self.fetcher = aiohttpfetch
#         self.symbol_update_task = True
#         self.data = {}
#         self.pullTimeout = 1
#         self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
#         self.topic_name = ""


#     async def get_symbols(self):
#         linear_perpetual, inverse_perpetual, futures = await self.info(self.underlying_asset)
#         self.linear_symbols = linear_perpetual
#         self.inverse_symbols = inverse_perpetual
#         self.future_symbols = futures

#     async def update_symbols(self, lag=0, update_interval=60*24):
#         await asyncio.sleep(lag)
#         while self.running:
#             task = asyncio.create_task(self.get_symbols())
#             await task
#             await asyncio.sleep(update_interval)  

#     async def helper(self, symbol, objective, didi, instType):
#         data = await self.fetcher(instType, objective, symbol)
#         self.data[f"{symbol}"] = data
    
#     @CommonFunctionality.log_exceptions
#     async def aiomethod(self):
#         d = {}
#         tasks = []
#         for sa in self.linear_symbols:
#             tasks.append(self.helper(sa, "oi", d, "perpetual"))
#         for saa in self.inverse_symbols:
#             tasks.append(self.helper(saa, "oi", d, "perpetual"))
#         for saaa in self.future_symbols:
#             tasks.append(self.helper(saaa, "oi", d, "future"))
#         await asyncio.gather(*tasks)        
        
#         for key, value in self.data.copy().items():
#             if "total_size" not in value and "open_interest" not in value:
#                 del self.data[key]
#                 if key.split("_")[-1].isdigit():
#                     self.future_symbols.remove(key)
#                 if "USD" in key and "USDT" in key: 
#                     self.linear_symbols.remove(key)
#                 if "USD" in key and "USDT" not in key: 
#                     self.inverse_symbols.remove(key)

# class gateio_aoihttp_posfutureperp_manager(CommonFunctionality):

#     def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
#         self.running = True
#         self.underlying_asset = underlying_asset
#         self.linear_symbols = []
#         self.inverse_symbols = []
#         self.future_symbols = []
#         self.info = info
#         self.fetcher = aiohttpfetch
#         self.symbol_update_task = True
#         self.data = {}
#         self.pullTimeout = 1
#         self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
#         self.topic_name = ""


#     async def get_symbols(self):
#         linear_perpetual, inverse_perpetual, futures = await self.info(self.underlying_asset)
#         self.linear_symbols = linear_perpetual
#         self.inverse_symbols = inverse_perpetual
#         self.future_symbols = futures

#     async def update_symbols(self, lag=0, update_interval=60*24):
#         await asyncio.sleep(lag)
#         while self.running:
#             task = asyncio.create_task(self.get_symbols())
#             await task
#             await asyncio.sleep(update_interval)  

#     async def gateio_positioning_useless_or_not(self, symbol, objective, didi):
#         data = await self.fetcher("perpetual", objective, symbol)
#         self.data[f"{symbol}"] = data

#     @CommonFunctionality.log_exceptions
#     async def aiomethod(self):
#         d = {}
#         tasks = []
#         for s in self.linear_symbols:
#             tasks.append(self.gateio_positioning_useless_or_not(s, "tta", d))
#         for s in self.inverse_symbols:
#             tasks.append(self.gateio_positioning_useless_or_not(s, "tta", d))
#         await asyncio.gather(*tasks)
        
# class htx_aiohttp_oifutureperp_manager(CommonFunctionality):

#     def __init__(self, underlying_asset, inverse_future_contract_types_htx, htx_aiohttpFetch):
#         self.inverse_future_contract_types_htx = inverse_future_contract_types_htx
#         self.htx_aiohttpFetch = htx_aiohttpFetch
#         self.data = {}
#         self.running = True
#         self.pullTimeout = 1
#         self.underlying_asset = underlying_asset
#         self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
#         self.topic_name = ""

#     async def htx_fetch_oi_helper(self, instType, objective, underlying_asset, asset_specification, state_dictionary):
#         response = await self.htx_aiohttpFetch(instType, objective, f"{underlying_asset}{asset_specification}")      
#         state_dictionary[f"{underlying_asset}{asset_specification}"] = response

#     async def htx_fetch_oi_helper_2(self, instType, objective, underlying_asset, asset_specification, state_dictionary, ctype):
#         response = await self.htx_aiohttpFetch(instType, objective, f"{underlying_asset}{asset_specification}", contract_type=ctype)

#         state_dictionary[f"{underlying_asset}{asset_specification}"] = response

#     @CommonFunctionality.log_exceptions
#     async def aiomethod(self):
#         tasks = []
#         tasks.append(self.htx_fetch_oi_helper("perpetual", "oiall", self.underlying_asset, "-USDT.LinearPerpetual", self.data))
#         tasks.append(self.htx_fetch_oi_helper("perpetual", "oi", self.underlying_asset, "-USD", self.data))
#         for ctype in self.inverse_future_contract_types_htx:
#             tasks.append(self.htx_fetch_oi_helper_2("future", "oi", self.underlying_asset, ".InverseFuture", self.data, ctype))
#         await asyncio.gather(*tasks)

# class htx_aiohttp_fundperp_manager(CommonFunctionality):

#     def __init__(self, underlying_asset, inverse_future_contract_types_htx, htx_aiohttpFetch):
#         self.inverse_future_contract_types_htx = inverse_future_contract_types_htx
#         self.htx_aiohttpFetch = htx_aiohttpFetch
#         self.data = {}
#         self.running = True
#         self.pullTimeout = 1
#         self.underlying_asset = underlying_asset
#         self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
#         self.topic_name = ""

#     async def htx_fetch_fundperp_helper(self, instType, objective, underlying_asset, asset_specification, state_dictionary, marginCoinCoinCoin):
#         l = await self.htx_aiohttpFetch(instType, objective, f"{underlying_asset}{asset_specification}")
#         state_dictionary[marginCoinCoinCoin] = l

#     @CommonFunctionality.log_exceptions
#     async def aiomethod(self):
#         tasks = []
#         tasks.append(self.htx_fetch_fundperp_helper("perpetual", "funding", self.underlying_asset, "-USDT", self.data, "usdt"))
#         tasks.append(self.htx_fetch_fundperp_helper("perpetual", "funding", self.underlying_asset, "-USD", self.data, "usd"))
#         await asyncio.gather(*tasks)
    
# class htx_aiohttp_posfutureperp_manager(CommonFunctionality):

#     def __init__(self, underlying_asset, inverse_future_contract_types_htx, htx_aiohttpFetch):
#         self.inverse_future_contract_types_htx = inverse_future_contract_types_htx
#         self.htx_aiohttpFetch = htx_aiohttpFetch
#         self.data = {}
#         self.running = True
#         self.pullTimeout = 1
#         self.underlying_asset = underlying_asset
#         self.send_message_to_topic:Callable[[Any, str, bytes], Any] = None
#         self.topic_name = ""

#     async def htx_fetch_pos_helper(self, instType, objective, underlying_asset, ltype, state_dictionary):
#         tta = await self.htx_aiohttpFetch(instType, objective, f"{underlying_asset}-{ltype}")
#         state_dictionary[f"{underlying_asset}_{ltype}_{objective}"] = tta

#     async def htx_fetch_pos_helper_2(self, instType, underlying_asset, obj, state_dictionary):
#         tta = await self.htx_aiohttpFetch(instType, obj, f"{underlying_asset}.InverseFuture")

#         state_dictionary[f"{underlying_asset}_InverseFuture_tta"] = tta
    
#     @CommonFunctionality.log_exceptions
#     async def aiomethod(self):
#         tasks = []
#         for ltype in ["USDT", "USD", "USDT-FUTURES"]:
#             for obj in ["tta", "ttp"]:
#                 tasks.append(self.htx_fetch_pos_helper("perpetual", obj, self.underlying_asset, ltype, self.data))
#         for obj in ["tta", "ttp"]:
#             tasks.append(self.htx_fetch_pos_helper_2("future", self.underlying_asset, obj, self.data))
#         await asyncio.gather(*tasks)









# class binance_aoihttp_posfutureperp_manager():
#     """
#         I after examining instruments related to BTC, ETHBTC instrument was present but its not suppoused to be. 
#         So info API has some mistakes on binance side and it was fixed by filtering all of the symbols that doesnt contain USD
#     """

#     def __init__ (self, underlying_asset, info_linear:callable, aiohttpfetch:callable):
#         super().__init__()
#         self.running = True
#         self.underlying_asset = underlying_asset
#         self.linear_symbols = []
#         self.inverse_symbol = underlying_asset + "USD"
#         self.info_linear_method = info_linear
#         self.fetcher = aiohttpfetch
#         self.symbol_update_task = True
#         self.data = {}
#         self.pullTimeout = 1
#         self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
#         self.topic_name = ""
        
#     async def get_binance_instruments(self):
#         self.linear_symbols = await self.info_linear_method(self.underlying_asset)
#         self.linear_symbols = [x for x in self.linear_symbols if self.underlying_asset in x and "USD" in  x]
    
#     async def update_symbols(self, lag=0, update_interval=60*24):
#         await asyncio.sleep(lag)
#         while self.running:
#             task = asyncio.create_task(self.get_binance_instruments())
#             await task
#             await asyncio.sleep(update_interval)  

#     async def helper_1(self, instType, objective, symbol):
#         data = await self.fetcher(instType, objective, symbol=symbol, special_method="posfutureperp")
#         if data == "[]" and symbol in self.linear_symbols:
#             self.linear_symbols.remove(symbol)
#         self.data[f"{symbol}_{objective}"] = data


#     async def helper_2(self, instType, objective, coinm_symbol):
#         data = await self.fetcher(instType, objective, symbol=coinm_symbol, special_method="posfutureperp")
#         self.data[coinm_symbol+f"coinmAgg_{objective}"] = data

#     # @CommonFunctionality.log_exceptions
#     async def aiomethod(self):
#         tasks = []
#         for symbol in self.linear_symbols:
#             instType = "future" if bool(re.search(r'\d', symbol.split("_")[-1])) else "perpetual"
#             for objective in ["tta", "ttp", "gta"]:
#                 marginType = binance_instType_help(symbol)
#                 symbol = symbol if marginType == "Linear" else symbol.replace("_", "").replace("PERP", "")
#                 tasks.append(self.helper_1(instType, objective, symbol))
#         for objective in ["tta", "ttp", "gta"]:
#             tasks.append(self.helper_2("perpetual", objective, self.inverse_symbol))
            
#         await asyncio.gather(*tasks)

#         keys = [f"{x}_{o}" for x in self.linear_symbols for o in ["tta", "ttp", "gta"]] + [self.inverse_symbol+f"coinmAgg_{o}" for o in ["tta", "ttp", "gta"]]
#         for key in self.data.copy():
#             if key not in keys:
#                 del self.data[key]




# class binance_aoihttp_oifutureperp_manager():

#     def __init__ (self, underlying_asset, info_linear_method:callable, info_inverse_method:callable, aiohttpfetch:callable):
#         self.running = True
#         self.underlying_asset = underlying_asset
#         self.info_linear_method = info_linear_method
#         self.info_inverse_method = info_inverse_method
#         self.fetcher = aiohttpfetch
#         self.symbol_update_task = True
#         self.data = {}
#         self.pullTimeout = 1
#         self.linear_symbols = []
#         self.inverse_symbols = []
#         self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
#         self.topic_name = ""
        

#     async def get_binance_instruments(self):
#         self.linear_symbols = await self.info_linear_method(self.underlying_asset)
#         self.linear_symbols = [x for x in self.linear_symbols if self.underlying_asset in x and "USD" in  x]
#         self.inverse_symbols = await self.info_inverse_method(self.underlying_asset)
#         self.inverse_symbols = [x for x in self.inverse_symbols if self.underlying_asset in x and "USD" in  x]  
    
#     async def update_symbols(self, lag=0, update_interval=60*24):
#         await asyncio.sleep(lag)
#         while self.running:
#             task = asyncio.create_task(self.get_binance_instruments())
#             await task
#             await asyncio.sleep(update_interval)  

#     async def helper(self, instType, symbol):
#         data = await self.fetcher(instType, "oi", symbol=symbol, special_method="oifutureperp")
#         if "code" not in data:
#             self.data[f"{symbol}_{instType}"] = data
#         else:
#             if "USD" in symbol:
#                 self.inverse_symbols.remove(symbol)
#             else:
#                 self.linear_symbols.remove(symbol)

#     # @CommonFunctionality.log_exceptions
#     async def aiomethod_2(self):
#         tasks = []
#         for symbol in self.linear_symbols + self.inverse_symbols:
#             instType = "future" if bool(re.search(r'\d', symbol.split("_")[-1])) else "perpetual"
#             tasks.append(self.helper(instType, symbol))    
#         await asyncio.gather(*tasks)

#         all_symbols = self.linear_symbols + self.inverse_symbols

#         for key in self.data.copy():
#             if len([x for x in all_symbols if x in key]) == 0:
#                 del self.data[key]



# class binance_aoihttp_fundperp_manager(CommonFunctionality):

#     def __init__ (self, underlying_asset, info_linear_method:callable, info_inverse_method:callable, aiohttpfetch:callable):
#         self.running = True
#         self.underlying_asset = underlying_asset
#         self.info_linear_method = info_linear_method
#         self.info_inverse_method = info_inverse_method
#         self.fetcher = aiohttpfetch
#         self.symbol_update_task = True
#         self.data = {}
#         self.pullTimeout = 1
#         self.linear_symbols = []
#         self.inverse_symbols = []
#         self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
#         self.topic_name = ""

#     async def get_binance_instruments(self):
#         self.linear_symbols = await self.info_linear_method(self.underlying_asset)
#         self.linear_symbols = [x for x in self.linear_symbols if self.underlying_asset in x and "USD" in  x and bool(re.search(r'\d', x.split("_")[-1])) is False]
#         self.inverse_symbols = await self.info_inverse_method(self.underlying_asset)
#         self.inverse_symbols = [x for x in self.inverse_symbols if self.underlying_asset in x and "USD" in  x and bool(re.search(r'\d', x.split("_")[-1])) is False]  

#     async def update_symbols(self, lag=0, update_interval=60*24):
#         await asyncio.sleep(lag)
#         while self.running:
#             task = asyncio.create_task(self.get_binance_instruments())
#             await task
#             await asyncio.sleep(update_interval)  

#     async def fetch_fund_binance_yeye(self, instType, symbol):
#         data = await self.fetcher(instType, "funding", symbol=symbol, special_method="fundperp")
#         self.data[f"{symbol}_{instType}"] = data

#     @CommonFunctionality.log_exceptions
#     async def aiomethod(self):
#         tasks = []
#         for symbol in self.linear_symbols + self.inverse_symbols:
#             instType = "future" if bool(re.search(r'\d', symbol.split("_")[-1])) else "perpetual"
#             if not bool(re.search(r'\d', symbol.split("_")[-1])):
#                 tasks.append(self.fetch_fund_binance_yeye(instType, symbol))
#         await asyncio.gather(*tasks)    