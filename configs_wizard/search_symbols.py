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



import sys
import argparse
from syncer import ExchangeAPIClient
from config import coinbase_secret, coinbase_api, kucoin_api, kucoin_pass, kucoin_secret

def main():
    parser = argparse.ArgumentParser(description="Find related symbols based on given criteria.")
    parser.add_argument('--base', nargs='+', required=True, help="Base symbols, e.g., ['BTC', 'BTC', 'XBT']")
    parser.add_argument('--quote', nargs='+', required=True, help="Quote symbols, e.g., ['PERP', 'USD', 'USD']")
    parser.add_argument('--type', nargs='+', required=True, help="Instrument types, e.g., ['option', 'future']")

    args = parser.parse_args()

    client = ExchangeAPIClient(coinbase_api, coinbase_secret, kucoin_api, kucoin_secret, kucoin_pass)
    all_instruments = client.retrieve_all_instruments()
    symbols = client.get_related_instruments(all_instruments, args.base, args.quote, args.type)
    print(symbols)

if __name__ == "__main__":
    main()
    
    
    
# @echo off
# python path\to\your\script\symbol_finder.py --base BTC BTC XBT --quote PERP USD USD --type option future
# pause


#!/bin/bash
# chmod +x run_symbol_finder.sh
# python3 path/to/your/script/symbol_finder.py --base BTC BTC XBT --quote PERP USD USD --type option future