Available streams:

every instrument name must be of what eachage knows, better fetch it with config?wizar search?symbols

ws: recieves data via websockests protocols
api: recives data via api protocols if there are no websockets data



    # depth metric goes with  4 params : exchange, instrument_type, instrument and include_order_book_history (bool)
    # only one instrument per stream, as there are lots of updates. If you surpass the limit of updates per second, you may get kicked.
    # It depends by exchange but for simplicity I decided to include only 1 symbol per depth stream
    # if snapshot is true, it will fatch full order book map defined by configs in {exchange}_config.yaml

    # for now only spot and perpetual are available, future and options will be comming later. Maybe you make add these streams types and we will trade together.
    # Dynamic streams coming in the future


    # Trades as oposed to depth may contain many instruments, but there is no parameter of snapshot, as there is nothing to snap, 
    # only spot and perpetual available for now options and future coming later

    # liquidations are like trades except for okx liquidations
    # intrument_type: SWAP, basecoin : BTC }   # intrument_types : SWAP, FUTURES, OPTION, MARGIN] instead of basecoin you can use instruments : [list of your instruments]


    # Heartbeats
    # for running deribit or coinbase streams heartbeats are required. One heartbeat oer deribit and multiple per coinbase


    # trades agg:
        --- these are actually aggregated trades for like options and trades
        --- okx bybit deribit and binance gateio has it for option
        --- deribit has it for future and perpaltogerher
    No instriment has a basecoin


    # apis
    every api contains param exchange, fetching_interval_seconds and intrument/basecoin. If instrument passed, data of only this instrument will be streamead. If basecoin passed, data related to all instruments with this basecoin will be streamed
    --- oi --- if you want to stream individual symbols then it works fine for perpetual contracts only. If you want to stream all symbols related to the basecoin then it will work for future_perpetual and option. or perpetual or future. For futures the expired symbols will be removed and new added automatically you do not need to manage them manualy
    ---- funding works only for perpetual contracts, basecoin will stream all of the symbols at once
    oi of options only available in bulk with params basecoin, actually okx and gateio have weird name for basecoins
    # deribit perpetual_future oi basecoin will also fetch funding as well as open  interest

    in bulk only perpetual future is allowed, option cant be mixed neither iwth perpetual neither with future

    if the category is mixed, then you can only stream by basecoin


    # you may experiment with fetching intervals, read docs on how many requests you may do on every exchange and choose accordingly contrarily just choose a safe value. valyues of 20 seconds should be fine. For oi 20 seconds fine. For any of the positional_data like gta tta ttp do not choose less than 600 seconds, its useless they do not update these metrics so often, usually. CHeck official docs if you need




ALL available websockets and api streams by metric and exchange



# # intrument_types : SWAP, FUTURES, OPTION, MARGIN] instead of basecoin you can use instruments : [list of your instruments]