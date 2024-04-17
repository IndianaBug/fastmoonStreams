# Note:
# The Instruments must be of the same format (upper lower with hiphens) as in API calls. 
# You may merge streams with the same channels (objectives).
# Bybit/Binance derivate perpetual futures must be sepparated by instrument type, use provided helpers

from syncer import ExchangeAPIClient
from config import coinbase_secret, coinbase_api, kucoin_api, kucoin_pass, kucoin_secret


client = ExchangeAPIClient(coinbase_api, coinbase_secret, kucoin_api, kucoin_secret, kucoin_pass)
all_instruments = client.retrieve_all_instruments()
symbols = client.get_related_instruments(all_instruments, ["BTC", "BTC", "XBT"], ["PERP", "USD", "USD"], ["option", "future"])
print(symbols)
print([x for x in client.okx_symbols_by_instType("future") if "BTC" in x])



