import okx.PublicData as PublicData

flag = "0"  # Production trading: 0, Demo trading: 1

publicDataAPI = PublicData.PublicAPI(flag=flag)

# Retrieve a list of instruments with open contracts
result = publicDataAPI.get_instruments(
    instType="OPTION" # SPOT SWAP FUTURES
)


# print([x['instId'] for x in result['data'] if "BTC" in x['instId']])

