APIparamsType = {
    "binance" : {
        "spot" : {
            "depth" : {
                "symbol" : "",
                "limit" : int("")
            }
        },
        "perp" : {
            "mfutures" : {
                "depth" : "/fapi/v1/depth"
            },
            "cfutures" : {
                "depth" : "/dapi/v1/depth",

            },
        }
    },
}