import json
import requests
from urls import apizzz

# Helper to retrive books

def books_snapshot(exchange, instrument, insType, snaplength):
    """
      Gets full latest snapshot of limit orders.
    """
    link = [x for x in apizzz if x["exchange"] = exchange and x["instrument"] = instrument and x["insType"] = insType]
    try:
        link = "&".join([link, f"limit={snaplength}"])
        response = requests.get(link)
    except:
        get_books_snapshot(exchange, instrument, insType, snaplength-100)  # Say 5000 length is unavailable for a certain symbol, we will try with a smaller lrngth until we get the snapshot
    data = {
        "exchange" : exchange,
        "instrument" : instrument,
        "insType" : insType,
        "response" : response.json()
    }
    return data
