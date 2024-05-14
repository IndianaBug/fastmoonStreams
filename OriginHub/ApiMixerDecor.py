from functools import wraps
import asyncio
import rapidjson as json
import re
from .utilis import *
from .clientpoints_.binance import binance_instType_help


def add_common_features(init_params, methods=None):
    """
    A decorator to add common features to a class.
    
    Args:
    - init_params (dict): A dictionary where keys are the names of the parameters and values are their default values.
    - methods (dict): A dictionary where keys are method names and values are the method implementations.
    """
    def decorator(cls):
        """decor"""
        def __init__(self, *args, **kwargs):
            for param, default in init_params.items():
                setattr(self, param, kwargs.get(param, default))
            for idx, param in enumerate(init_params.keys()):
                if idx < len(args):
                    setattr(self, param, args[idx])
            if hasattr(super(cls, self), '__init__'):
                super(cls, self).__init__(*args, **kwargs)
        cls.__init__ = __init__
        if methods:
            for method_name, method in methods.items():
                setattr(cls, method_name, method)
        
        return cls
    return decorator

async def get_instruments(self):
    expiries = await self.get_expiries(self.underlying_asset)
    self.expiries = expiries