from syncer import ExchangeAPIClient, binance_get_marginType, bybit_get_marginType
from config import coinbase_secret, coinbase_api, kucoin_api, kucoin_pass, kucoin_secret, fiats, stablecoins



client = ExchangeAPIClient(
    coinbase_api, 
    coinbase_secret,
    kucoin_api,
    kucoin_secret, 
    kucoin_pass, 
    price_level_size=20, 
    process_interval=10,
    mode="testing",
    option_process_interval=2
    )

api = "get api streams from yaml"
ws = "get_ws_from_yamls"

streams_data = client.build_connection_data(ws, api)


for e in streams_data:
    print(e)
    print()