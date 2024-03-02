from utilis import *

AaWS = [
    # updateSpeed in seconds

    # Binance APIs : https://binance-docs.github.io/apidocs/spot/en/#change-log
    #                 https://binance-docs.github.io/apidocs/futures/en/#change-log
    #                 https://binance-docs.github.io/apidocs/delivery/en/#change-log
    # OKEx APIs:     https://www.okx.com/docs-v5/en/?python#public-data-rest-api-get-instruments
    # Bybit APIs:    https://bybit-exchange.github.io/docs/v5/intro
    # Deribit APIs:  https://docs.deribit.com/#deribit-api-v2-1-1
    # Kucoin APIs :  https://www.kucoin.com/docs/rest/spot-trading/market-data/get-full-order-book-aggregated-

    ###
    # Depth
    ###
    {
        "type" : "api",
        "id" : "binance_spot_btcusdt_depth",
        "exchange":"binance", 
        "instrument": "btcusdt", 
        "insType":"spot", 
        "obj":"depth", 
        "updateSpeed" : 1, 
        "url" : f"https://api.binance.com/api/v3/depth?symbol=BTCUSDT"
        },
    {
        "type" : "api",
        "id" : "binance_spot_btcfdusd_depth",
        "exchange":"binance",
        "instrument": "btcfdusd", 
        "insType":"spot", 
        "obj":"depth", 
        "updateSpeed":1, 
        "url" : f"https://api.binance.com/api/v3/depth?symbol=BTCFDUSD"
    },
    {
        "type" : "api",
        "id" : "binance_perpetual_btcusdt_depth",
        "exchange":"binance", 
        "instrument": "btcusdt",
        "insType":"perpetual", 
        "obj":"depth", 
        "updateSpeed":1,
        "url" : f"https://fapi.binance.com/fapi/v1/depth?symbol=BTCUSDT"
    },
    {
        "type" : "api",
        "id" : "binance_perpetual_btcusd_depth",
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument": "btcusd", 
        "updateSpeed":1, 
        "url" : f"https://dapi.binance.com/dapi/v1/depth?symbol=BTCUSD_PERP"
    },
    {
        "type" : "api",
        "id" : "bybit_spot_btcusdt_depth",
        "exchange":"bybit", 
        "insType":"spot", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1, 
        "url" : "https://api.bybit.com/v5/market/orderbook?category=spot&symbol=BTCUSDT&limit=200"
    },
    {
        "type" : "api",
        "id" : "bybit_spot_btcusdc_depth",
        "exchange":"bybit", 
        "insType":"spot", 
        "obj":"depth", 
        "instrument": "btcusdc",
        "updateSpeed":1, 
        "url" : "https://api.bybit.com/v5/market/orderbook?category=spot&symbol=BTCUSDC&limit=200"
    },
    {
        "type" : "api",
        "id" : "bybit_perpetual_btcusdt_depth",
        "exchange":"bybit", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1, 
        "url" : "https://api.bybit.com/v5/market/orderbook?category=linear&symbol=BTCUSDT&limit=200"
    },
    {
        "type" : "api",
        "id" : "bybit_perpetual_btcusd_depth",
        "exchange":"bybit", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument": "btcusd",
        "updateSpeed":1, 
        "url" : "https://api.bybit.com/v5/market/orderbook?category=linear&symbol=BTCUSD&limit=200"
    },
    {
        "type" : "api",
        "id" : "coinbase_spot_btcusd_depth",
        "exchange":"coinbase", 
        "insType":"spot", 
        "obj":"depth", 
        "instrument": "btcusd",
        "updateSpeed":1,
        "url_base" :  "api.coinbase.com",
        "url" : "/api/v3/brokerage/product_book?product_id=BTC-USD"
    },
    {
        "type" : "api",
        "id" : "kucoin_spot_btcusdt_depth",
        "exchange":"kucoin", 
        "insType":"spot", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://api.kucoin.com/api/v3/market/orderbook/level2?symbol=BTC-USDT",
        "headers" : build_kucoin_headers_spot()         
    },
    {
        "type" : "api",
        "id" : "kucoin_perpetual_btcusdt_depth",
        "exchange":"kucoin", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://api-futures.kucoin.com/api/v1/level2/snapshot?symbol=XBTUSDTM",
        "headers" : build_kucoin_headers_futures()         
    },
    {
        "type" : "api",
        "id" : "gateio_spot_btcusdt_depth",
        "exchange":"gateio", 
        "insType":"spot", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://api.gateio.ws/api/v4/spot/order_book?currency_pair=BTC_USDT",
        "headers" : {'Accept': 'application/json', 'Content-Type': 'application/json'}          # requests.request('GET', url, headers=headers)
    },
    {
        "type" : "api",
        "id" : "gateio_perpetual_btcusdt_depth",
        "exchange":"gateio", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://api.gateio.ws/api/v4/futures/usdt/order_book?contract=BTC_USDT",
        "headers" : {'Accept': 'application/json', 'Content-Type': 'application/json'}          
    },
    {
        "type" : "api",
        "id" : "mexc_spot_btcusdt_depth",
        "exchange":"mexc", 
        "insType":"spot", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://api.mexc.com/api/v3/depth?symbol=BTCUSDT&limit=5000", # simple get request
    },
    {
        "type" : "api",
        "id" : "mexc_perpetual_btcusdt_depth",
        "exchange":"mexc", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://contract.mexc.com/api/v1/contract/depth/BTC_USDT", # simple get request
    },
    {
        "type" : "api",
        "id" : "bitget_spot_btcusdt_depth",
        "exchange":"bitget", 
        "insType":"spot", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://api.bitget.com/api/v2/spot/market/orderbook?symbol=BTCUSDT&type=step0&limit=150" , # simple get request
    },
    {
        "type" : "api",
        "id" : "bitget_perpetual_btcusdt_depth",
        "exchange":"bitget", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://api.bitget.com/api/v2/mix/market/merge-depth?productType=usdt-futures&symbol=BTCUSDT&limit=1000", 
    },
    {
        "type" : "api",
        "id" : "htx_spot_btcusdt_depth",
        "exchange":"htx", 
        "insType":"spot", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://api.huobi.pro/market/depth?symbol=btcusdt&depth=20&type=step0", 
    },
    {
        "type" : "api",
        "id" : "htx_perpetual_btcusdt_depth",
        "exchange":"htx", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://api.hbdm.com/linear-swap-ex/market/depth?contract_code=BTC-USDT&type=step0", 
    },
    {   # Can only be called with websockets
        "type" : "api",
        "id" : "deribit_perpetual_btcusd_depth",
        "exchange":"deribit", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument":"btcusd", 
        "updateSpeed": 5,
        "url" : "wss://test.deribit.com/ws/api/v2",  
        "headers" : {
            "jsonrpc": "2.0", "id": generate_random_integer(10), 
            "method": "public/get_order_book",
            "params": { 
                "depth": 1000, 
                "instrument_name": "BTC-PERPETUAL"
                }
            }
    },
    {
        "type" : "api",
        "id" : "bingx_perpetual_btcusdt_depth",  
        "exchange":"bingx", 
        "insType":"perpetual", 
        "obj":"depth", 
        "instrument":"btcusdt", 
        "updateSpeed": 5,
        "url" : "https://open-api.bingx.com",  
        "path" : "/openApi/swap/v2/quote/depth",
        "params" : {
                    "symbol": "BTC-USDT",
                    "limit": "1000"
                    }
    },
    {
        "type" : "api",  
        "id" : "bingx_spot_btcusdt_depth",  
        "exchange":"bingx", 
        "insType":"spot", 
        "obj":"depth", 
        "instrument":"btcusdt", 
        "updateSpeed": 1,
        "url" : "https://open-api.bingx.com",  
        "path" : "/openApi/spot/v1/market/depth",
        "params" : {
                    "symbol": "BTC-USDT",
                    "limit": "1000"
                    }
    },
    ###
    # Funding rate
    ###
    {
        "type" : "api",
        "id" : "binance_perpetual_btcusd_fundingRate",
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"fundingRate", 
        "instrument": "btcusd", 
        "updateSpeed": 1000,  # 360 
        "url" : "https://dapi.binance.com/dapi/v1/fundingRate?symbol=BTCUSD_PERP&limit=1"
    },
    {
        "type" : "api",
        "id" : "binance_perpetual_btcusdt_fundingRate",
        "exchange":"binance",
        "insType":"perpetual", 
        "obj":"fundingRate",
        "instrument": "btcusdt", 
        "updateSpeed":1000,  # 360 
        "url" : "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1"
    },
    {
        "type" : "api",
        "id" : "htx_perpetual_btcusdt_fundingRate",
        "exchange":"htx", 
        "insType":"perpetual", 
        "obj":"fundingRate", 
        "instrument": "btcusdt", 
        "updateSpeed":1000, 
        "url" : "https://api.hbdm.com/index/market/history/linear_swap_estimated_rate_kline?contract_code=BTC-USDT&period=1min&size=1"
    },
    {
        "type" : "api",  
        "id" : "bingx_perpetual_btcusdt_OI",  
        "exchange":"bingx", 
        "insType":"perpetual", 
        "obj":"OI", 
        "instrument":"btcusdt", 
        "updateSpeed": 5,
        "url" : "https://open-api.bingx.com",  
        "path" : "/openApi/swap/v2/quote/openInterest",
        "params" : {
                    "symbol": "BTC-USDT",
                    }
    },
    ###
    # OI
    ###
    {
        "type" : "api",
        "id" : "binance_perpetual_btcusdt_OI",
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"OI", 
        "instrument": "btcusdt", 
        "updateSpeed":3, 
        "url" : "https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT"
    },
    {
        "type" : "api",
        "id" : "binance_perpetual_btcusd_OI",
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"OI", 
        "instrument": "btcusd", 
        "updateSpeed":3, 
        "url" : "https://dapi.binance.com/dapi/v1/openInterest?symbol=BTCUSD_PERP"
    },
    {
        "type" : "api",
        "id" : "htx_perpetual_btcusdt_OI",
        "exchange":"htx", 
        "insType":"perpetual", 
        "obj":"OI", 
        "instrument": "btcusdt", 
        "updateSpeed":3, 
        "url" : "https://api.hbdm.com/linear-swap-api/v1/swap_his_open_interest?contract_code=BTC-USDT&period=60min&amount_type=1"
    },
    {
        "type" : "api",  
        "id" : "bingx_perpetual_btcusdt_fundingRate",  
        "exchange":"bingx", 
        "insType":"perpetual", 
        "obj":"fundingRate", 
        "instrument":"btcusdt", 
        "updateSpeed": 1000,
        "url" : "https://open-api.bingx.com",  
        "path" : "/openApi/swap/v2/quote/premiumIndex",
        "params" : {
                    "symbol": "BTC-USDT",
                    }
    },
    ###
    # Funding + OI
    ###
    {
        "type" : "api",
        "id" : "gateio_perpetual_btcusdt_fundingOI",
        "exchange":"gateio", 
        "insType":"perpetual", 
        "obj":"fundingOI", 
        "instrument": "btcusdt", 
        "updateSpeed":3, 
        "url" : "https://api.gateio.ws/api/v4/futures/usdt/contracts/BTC_USDT",
        "headers" : {'Accept': 'application/json', 'Content-Type': 'application/json'}
    },
    {
        "type" : "api",
        "id" : "kucoin_perpetual_btcusdt_fundingOI",
        "exchange":"kucoin", 
        "insType":"perpetual", 
        "obj":"fundingOI", 
        "instrument": "btcusdt",
        "updateSpeed":1,
        "url" : "https://api-futures.kucoin.com/api/v1/contracts/XBTUSDTM",
        "headers" : build_kucoin_headers_futures()         
    },
    ###
    # Liquidation History
    ###
    {  # https://www.gate.io/docs/developers/apiv4/en/#retrieve-liquidation-history
        "type" : "api",
        "id" : "gateio_perpetual_btcusdt_liquidations",
        "exchange":"gateio", 
        "insType":"perpetual", 
        "obj":"liquidations", 
        "instrument": "btcusdt", 
        "updateSpeed":3, 
        "url" : f"https://api.gateio.ws/api/v4/futures/usdt/liq_orders?s=BTC_USDT&from={int(time.time()) - 10}&to={int(time.time())}",
        "headers" : {'Accept': 'application/json', 'Content-Type': 'application/json'}
    },    
    ###
    # Top Trades Accounts
    ###
    {
        "type" : "api",
        "id" : "binance_perpetual_btcusdt_TTA",
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"TTA", 
        "instrument": "btcusdt", 
        "updateSpeed":10,  # 300 
        "url" : "https://fapi.binance.com/futures/data/topLongShortAccountRatio?symbol=BTCUSDT&period=5m&limit=1"
    },
    {
        "type" : "api",
        "id" : "binance_perpetual_btcusd_TTA",
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"TTA", 
        "instrument": "btcusd", 
        "updateSpeed":10, 
        "url" : "https://dapi.binance.com/futures/data/topLongShortAccountRatio?pair=BTCUSD&period=5m&limit=1"
    },
    ###
    # Top Trades Positions
    ###
    {
        "type" : "api",
        "id" : "binance_perpetual_btcusdt_TTP",
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"TTP", 
        "instrument": "btcusdt", 
        "updateSpeed":10, 
        "url" : "https://fapi.binance.com/futures/data/topLongShortPositionRatio?symbol=BTCUSDT&period=5m&limit=1"
    },
    {
        "type" : "api",
        "id" : "binance_perpetual_btcusd_TTP",
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"TTP", 
        "instrument": "btcusd", 
        "updateSpeed":10, 
        "url" : "https://dapi.binance.com/futures/data/topLongShortPositionRatio?pair=BTCUSD&period=5m&limit=1"
    },
    ###
    # Global Traders Accounts
    ##
    {
        "type" : "api",
        "id" : "binance_perpetual_btcusdt_GTA",
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"GTA", 
        "instrument": "btcusdt", 
        "updateSpeed":10, 
        "url" : "https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol=BTCUSDT&period=5m&limit=1"
    },
    {
        "type" : "api",
        "id" : "binance_perpetual_btcusd_GTA",
        "exchange":"binance", 
        "insType":"perpetual", 
        "obj":"GTA", 
        "instrument": "btcusd", 
        "updateSpeed":10, 
        "url" : "https://dapi.binance.com/futures/data/globalLongShortAccountRatio?pair=BTCUSD&period=5m&limit=1"
    },
    {
        "type" : "api",
        "id" : "okx_perpetual_btc_GTA",
        "exchange":"okx", 
        "insType":"perpetual", 
        "obj":"GTA", 
        "updateSpeed":10, 
        "instrument": "btcusd", 
        "url" : f"https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio?ccy=BTC&period=5m"
    }, 
    {
        "type" : "api",
        "id" : "bybit_perpetual_btcusdt_GTA",
        "exchange":"bybit", 
        "insType":"perpetual", 
        "obj":"GTA", 
        "instrument": "btcusdt", 
        "updateSpeed":10, 
        "url" : "https://api.bybit.com/v5/market/account-ratio?category=linear&symbol=BTCUSDT&period=1d&limit=50" # the minimum limit
    },
    {
        "type" : "api",
        "id" : "bybit_perpetual_btcusd_GTA",
        "exchange":"bybit", 
        "insType":"perpetual", 
        "obj":"GTA", 
        "instrument": "btcusd", 
        "updateSpeed":10, 
        "url" : "https://api.bybit.com/v5/market/account-ratio?category=linear&symbol=BTCUSD&period=1d&limit=50" # the minimum limit
    },
    ###
    # Options OI
    ## 
    {   # Can only be called with websockets
        "type" : "api",
        "id" : "deribit_option_btc_OI",
        "exchange":"deribit", 
        "insType":"option", 
        "obj":"OI", 
        "instrument":"btcusd", 
        "updateSpeed":1800,
        "url" : "wss://test.deribit.com/ws/api/v2",  
        "msg" : {
            "jsonrpc": "2.0", "id": generate_random_integer(10), 
            "method": "public/get_book_summary_by_currency",
            "params": { 
                "currency": "BTC", 
                "kind": "option"
                }
            }
    },
    {
        "type" : "api",
        "id" : "bybit_option_btc_OI",
        "exchange":"bybit", 
        "insType":"option", 
        "obj":"OI", 
        "instrument": "btcusdt",
        "updateSpeed":1800, 
        "url" : "https://api.bybit.com/v5/market/tickers?category=option&baseCoin=BTC"
    },
    {
        "type" : "api",
        "id" : "okx_option_btc_OI",
        "exchange":"okx", 
        "insType":"option", 
        "obj":"OI", 
        "instrument": "btc",
        "updateSpeed":1800, 
        "url" : f"https://www.okx.com/api/v5/public/open-interest?instType=OPTION&instFamily=BTC-USD"
    },
    ###
    # News Aggregator
    ###
    {
        "type" : "api",
        "id"   :  "cryptopanic",
        "exchange":"ALL", 
        "insType":"news", 
        "obj":"aggregator", 
        "instrument":"BTC_USDT_ETH",
        "updateSpeed":30,  # We use server-side caching, so there is no point of making requests more than once every 30 seconds.  https://cryptopanic.com/developers/api/
        "url" : f'https://cryptopanic.com/api/v1/posts/?auth_token={crypto_panic_token}&public=true&currencies=BTC,USDT,ETH&region=en'
    },
    ###
    # Set heartbeat
    ###  
    {   # Can only be called with websockets
        "type" : "api",
        "id" : "deribit_hearbeat",
        "exchange":"deribit", 
        "insType":"hearbeat", 
        "obj":"heartbeat", 
        "instrument":"btcusd", 
        "updateSpeed":1800,
        "url" : "wss://test.deribit.com/ws/api/v2",  
        "msg" : {
            "jsonrpc": "2.0", "id": generate_random_integer(10), 
            "method": "public/set_heartbeat",
            "params":  {
                        "interval" : 30
                       }
            }
    },    

        # Binance spot APIs: https://binance-docs.github.io/apidocs/spot/en/#change-log
        # Binance usdt APIs: https://binance-docs.github.io/apidocs/futures/en/#change-log
        # Binance coin APIs: https://binance-docs.github.io/apidocs/delivery/en/#change-log
        # OKEx: https://www.okx.com/docs-v5/en/?python#public-data-websocket-funding-rate-channel
        # Bybit: https://www.bybit.com/future-activity/en/developer
        # Coinbase: https://docs.cloud.coinbase.com/exchange/docs/websocket-channels
        # Derebit: https://docs.deribit.com/
        ###
        # Trades
        ###
        {
          "type" : "websocket",
          "id" : "deribit_option_btc_OI",
          "exchange":"binance", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://stream.binance.com:9443/ws",
          "msg" : {
              "method": "SUBSCRIBE", 
              "params": ["btcusdt@aggTrade"], 
              "id": generate_random_integer(10)
              }
        },
        {
          "type" : "websocket",
          "id" : "binance_spot_btcfdusd_trades",
          "exchange":"binance", 
          "instrument": "btcfdusd", 
          "insType":"spot", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://stream.binance.com:9443/ws",
          "msg" : {
              "method": "SUBSCRIBE", 
              "params": ["btcfdusd@aggTrade"], 
              "id": generate_random_integer(10)
              }
        },
        {
          "type" : "websocket",
          "id" : "binance_spot_btcusdt_trades",
          "exchange":"binance", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://stream.binance.com:9443/ws",
          "msg" : {
              "method": "SUBSCRIBE", 
              "params": ["btcfdusd@aggTrade"], 
              "id": generate_random_integer(10)
              }
        },
        {
          "type" : "websocket",
          "id" : "binance_perpetual_btcusdt_trades",
          "exchange":"binance", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://fstream.binance.com/ws",
          "msg" : {
              "method": "SUBSCRIBE", 
              "params": ["btcusdt@aggTrade"], 
              "id": generate_random_integer(10)
              }
        },
        {
          "type" : "websocket",
          "id" : "binance_perpetual_btcusd_trades",
          "exchange":"binance", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://dstream.binance.com/ws",
          "msg" : {
              "method": "SUBSCRIBE", 
              "params": ["btcusd_perp@aggTrade"], 
              "id": generate_random_integer(10)
              }
        },
        {
          "type" : "websocket",
          "id" : "okx_perpetual_btcusdt_trades",
          "exchange":"okx", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'trades', 'instId': 'BTC-USDT-SWAP'
                      }
              ]
              }
        },
        {
          "type" : "websocket",
          "id" : "okx_perpetual_btcusd_trades",
          "exchange":"okx", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'trades', 'instId': 'BTC-USD-SWAP'
                      }
              ]
              }
        },
        {
          "type" : "websocket",
          "id" : "okx_spot_btcusdt_trades",
          "exchange":"okx", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'trades', 'instId': 'BTC-USDT'
                      }
              ]
              }
        },
        {
          "type" : "websocket",
          "id" : "bybit_spot_btcusdt_trades",
          "exchange":"bybit", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://stream.bybit.com/v5/public/spot",
          "msg" : {
              "op": 
              "subscribe","args": [
                  "publicTrade.BTCUSDT"
                  ]
              }
        },
        {
          "type" : "websocket",
          "id" : "bybit_spot_btcusdc_trades",
          "exchange":"bybit", 
          "instrument": "btcusdc", 
          "insType":"spot", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://stream.bybit.com/v5/public/spot",
          "msg" : {
              "op": 
              "subscribe","args": [
                  "publicTrade.BTCUSDC"
                  ]
              }
        },
        {
          "type" : "websocket",
          "id" : "bybit_perpetual_btcusdt_trades",
          "exchange":"bybit", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://stream.bybit.com/v5/public/linear",
          "msg" : {
              "op": "subscribe",
              "args": [
                  "publicTrade.BTCUSDT"
                  ]
              }
        },
        {
          "type" : "websocket",
          "id" : "bybit_perpetual_btcusd_trades",
          "exchange":"bybit", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://stream.bybit.com/v5/public/linear",
          "msg" : {
              "op": "subscribe",
              "args": [
                  "publicTrade.BTCPERP"
                  ]
              }
        },
        {
          "type" : "websocket",
          "id" : "coinbase_spot_btcusd_trades",
          "exchange":"coinbase", 
          "instrument": "btcusd", 
          "insType":"spot", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://advanced-trade-ws.coinbase.com",
          "msg" : {
              "type": "subscribe",
              "product_ids": ["BTC-USD"],
              "channel": "market_trades",
              "jwt": build_jwt_websockets(),
              "timestamp": int(time.time())
              }     
        },
        {
          "type" : "websocket",
          "id" : "kucoin_spot_btcusdt_trades",  
          "exchange":"kucoin", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : build_kucoin_wsendpoint(),
          "msg" : {
                    "id": generate_random_integer(10),   
                    "type": "subscribe",
                    "topic": "/market/match:BTC-USDT",
                    "response": True
                    }
        },
        {
          "type" : "websocket",
          "id" : "kucoin_perpetual_btcusdt_trades",
          "exchange":"kucoin", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : build_kucoin_wsendpoint(),
          "msg" : {
                    "id": generate_random_integer(10),   
                    "type": "subscribe",
                    "topic": "/contractMarket/execution:XBTUSDTM",
                    "response": True
                    }
        },
        {
          "type" : "websocket",
          "id" : "gateio_spot_btcusdt_trades",
          'exchange':'gateio', 
          'instrument': 'btcusdt', 
          'insType':'spot', 
          'obj':'trades', 
          'updateSpeed' : 0, 
          'url' : "wss://api.gateio.ws/ws/v4/",
          'msg' : {
                        "time": int(time.time()),
                        "channel": "spot.trades",
                        "event": "subscribe",  
                        "payload": ["BTC_USDT"]
                    }
        },
        { # https://www.gate.io/docs/developers/futures/ws/en/#trades-api
          "type" : "websocket",
          "id" : "gateio_perpetual_btcusdt_trades",
          'exchange':'gateio', 
          'instrument': 'btcusdt', 
          'insType':'perpetual', 
          'obj':'trades', 
          'updateSpeed' : 0, 
          'url' : "wss://fx-ws-testnet.gateio.ws/v4/ws/btc",
          'msg' : {
                        "time": int(time.time()),
                        "channel": "futures.trades",
                        "event": "subscribe",  
                        "payload": ["BTC_USDT"]
                    }
        },
        {
          "type" : "websocket",
          "id" : "mexc_spot_btcusdt_trades",
          "exchange":"mexc", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://wbs.mexc.com/ws",
          "msg" : {
                        "method": "SUBSCRIPTION",
                        "params": [
                            "spot@public.deals.v3.api@BTCUSDT"
                        ]
                    }
        },
        {
          "type" : "websocket",
          "id" : "mexc_perpetual_btcusdt_trades",
          "exchange":"mexc", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://contract.mexc.com/edge",
          "msg" : {
                    "method":"sub.deal",
                    "param":{
                        "symbol":"BTC_USDT"
                    }
                }
        },
        {
          "type" : "websocket",
          "id" : "bitget_spot_btcusdt_trades",
          "exchange":"bitget", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://ws.bitget.com/v2/ws/public",
          "msg" : {
                    "op": "subscribe",
                    "args": [
                        {
                            "instType": "SPOT",
                            "channel": "trade",
                            "instId": "BTCUSDT"
                        }
                    ]
                }
        },
        {
          "type" : "websocket",
          "id" : "bitget_perpetual_btcusdt_trades",
          "exchange":"bitget", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://ws.bitget.com/v2/ws/public",
          "msg" : {
                    "op": "subscribe",
                    "args": [
                        {
                            "instType": "USDT-FUTURES",
                            "channel": "trade",
                            "instId": "BTCUSDT"
                        }
                    ]
                }
        },
        { 
           "type" : "websocket",  
            "id" : "deribit_perpetual_btcusd_trades",
            "exchange":"deribit", 
            "insType":"perpetual", 
            "obj":"trades", 
            "instrument":"btcusd", 
            "updateSpeed":0,
            "url" : "wss://test.deribit.com/ws/api/v2",  
            "msg" : {
                    "jsonrpc": "2.0",
                    "method": "public/subscribe",
                    "id": generate_random_integer(10),
                    "params": {
                        "channels": ["trades.BTC-PERPETUAL.100ms"]}
                    }
        },
        {
          "type" : "websocket",
          "id" : "htx_spot_btcusdt_trades",
          "exchange":"htx", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://api-aws.huobi.pro/ws",
          "msg" : {
                    "sub" : "market.btcusdt.trade.detail",
                    "id" : generate_random_integer(10)
                    }
        }, 
        {
          "type" : "websocket",
          "id" : "htx_perpetual_btcusdt_trades",
          "exchange":"htx", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://api.hbdm.com/linear-swap-ws",
          "msg" : {
                    "sub" : "market.BTC-USDT.trade.detail",
                    "id" : generate_random_integer(10)
                    }
        },
        {
          "type" : "websocket",
          "id" : "bingx_spot_btcusdt_trades",
          "exchange":"bingx", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://open-api-ws.bingx.com/market",
          "msg" : {"id":generate_random_id(20),
                   "reqType": "sub",
                   "dataType":"BTC-USDT@trade"}
        },  
        {
          "type" : "websocket",
          "id" : "bingx_perpetual_btcusdt_trades",
          "exchange":"bingx", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"trades", 
          "updateSpeed" : 0, 
          "url" : "wss://open-api-swap.bingx.com/swap-market",
          "msg" : {
                   "id" : generate_random_id(20),
                   "reqType": "sub",
                   "dataType":"BTC-USDT@trade"
                   }
        },                     
        ###
        # Depth
        ###
        {
          "type" : "websocket",
          "id" : "binance_spot_btcusdt_depth",
          "exchange":"binance", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"depth", 
          "updateSpeed" : 1, 
          "url" : "wss://stream.binance.com:9443/ws",
          "msg" : {
              "method": "SUBSCRIBE", 
              "params": ["btcusdt@depth@1000ms"], 
              "id": generate_random_integer(10)
              }
        },
        {
          "type" : "websocket",
          "id" : "binance_spot_btcfdusd_depth",
          "exchange":"binance", 
          "instrument": "btcfdusd", 
          "insType":"spot", 
          "obj":"depth", 
          "updateSpeed" : 1, 
          "url" : "wss://stream.binance.com:9443/ws",
          "msg" : {
              "method": "SUBSCRIBE", 
              "params": ["btcfdusd@depth@1000ms"], 
              "id": generate_random_integer(10)
              }
        },
        {
          "type" : "websocket",
          "id" : "binance_perpetual_btcusdt_depth",
          "exchange":"binance", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"depth", 
          "updateSpeed" : 0.5, 
          "url" : "wss://stream.binance.com:9443/ws",
          "msg" : {
              "method": "SUBSCRIBE", 
              "params": ["btcusdt@depth@500ms"], 
              "id": generate_random_integer(10)
              }
        },
        {
          "type" : "websocket",
          "id" : "binance_perpetual_btcusd_depth",
          "exchange":"binance", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"depth", 
          "updateSpeed" : 0.5, 
          "url" : "wss://dstream.binance.com/ws",
          "msg" : {
              "method": "SUBSCRIBE", 
              "params": ["btcusd_perp@depth@500ms"], 
              "id": generate_random_integer(10)
              }
        },
        {
          "type" : "websocket",
          "id" : "okx_perpetual_btcusdt_depth",
          "exchange":"okx", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"depth", 
          "updateSpeed" : 0.5, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'books', 'instId': 'BTC-USDT'
                      }
              ]
              }
        },
        {
          "type" : "websocket",
          "id" : "okx_perpetual_btcusd_depth",
          "exchange":"okx", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"depth", 
          "updateSpeed" : 0.5, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'books', 'instId': 'BTC-USD-SWAP'
                      }
              ]
              }
        },
        {
          "type" : "websocket",
          "id" : "okx_spot_btcusdt_depth",
          "exchange":"okx", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"depth", 
          "updateSpeed" : 0.5, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'books', 'instId': 'BTC-USDT'
                      }
              ]
              }
        },
        {
          "type" : "websocket",
          "id" : "bybit_spot_btcusdt_depth",
          "exchange":"bybit", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"depth", 
          "updateSpeed" : 0.2, 
          "url" : "wss://stream.bybit.com/v5/public/spot",
          "msg" : {
              "op": 
              "subscribe","args": [
                  "orderbook.200.BTCUSDT"
                  ]
              }
        },
        {
          "type" : "websocket",
          "id" : "bybit_spot_btcusdc_depth",
          "exchange":"bybit", 
          "instrument": "btcusdc", 
          "insType":"spot", 
          "obj":"depth", 
          "updateSpeed" : 0.2, 
          "url" : "wss://stream.bybit.com/v5/public/spot",
          "msg" : {
              "op": 
              "subscribe","args": [
                  "orderbook.200.BTCUSDC"
                  ]
              }
        },
        {
          "type" : "websocket",
          "id" : "bybit_perpetual_btcusdt_depth",
          "exchange":"bybit", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"depth", 
          "updateSpeed" : 0.2, 
          "url" : "wss://stream.bybit.com/v5/public/linear",
          "msg" : {
              "op": 
              "subscribe","args": [
                  "orderbook.200.BTCUSDT"
                  ]
              }
        },
        {
          "type" : "websocket",
          "id" : "bybit_perpetual_btcusd_depth",
          "exchange":"bybit", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"depth", 
          "updateSpeed" : 0.2, 
          "url" : "wss://stream.bybit.com/v5/public/linear",
          "msg" : {
              "op": 
              "subscribe","args": [
                  "orderbook.200.BTCPERP"
                  ]
              }
        },
        {
          "type" : "websocket",
          "id" : "coinbase_spot_btcusd_depth",
          "exchange":"coinbase", 
          "instrument": "btcusd", 
          "insType":"spot", 
          "obj":"depth", 
          "updateSpeed" : 0, 
          "url" : "wss://advanced-trade-ws.coinbase.com",
          "msg" : {
              "type": "subscribe",
              "product_ids": ["BTC-USD"],
              "channel": "level2",
              "jwt": build_jwt_websockets(),
              "timestamp": int(time.time())
              }     
        },
        {
          "type" : "websocket",
          "id" : "kucoin_spot_btcusdt_depth",
          "exchange":"kucoin", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"depth", 
          "updateSpeed" : 0, 
          "url" : build_kucoin_wsendpoint(),
          "msg" : {
                    "id": generate_random_integer(10),   
                    "type": "subscribe",
                    "topic": "/market/level2:BTC-USDT",
                    "response": True
                    }
        },
        {
          "type" : "websocket",
          "id" : "kucoin_perpetual_btcusdt_depth",
          "exchange":"kucoin", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"depth", 
          "updateSpeed" : 0, 
          "url" : build_kucoin_wsendpoint(),
          "msg" : {
                    "id": generate_random_integer(10),   
                    "type": "subscribe",
                    "topic": "/contractMarket/level2:XBTUSDTM",
                    "response": True
                    }
        },
        {
          "type" : "websocket",
          "id" : "gateio_spot_btcusdt_depth",
          'exchange':'gateio', 
          'instrument': 'btcusdt', 
          'insType':'spot', 
          'obj':'depth', 
          'updateSpeed' : 0, 
          'url' : "wss://api.gateio.ws/ws/v4/",
          'msg' : {
                        "time": int(time.time()),
                        "channel": "spot.order_book_update",
                        "event": "subscribe",  
                        "payload": ["BTC_USDT", "1000ms"]
                    }

        },
        {
          "type" : "websocket",
          "id" : "gateio_perpetual_btcusdt_depth",
          'exchange':'gateio', 
          'instrument': 'btcusdt', 
          'insType':'perpetual', 
          'obj':'depth', 
          'updateSpeed' : 0, 
          'url' : "wss://fx-ws-testnet.gateio.ws/v4/ws/btc",
          'msg' : {
                        "time": int(time.time()),
                        "channel": "futures.order_book_update",
                        "event": "subscribe",  
                        "payload": ["BTC_USDT", "1000ms"]
                    }

        },
        {
          "type" : "websocket",
          "id" : "mexc_spot_btcusdt_depth",
          "exchange":"mexc", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"depth", 
          "updateSpeed" : 0, 
          "url" : "wss://wbs.mexc.com/ws",
          "msg" : {
                        "method": "SUBSCRIPTION",
                        "params": [
                            "spot@public.increase.depth.v3.api@BTCUSDT"
                        ]
                    }
        },
        {
          "type" : "websocket",
          "id" : "mexc_perpetual_btcusdt_depth",
          "exchange":"mexc", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"depth", 
          "updateSpeed" : 0, 
          "url" : "wss://contract.mexc.com/edge",
          "msg" : {
                    "method":"sub.depth",
                    "param":{
                        "symbol":"BTC_USDT"
                    }
                }
        },
        {
          "type" : "websocket",
          "id" : "bitget_spot_btcusdt_depth",
          "exchange":"bitget", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"depth", 
          "updateSpeed" : 0, 
          "url" : "wss://ws.bitget.com/v2/ws/public",
          "msg" : {
                    "op": "subscribe",
                    "args": [
                        {
                            "instType": "SPOT",
                            "channel": "books",
                            "instId": "BTCUSDT"
                        }
                    ]
                }
        },
        {
          "type" : "websocket",
          "id" : "bitget_perpetual_btcusdt_depth",
          "exchange":"bitget", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"depth", 
          "updateSpeed" : 0, 
          "url" : "wss://ws.bitget.com/v2/ws/public",
          "msg" : {
                    "op": "subscribe",
                    "args": [
                        {
                            "instType": "USDT-FUTURES",
                            "channel": "books",
                            "instId": "BTCUSDT"
                        }
                    ]
                }
        },
        { 
          "type" : "websocket",  
            "id" : "deribit_perpetual_btcusd_depth",
            "exchange":"deribit", 
            "insType":"perpetual", 
            "obj":"depth", 
            "instrument":"btcusd", 
            "updateSpeed":0,
            "url" : "wss://test.deribit.com/ws/api/v2",  
            "msg" : {
                    "jsonrpc": "2.0",
                    "method": "public/subscribe",
                    "id": generate_random_integer(10),
                    "params": {
                        "channels": ["book.BTC-PERPETUAL.100ms"]}
                    }
        }, 
        {
          "type" : "websocket",
          "id" : "htx_spot_btcusdt_depth",
          "exchange":"htx", 
          "instrument": "btcusdt", 
          "insType":"spot", 
          "obj":"depth", 
          "updateSpeed" : 0, 
          "url" : "wss://api-aws.huobi.pro/ws",
          "msg" : {
                    "sub": "market.btcusdt.depth.step0",
                    "id" : generate_random_integer(10)
                    }
        }, 
        {
          "type" : "websocket",
          "id" : "htx_perpetual_btcusdt_depth",
          "exchange":"htx", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"depth", 
          "updateSpeed" : 0, 
          "url" : "wss://api.hbdm.com/linear-swap-ws",
          "msg" : {
                    "sub":"market.BTC-USDT.depth.size_150.high_freq",
                    "data_type":"incremental",
                    "id" : generate_random_integer(10)
                    }
        },
        # {
        #   "type" : "websocket",
        #   "id" : "bingx_spot_btcusdt_depth",
        #   "exchange":"bingx", 
        #   "instrument": "btcusdt", 
        #   "insType":"spot", 
        #   "obj":"depth", 
        #   "updateSpeed" : 0, 
        #   "url" : "wss://open-api-ws.bingx.com/market",
        #   "msg" : {"id":generate_random_id(20),
        #            "reqType": "sub",
        #            "dataType":"BTC-USDT@depth100"}
        # },
        # {
        #   "type" : "websocket",
        #   "id" : "bingx_perpetual_btcusdt_depth",
        #   "exchange":"bingx", 
        #   "instrument": "btcusdt", 
        #   "insType":"perpetual", 
        #   "obj":"depth", 
        #   "updateSpeed" : 0, 
        #   "url" : "wss://open-api-swap.bingx.com/swap-market",
        #   "msg" : {"id":generate_random_id(20),
        #            "reqType": "sub",
        #            "dataType":"BTC-USDT@depth100@1000ms"}
        # },    
        ###
        # Open interest
        ###
        {
          "type" : "websocket",
          "id" : "okx_perpetual_btcusdt_OI",
          "exchange":"okx", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"OI", 
          "updateSpeed" : 0.5, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'open-interest', 'instId': 'BTC-USDT-SWAP'
                      }
              ]
              }
        },
        {
          "type" : "websocket",
          "id" : "okx_perpetual_btcusd_OI",
          "exchange":"okx", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"OI", 
          "updateSpeed" : 0.5, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'open-interest', 'instId': 'BTC-USD-SWAP'
                      }
              ]
              }
        },
        {
          "type" : "websocket",
          "id" : "okx_perpetual_btcusd_fundingRate",
          "exchange":"okx", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"fundingRate", 
          "updateSpeed" : 0.5, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'funding-rate', 'instId': 'BTC-USD-SWAP'
                      }
              ]
              }
        },
        {
          "type" : "websocket",
          "id" : "okx_perpetual_btcusdt_fundingRate",
          "exchange":"okx", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"fundingRate", 
          "updateSpeed" : 0.5, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'funding-rate', 'instId': 'BTC-USDT-SWAP'
                      }
              ]
              }
        },
        ###
        # Liquidations
        ###
        {
          "type" : "websocket",
          "id" : "binance_perpetual_btcusdt_liquidations",
          "exchange":"binance", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"liquidations", 
          "updateSpeed" : 0, 
          "url" : "wss://fstream.binance.com/ws",
          "msg" : {
              "method": "SUBSCRIBE", 
              "params": ["btcusdt@forceOrder"], 
              "id": generate_random_integer(10)
              }
        },
        {
          "type" : "websocket",
          "id" : "binance_perpetual_btcusd_liquidations",
          "exchange":"binance", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"liquidations", 
          "updateSpeed" : 0, 
          "url" : "wss://dstream.binance.com/ws",
          "msg" : {
              "method": "SUBSCRIBE", 
              "params": ["btcusd_perp@forceOrder"], 
              "id": generate_random_integer(10)
              }
        },
        {
          "type" : "websocket",
          "id" : "okx_perpetual_all_liquidations",
          "exchange":"okx", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"liquidations", 
          "updateSpeed" : 0.5, 
          "url" : "wss://ws.okx.com:8443/ws/v5/public",
          "msg" : {
              "op": "subscribe", 
              "args": [
                  {
                      'channel': 'liquidation-orders', 'instType': 'SWAP'
                      }
              ]
              }
        },
        {
          "type" : "websocket",
          "id" : "bybit_perpetual_btcusdt_liquidations",
          "exchange":"bybit", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"liquidations", 
          "updateSpeed" : 0.2, 
          "url" : "wss://stream.bybit.com/v5/public/linear",
          "msg" : {
              "op": 
              "subscribe","args": [
                  "liquidation.BTCUSDT"
                  ]
              }
        },
        {
          "type" : "websocket",
          "id" : "bybit_perpetual_btcusd_liquidations",
          "exchange":"bybit", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"liquidations", 
          "updateSpeed" : 0.2, 
          "url" : "wss://stream.bybit.com/v5/public/linear",
          "msg" : {
              "op": 
              "subscribe","args": [
                  "liquidation.BTCUSD"
                  ]
              }
        },
        ###
        # OI + FUNDING        # OK
        ###
        {
          "type" : "websocket",
          "id" : "bybit_perpetual_btcusdt_fundingOI",
          "exchange":"bybit", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"fundingOI", 
          "updateSpeed" : 0, 
          "url" : "wss://stream.bybit.com/v5/public/linear",
          "msg" : {
              "op": 
              "subscribe","args": [
                  "tickers.BTCUSDT"
                  ]
              }
        },
        {
          "type" : "websocket",
          "id" : "bybit_perpetual_btcusd_fundingOI",
          "exchange":"bybit", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"fundingOI", 
          "updateSpeed" : 0, 
          "url" : "wss://stream.bybit.com/v5/public/linear",
          "msg" : {
              "op": 
              "subscribe","args": [
                  "tickers.BTCPERP"
                  ]
              }
        },
        {
          "type" : "websocket",
          "id" : "mexc_perpetual_btcusdt_fundingOI",
          "exchange":"mexc", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"fundingOI", 
          "updateSpeed" : 0, 
          "url" : "wss://contract.mexc.com/edge",
          "msg" : {
                    "method":"sub.ticker",
                    "param":{
                        "symbol":"BTC_USDT"
                    }
                }
        },
        {
          "type" : "websocket",
          "id" : "bitget_perpetual_btcusdt_fundingOI",
          "exchange":"bitget", 
          "instrument": "btcusdt", 
          "insType":"perpetual", 
          "obj":"fundingOI", 
          "updateSpeed" : 0, 
          "url" : "wss://ws.bitget.com/v2/ws/public",
          "msg" : {
                    "op": "subscribe",
                    "args": [
                        {
                            "instType": "USDT-FUTURES",
                            "channel": "ticker",
                            "instId": "BTCUSDT"
                        }
                    ]
                }
        },
        {
          "type" : "websocket",   
            "id" : "deribit_perpetual_btcusd_ticker",
            "exchange":"deribit", 
            "insType":"perpetual", 
            "obj":"fundingOI", 
            "instrument":"btcusd", 
            "updateSpeed":0,
            "url" : "wss://test.deribit.com/ws/api/v2",  
            "msg" : {
                    "jsonrpc": "2.0",
                    "method": "public/subscribe",
                    "id": generate_random_integer(10),
                    "params": {
                        "channels": ["ticker.BTC-PERPETUAL.100ms"]}
                    }
        },          
        # HEARTBEAT # Coibase requires to use heartbeats to keep all connections opened
        {
          "type" : "websocket",   
          "id" : "coinbase_heartbeat",
          "exchange":"coinbase", 
          "instrument": "btcusd", 
          "insType":"spot", 
          "obj":"heartbeat", 
          "updateSpeed" : 0, 
          "url" : "wss://advanced-trade-ws.coinbase.com",
          "msg" :         {
            "type": "subscribe",
            "product_ids": [
                "BTC-USD"
            ],
            "channel": "heartbeats",
            "jwt": build_jwt_websockets(),
            "timestamp": int(time.time())
            }  
        },
        {
          "type" : "websocket",   
          "id" : "deribit_heartbeat",  
          "exchange":"deribit", 
          "instrument": "btcusd", 
          "insType":"perpetual", 
          "obj":"heartbeat", 
          "updateSpeed" : 0, 
          "url" : "wss://test.deribit.com/ws/api/v2",
          "msg" :         {
                    "jsonrpc" : "2.0",
                    "id" : generate_random_integer(10),
                    "method" : "public/set_heartbeat",
                    "params" : {
                        "interval" : 30
                    }
                    }
        },    
]



