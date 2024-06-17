# config.py

coinbase_secret = '-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIDOVctxJpAI/hHtbUN9VrHej4bWPRuT9um9FoBlTgiyaoAoGCCqGSM49\nAwEHoUQDQgAEJt8JWIh8CHm045POImBF0ZvVuX5FbQjIDhIT82hE5r1+vb8cSQ3M\nfEjriBy1/ZD3EywPNxyGe6nO/Wsq0M8hXQ==\n-----END EC PRIVATE KEY-----\n'
coinbase_api = 'organizations/b6a02fc1-cbb0-4658-8bb2-702437518d70/apiKeys/697a8516-f2e2-4ec9-a593-464338d96f21'
kucoin_api = "65d92cc0291aa2000118b67b"
kucoin_secret = "3d449464-ab5e-4415-9950-ae31648fe90c"
kucoin_pass = "sN038-(!UK}4"

merge_types = [
    "depth_spot", "depth_future", "trades_spot", "trades_future", 
    "trades_option", "oi_delta_future", "liquidations_future",
    "oi_options", "cdepth_spot", "cdepth_future", "rdepth_spot", "rdepth_future"
    ]

fiats = [
    "usd", "eur", "rub", "try", "uah", "kzt", "inr", 
    "gbp", "krw", "aud", "chf", "czk", "dkk", "nok", 
    "nzd", "pln", "sek", "zar", "huf", "ils"
]
stablecoins = ["usdt", "usdc", "busd", "dai", "tusd", "fdusd"]

message_processor_fail_threshold = 0.1