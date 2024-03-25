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
        },
        "option" : {
            "trades" : ["BTC"]
        }
    },
    "bybit" :  {
        "spot" : {
            "depth" : ["BTCUSDT"],
            "trades" : [],
        },
        "perpetual" : {
            "depth" : [],
            "trades" : [],
        },
        "option" : {
            "trades" : ["BTC"]
        }
    },
    "okx" :  {
        "spot" : {
            "depth" : ["BTCUSDT"],
            "trades" : [],
        },
        "perpetual" : {
            "depth" : [],
            "trades" : [],
        },
        "option" : {
            "trades" : ["BTC"]
        }
    },
    "deribit" :  {
        "spot" : {
            "depth" : ["BTCUSDT"],
            "trades" : [],
        },
        "perpetual" : {
            "depth" : [],
            "trades" : [],
        },
        "option" : {
            "trades" : ["BTC"]
        }
    },
    "bitget" :  {
        "spot" : {
            "depth" : ["BTCUSDT"],
            "trades" : ["BTCUSDT", "BTCUSDC"],
        },
        "perpetual" : {
            "depth" : ["BTCUSDT"],
            "trades" : ["BTCUSDT", "BTCUSDC"],
        },
        "option" : {
            "trades" : ["BTC"]
        }
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
            "depth" : ["BTCUSDT"],
            "trades" : [],
        },
        "perpetual" : {
            "depth" : [],
            "trades" : [],
        },
        "option" : {
            "trades" : ["BTC"]
        }
    },
    "gateio" :  {
        "spot" : {
            "depth" : ["BTCUSDT"],
            "trades" : [],
        },
        "perpetual" : {
            "depth" : [],
            "trades" : [],
        },
        "option" : {
            "trades" : ["BTC"]
        }
    },
    "htx" :  {
        "spot" : {
            "depth" : ["BTCUSDT"],
            "trades" : [],
        },
        "perpetual" : {
            "depth" : [],
            "trades" : [],
        },
        "option" : {
            "trades" : ["BTC"]
        }
    },
    "mexc" :  {
        "spot" : {
            "depth" : ["BTCUSDT"],
            "trades" : [],
        },
        "perpetual" : {
            "depth" : [],
            "trades" : [],
        },
        "option" : {
            "trades" : ["BTC"]
        }
    },
    "coinbase" :  {
        "spot" : {
            "depth" : ["BTCUSDT"],
            "trades" : [],
        },
        "perpetual" : {
            "depth" : [],
            "trades" : [],
        },
        "option" : {
            "trades" : ["BTC"]
        }
    },
}


aiohttp = {
    "binance" : {
        "spot" : {
            
        },
        "perpetual" : {
            
        },
        "option" : {
            
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