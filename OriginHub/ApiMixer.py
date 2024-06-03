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


class DecoratorsClass:

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


class CommonFunctionality(DecoratorsClass):
    
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
        self.symbol_check_tries = 0

        
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
                
    
    @DecoratorsClass.backoff_exception_
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
        elif exchange == "binance" and objective in ["tta", "ttp", "gta"] and special_method == "posfutureperp":
            if margin_type == "linear":
                inst_type = "future" if bool(re.search(r'\d', instrument.split("_")[-1])) else "perpetual"
                fetch_method = partial(self.fetcher, inst_type, objective, symbol=instrument,  special_method="posfutureperp")
            if margin_type == "inverse":
                fetch_method = partial(self.fetcher, "perpetual", objective, symbol=self.underlying_asset+"USD",  special_method="posfutureperp")
        elif exchange == "binance" and objective == "oi" and special_method == "oifutureperp":
            inst_type = "future" if bool(re.search(r'\d', instrument.split("_")[-1])) else "perpetual"
            fetch_method = partial(self.fetcher, inst_type, "oi", symbol=instrument,  special_method="oifutureperp")
        elif exchange == "binance" and special_method == "fundperp":
            fetch_method = partial(self.fetcher, "perpetual", "funding", symbol=instrument, special_method="fundperp")
        
        # Bybit
        elif exchange == "bybit" and special_method == "oifutureperp":
            inst_type = "future" if "-" in instrument else "perpetual"
            fetch_method = partial(self.fetcher, inst_type, "oi", symbol=instrument, special_method="oifutureperp")
        elif exchange == "bybit" and special_method == "posfutureperp": 
            instrument = instrument.replace("PERP", "USD") if "PERP" in instrument else instrument
            inst_type = "future" if "-" in instrument else "perpetual"
            fetch_method = partial(self.fetcher, inst_type, "gta", symbol=instrument, special_method="posfutureperp")
        elif exchange == "bybit" and special_method == "fundperp": 
            fetch_method = partial(self.fetcher, "perpetual", "funding", symbol=instrument, special_method="fundperp")
            
        # Okx
        elif exchange == "okx" and objective == "oi": 
            fetch_method = partial(self.fetcher, margin_type, "oi", instrument)
        elif exchange == "okx" and objective == "funding": 
            fetch_method = partial(self.fetcher, margin_type, "funding", instrument)
            
        # Bitget
        elif exchange == "bitget" and objective == "oi": 
            fetch_method = partial(self.fetcher, "perpetual", "oi", symbol=instrument, special_method="oifutureperp")
        elif exchange == "bitget" and objective == "funding": 
            fetch_method = partial(self.fetcher, "perpetual", "funding", symbol=instrument, special_method="fundperp")

        # gateio
        elif exchange == "gateio" and objective == "oi": 
            inst_type = "future" if margin_type == "futures" else "perpetual"
            fetch_method = partial(self.fetcher, inst_type, "oi", symbol=instrument)
        elif exchange == "gateio" and objective == "tta": 
            fetch_method = partial(self.fetcher, "perpetual", "tta", symbol=instrument)
        elif exchange == "gateio" and objective == "funding": 
            fetch_method = partial(self.fetcher, "perpetual", "funding", symbol=instrument)

        elif exchange == "htx" and objective == "oi" and margin_type == "linear": 
            fetch_method = partial(self.fetcher, "perpetual", "oiall", f"{self.underlying_asset}{instrument}")
        elif exchange == "htx" and objective == "oi" and margin_type == "inverse": 
            fetch_method = partial(self.fetcher, "perpetual", "oi", f"{self.underlying_asset}{instrument}")
        elif exchange == "htx" and objective == "oi" and margin_type == "future": 
            fetch_method = partial(self.fetcher, "future", "oi", f"{self.underlying_asset}.InverseFuture", contract_type=instrument)
        elif exchange == "htx" and objective == "funding": 
            fetch_method = partial(self.fetcher, "perpetual", "funding", f"{self.underlying_asset}{instrument}")
        elif exchange == "htx" and objective in ["tta", "ttp"]:
            name = f"{self.underlying_asset}-{instrument}" if margin_type == "perpetual" else f"{self.underlying_asset}.InverseFuture"
            fetch_method = partial(self.fetcher, margin_type, objective, name)

        return fetch_method
    
    
    async def _cancel_empty_coroutines(self, message, id_instrument, exchange, objective):

        if exchange == "binance" and objective in ["tta", "ttp", "gta"]:
            message = json.loads(message)
            if message.get("data") == []:
                await self._hault_coroutine(id_instrument)
        if exchange == "binance" and objective == "oi":
            message = json.loads(message)
            if int(message.get("code")) == -4108 or message.get("msg") == "Symbol is on delivering or delivered or settling or closed or pre-trading.":
                await self._hault_coroutine(id_instrument)
        if exchange == "bitget" and objective=="funding":
            message = json.loads(message)
            if message.get("data") == []:
                await self._hault_coroutine(id_instrument)
        if exchange == "bybit" and objective=="funding":
            message = json.loads(message)
            if message.get("result").get("list") == []:
                await self._hault_coroutine(id_instrument)

    async def _asyncronous_data_stream(self, id_instrument, exchange, margin_type, objective, instrument, special_param, special_method):

        """ Creates fetching coroutine for a specific symbol """
        self._start_coroutine(id_instrument)
        topic_name = self.connection_data.get("topic_name")
        pull_timeout = self.connection_data.get("pullTimeout")
        fetch_method = self._build_fetching_method(exchange, margin_type, objective, instrument, special_param, special_method)
        
        while self.running.get(id_instrument):
            
            data = await fetch_method()
            
            if exchange == "binance" and objective in ["tta", "ttp", "gta"]:
                data = json.dumps({"data" : json.loads(data), "objective" : objective})
            if exchange == "gateio":
                data = json.dumps({"data" : json.loads(data), "instrument" : instrument})
                
            await self.send_message_to_topic(topic_name, data)
            # -------
            # print(data)
            # message_encoded = data.encode("utf-8")
            # print(sys.getsizeof(message_encoded), id_instrument)
            # -------
            if self.symbol_check_tries < 5:
                await self._cancel_empty_coroutines(data, id_instrument, exchange, objective)
                self.symbol_check_tries += 1
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
            self.symbol_check_tries = 0
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
            self.symbol_check_tries = 0
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
                        
            self.symbol_check_tries = 0
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
                                    
            self.symbol_check_tries = 0
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
                                                
            self.symbol_check_tries = 0
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
                                                
            self.symbol_check_tries = 0
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
                                                
            self.symbol_check_tries = 0
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
                                                            
            self.symbol_check_tries = 0
            await asyncio.sleep(symbols_update_interval)
            
class okx_aoihttp_fundperp_manager(CommonFunctionality):
    
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
            current_symbols_perpetual = await self.get_symbols_perpetual(self.underlying_asset)
            old_symbols_perpetual = self._instruments.get("perpetual", [])
            instruments_to_remove = list(set(old_symbols_perpetual) - set(current_symbols_perpetual)) 
            instruments_to_add = list(set(current_symbols_perpetual) - set(old_symbols_perpetual))         
            self._instruments["perpetual"] = current_symbols_perpetual
            self._instruments_to_remove["perpetual"] = instruments_to_remove
            self._instruments_to_add["perpetual"] = instruments_to_add
                                                            
            self.symbol_check_tries = 0
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
                                                            
            self.symbol_check_tries = 0
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
                                                            
            self.symbol_check_tries = 0
            await asyncio.sleep(symbols_update_interval)

class gateio_aoihttp_fundperp_manager(CommonFunctionality):
    
    def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
        super().__init__()
        self.underlying_asset = underlying_asset
        self.get_symbols = info
        self.fetcher = aiohttpfetch
        self._objectives = ["funding"]

    @CommonFunctionality.errors_aiohttp
    async def _calibrate_instruments(self, symbols_update_interval):
        """ there are no unique positions for every symbol from inverse margin. The positioning is encapsulated simply within underlyingasset_USD"""
        self.running["calibrate_instruments"] = True
        while self.running["calibrate_instruments"]:
            # current linear symbols
            current_symbols_linear, current_symbols_inverse, futures = await self.get_symbols(self.underlying_asset)
            
            for margin_type, instruments in zip(["linear", "inverse"], [current_symbols_linear, current_symbols_inverse]):
                old_symbols = self._instruments.get(margin_type, [])
                instruments_to_remove = list(set(old_symbols) - set(instruments)) 
                instruments_to_add = list(set(instruments) - set(old_symbols))         
                self._instruments[margin_type] = instruments
                self._instruments_to_remove[margin_type] = instruments_to_remove
                self._instruments_to_add[margin_type] = instruments_to_add
                                                            
            self.symbol_check_tries = 0
            await asyncio.sleep(symbols_update_interval)

class gateio_aoihttp_oifutureperp_manager(CommonFunctionality):
    
    def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
        super().__init__()
        self.underlying_asset = underlying_asset
        self.get_symbols = info
        self.fetcher = aiohttpfetch
        self._objectives = ["oi"]

    @CommonFunctionality.errors_aiohttp
    async def _calibrate_instruments(self, symbols_update_interval):
        """ there are no unique positions for every symbol from inverse margin. The positioning is encapsulated simply within underlyingasset_USD"""
        self.running["calibrate_instruments"] = True
        while self.running["calibrate_instruments"]:
            # current linear symbols
            current_symbols_linear, current_symbols_inverse, futures = await self.get_symbols(self.underlying_asset)
            
            for margin_type, instruments in zip(["linear", "inverse", "futures"], [current_symbols_linear, current_symbols_inverse, futures]):
                old_symbols = self._instruments.get(margin_type, [])
                instruments_to_remove = list(set(old_symbols) - set(instruments)) 
                instruments_to_add = list(set(instruments) - set(old_symbols))         
                self._instruments[margin_type] = instruments
                self._instruments_to_remove[margin_type] = instruments_to_remove
                self._instruments_to_add[margin_type] = instruments_to_add
                                                            
            self.symbol_check_tries = 0
            await asyncio.sleep(symbols_update_interval)

class gateio_aoihttp_posfutureperp_manager(CommonFunctionality):
    
    def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
        super().__init__()
        self.underlying_asset = underlying_asset
        self.get_symbols = info
        self.fetcher = aiohttpfetch
        self._objectives = ["tta"]

    @CommonFunctionality.errors_aiohttp
    async def _calibrate_instruments(self, symbols_update_interval):
        """ there are no unique positions for every symbol from inverse margin. The positioning is encapsulated simply within underlyingasset_USD"""
        self.running["calibrate_instruments"] = True
        while self.running["calibrate_instruments"]:
            # current linear symbols
            current_symbols_linear, current_symbols_inverse, futures = await self.get_symbols(self.underlying_asset)
            
            for margin_type, instruments in zip(["linear", "inverse"], [current_symbols_linear, current_symbols_inverse]):
                old_symbols = self._instruments.get(margin_type, [])
                instruments_to_remove = list(set(old_symbols) - set(instruments)) 
                instruments_to_add = list(set(instruments) - set(old_symbols))         
                self._instruments[margin_type] = instruments
                self._instruments_to_remove[margin_type] = instruments_to_remove
                self._instruments_to_add[margin_type] = instruments_to_add
                                                            
            self.symbol_check_tries = 0
            await asyncio.sleep(symbols_update_interval)

class htx_aiohttp_oifutureperp_manager(CommonFunctionality):
    
    def __init__ (self, underlying_asset, inverse_future_contract_types_htx, htx_aiohttpFetch:callable):
        super().__init__()
        self.underlying_asset = underlying_asset
        self.inverse_future_contract_types_htx = inverse_future_contract_types_htx
        self.fetcher = htx_aiohttpFetch
        self._objectives = ["oi"]

    @CommonFunctionality.errors_aiohttp
    async def _calibrate_instruments(self, *args, **kwargs):
        """ Reference"""
        self._instruments_to_add["future"] = self.inverse_future_contract_types_htx
        self._instruments_to_add["linear"] = ["-USDT.LinearPerpetual"]
        self._instruments_to_add["inverse"] = ["-USD"]

        self._instruments["future"] = self.inverse_future_contract_types_htx
        self._instruments["linear"] = ["-USDT.LinearPerpetual"]
        self._instruments["inverse"] = ["-USD"]
        
class htx_aiohttp_fundperp_manager(CommonFunctionality):
    
    def __init__ (self, underlying_asset, inverse_future_contract_types_htx, htx_aiohttpFetch:callable):
        super().__init__()
        self.underlying_asset = underlying_asset
        self.inverse_future_contract_types_htx = inverse_future_contract_types_htx
        self.fetcher = htx_aiohttpFetch
        self._objectives = ["funding"]

    @CommonFunctionality.errors_aiohttp
    async def _calibrate_instruments(self, *args, **kwargs):
        """ Reference"""
        self._instruments_to_add["linear"] = ["-USDT.LinearPerpetual"]
        self._instruments_to_add["inverse"] = ["-USD"]

        self._instruments["linear"] = ["-USDT"]
        self._instruments["inverse"] = ["-USD"]

class htx_aiohttp_posfutureperp_manager(CommonFunctionality):
    
    def __init__ (self, underlying_asset, inverse_future_contract_types_htx, htx_aiohttpFetch:callable):
        super().__init__()
        self.underlying_asset = underlying_asset
        self.inverse_future_contract_types_htx = inverse_future_contract_types_htx
        self.fetcher = htx_aiohttpFetch
        self._objectives = ["tta", "ttp"]

    @CommonFunctionality.errors_aiohttp
    async def _calibrate_instruments(self, *args, **kwargs):
        """ Reference"""
        self._instruments_to_add["perpetual"] = ["USDT", "USD", "USDT-FUTURES"]
        self._instruments_to_add["future"] = ["InverseFuture"]

        self._instruments["perpetual"] = ["USDT", "USD", "USDT-FUTURES"]
        self._instruments["future"] = ["InverseFuture"]




