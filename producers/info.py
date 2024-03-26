from exchange_interaction import ExchangeAPIClient


coinbaseSecret = '-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIDOVctxJpAI/hHtbUN9VrHej4bWPRuT9um9FoBlTgiyaoAoGCCqGSM49\nAwEHoUQDQgAEJt8JWIh8CHm045POImBF0ZvVuX5FbQjIDhIT82hE5r1+vb8cSQ3M\nfEjriBy1/ZD3EywPNxyGe6nO/Wsq0M8hXQ==\n-----END EC PRIVATE KEY-----\n'
coinbaseAPI = 'organizations/b6a02fc1-cbb0-4658-8bb2-702437518d70/apiKeys/697a8516-f2e2-4ec9-a593-464338d96f21'
kucoinAPI = "65d92cc0291aa2000118b67b"
kucoinSecret = "3d449464-ab5e-4415-9950-ae31648fe90c"
kucoinPass = "sN038-(!UK}4"


client = ExchangeAPIClient(coinbaseAPI, coinbaseSecret, kucoinAPI, kucoinSecret, kucoinPass)
all_instruments = client.retrieve_all_instruments()
symbols = client.get_related_instruments(all_instruments, ["BTC", "BTC", "XBT"], ["PERP", "USD", "USD"], ["option", "future"])

websockets = {
    "binance" : {
        "spot" : {
            "depth" : ["BTCUSDT", "BTCFDUSD"],
            "trades" : ["BTCUSDT", "BTCTUSD", "BTCUSDC", "BTCUSDS", "BTCBUSD", "BTCFDUSD"],
        },
        "perpetual" : {
            "depth" : ["BTCUSD_PERP", "BTCUSDT"],
            "trades" : ["BTCUSD_PERP", "BTCUSDT", "BTCUSDC"],
            "liquidations" : ["BTCUSD_PERP", "BTCUSDT", "BTCUSDC"],
        },
        "option" : {
            "trades" : ["BTC"]
        }
    },
    "bybit" :  {
        "spot" : {
            "depth" : ["BTCUSDT"],
            "trades" : ["BTCUSDT", "BTCUSDC"],
        },
        "perpetual" : {
            "depth" : ["BTCUSDT"],
            "trades" : ["BTCPERP", "BTCUSD", "BTCUSDT"],
            "liquidations" : ["BTCPERP", "BTCUSD", "BTCUSDT"],
        },
        "option" : {
            "trades" : ["BTC"],
            "oi" : ["BTC"]
        }
    },
    "okx" :  {
        "spot" : {
            "depth" : ["BTC-USDT"],
            "trades" : ["BTC-USDT", "BTC-USDC"],
        },
        "perpetual" : {
            "depth" : ["BTC-USDT-SWAP"],
            "trades" : ["BTC-USD-SWAP", "BTC-USDT-SWAP", "BTC-USDC-SWAP"],
            "liquidations" : ["SWAP", "FUTURES", "OPTION"]
        },
        "option" : {
            "trades" : ["BTC"]
        }
    },
    "deribit" :  {
        "spot" : {
        },
        "perpetual" : {
            "depth" : ["BTC-PERPETUAL"],
            "tradesagg" : ["BTC-PERPETUAL", "BTC-4JUN21"],
        },
        "option" : {
            "trades" : ["BTC"]
        },
        "heartbeats" : {
            "heartbeats" : ["BTC-PERPETUAL"]
        }
    },
    "bitget" :  {
        "spot" : {
            "depth" : ["BTCUSDT"],
            "trades" : ["BTCUSDT", "BTCUSDC"],
        },
        "perpetual" : {
            "depth" : ["BTCUSDT"],
            "trades" : ["BTCUSDT", "BTCPERP", "BTCUSD"],
        },
    },
    "bingx" :  {
        "spot" : {
            "trades" : ["BTC-USDT"],
        },
        "perpetual" : {
            "trades" : ["BTC-USDT"],
        },

    },
    "kucoin" :  {
        "spot" : {
            "depth" : ["BTC-USDT"],
            "trades" : ["BTC-USDT"],
        },
        "perpetual" : {
            "depth" : ["XBTUSDTM"],
            "trades" : ["XBTUSDTM"],
        },
    },
    "gateio" :  {
        "spot" : {
            "depth" : ["BTC_USDT"],
            "trades" : ["BTC_USDT"],
        },
        "perpetual" : {
            "depth" : ["BTC_USDT"],
            "trades" : ["BTC_USDT"],
        },
        "option" : {
            "trades" : ["BTC"],
            "oi" : ["BTC"]
        }
    },
    "htx" :  {
    },
    "mexc" :  {
        "spot" : {
            "depth" : ["BTCUSDT"],
            "trades" : ["BTCUSDT"],
        },
        "perpetual" : {
            "depth" : [],
            "trades" : ["BTC_USDT"],
        },
    },
    "coinbase" :  {
        "spot" : {
            "depth" : ["BTC-USD"],
            "trades" : ["BTC-USD"],
            "heartbeats":["BTC-USD"]
        }
    },
}


aiohttp = {
    "binance" : {
        "perpetual" : {
            "oi" : "",
            "oi" : "",
            "oi" : "",
        },
        "option" : {
            "oi" : ["BTC", ]
        }
    },
    "bybit" : {
        "spot" : {
            
        },
        "perpetual" : {
            
        },
        "option" : {
            
        }
    },
    "okx" : {
        "spot" : {
            
        },
        "perpetual" : {
            
        },
        "option" : {
            
        }
    },
    "deribit" : {
        "spot" : {
            
        },
        "perpetual" : {
            
        },
        "option" : {
            
        }
    },
    "bitget" : {
        "spot" : {
            
        },
        "perpetual" : {
            
        },
        "option" : {
            
        }
    },
    "bingx" : {
        "spot" : {
            
        },
        "perpetual" : {
            
        },
        "option" : {
            
        }
    },
    "kucoin" : {
        "spot" : {
            
        },
        "perpetual" : {
            
        },
        "option" : {
            
        }
    },
    "gateio" : {
        "spot" : {
            
        },
        "perpetual" : {
            
        },
        "option" : {
            
        }
    },
    "htx" : {
        "spot" : {
            
        },
        "perpetual" : {
            
        },
        "option" : {
            
        }
    },
    "mexc" : {
        "spot" : {
            
        },
        "perpetual" : {
            
        },
        "option" : {
            
        }
    },
    "coinbase" : {
        "spot" : {
            
        },
        "perpetual" : {
            
        },
        "option" : {
            
        }
    },
}