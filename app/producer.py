import asyncio
import os
from utilis import get_nested_variable_from_yaml, get_yaml_variable
from OriginHub.SupplyEngine import publisher
#from .syncer import ExchangeAPIClient 

current_directory = os.path.dirname(os.path.abspath(__file__))
config_file_path = os.path.join(current_directory, '../configs/app_config.yaml')
streams_file_path = os.path.join(current_directory, '../configs/streams.yaml') 

# app configs
mode = get_yaml_variable(config_file_path, "mode")
spot_perp_future_configs = get_yaml_variable(config_file_path, "spot_perpetual_future_data_aggregation")
option_configs = get_yaml_variable(config_file_path, "option_data_aggregation")
merge_weighting_factor_configs = get_yaml_variable(config_file_path, "merge_weighting_factor")
initial_price_symbols = get_yaml_variable(config_file_path, "initial_price")
fallback_symbols_perpetual_future = get_yaml_variable(config_file_path, "fallback_symbols_perpetual_future")
fallback_symbols_option = get_yaml_variable(config_file_path, "fallback_symbols_option")

# data_streams

streams_dicrionary = get_yaml_variable(streams_file_path)
# build stream_data here

# keys passwords
coinbase_api = os.getenv("COINBASE_API")
coinbase_secret = os.getenv("COINBASE_SECRET")
kucoin_api = os.getenv("KUCOIN_API")
kucoin_secret = os.getenv("KUCOIN_SECRET")
kucoin_pass = os.getenv("KUCOIN_PASS")

# client = ExchangeAPIClient(
#     coinbase_api, 
#     coinbase_secret,
#     kucoin_api,
#     kucoin_secret, 
#     kucoin_pass, 
#     price_level_size=20, 
#     process_interval=10,
#     mode="testing",
#     option_process_interval=2
#     )

# streams_data = client.build_connection_data(ws, api)


# for e in streams_data:
#     print(e)
#     print()

# __name__ = "__main__"

# if __name__ == '__main__':
#     cryptoProducer = publisher(streams_data)
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     loop.run_until_complete(cryptoProducer.run_producer())
