import asyncio
import ijson
import json
import time

data = {
  "earth": {
    "europe": [
      {"name": "Paris", "type": "city", "info": 1},
      {"name": "Thames", "type": "river", "info": 1},
      {"name": "Thames", "type": "river", "info": 1},
      {"name": "Thames", "type": "city", "info": 1},
    ],
    "america": [
      {"name": "Texas", "type": "state", "info": 1},
    ]
  }
}

import asyncio
from concurrent.futures import ThreadPoolExecutor
import rapidjson

async def main(json_data):
    loop = asyncio.get_running_loop()
    chunk_size = 100  # Adjust chunk size as needed

    # Split the JSON data into chunks
    chunks = split_json_into_chunks(json_data, chunk_size)

    # Process each chunk asynchronously
    for chunk in chunks:
        await process_chunk_in_executor(loop, chunk)

def split_json_into_chunks(json_string, chunk_size):
    chunks = []
    start = 0
    while start < len(json_string):
        end = min(start + chunk_size, len(json_string))
        while end > start and json_string[end - 1] != '}':
            end -= 1
        if end == start:
            end = len(json_string)
        chunks.append(json_string[start:end])
        start = end
    return chunks

async def process_chunk_in_executor(loop, chunk):
    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, rapidjson.loads, chunk)
        for item in result.get('earth', {}).get('europe', []):
            if item['type'] == 'city':
                print(item)

json_data = '{"earth":{"europe":[{"name":"Paris","type":"city","info":1},{"name":"Thames","type":"river","info":1},{"name":"Thames","type":"river","info":1},{"name":"Thames","type":"city","info":1}],"america":[{"name":"Texas","type":"state","info":1}]}}'

import ijson

d = {}
objects = ijson.items(data, 'item')
open_interests = (o.get("sumOpenInterest") for o in objects)
symbols = (o.get("symbol") for o in objects)
for open_interest, symbol in zip(open_interests, symbols):
    d[symbol] = {"openInterest" : open_interest}


asyncio.run(main(json.dumps(data)))













#################333

# import json

# def split_json_into_chunks(json_string, chunk_size):
#   chunks = []
#   start = 0
#   while start < len(json_string):
#     end = min(start + chunk_size, len(json_string))
#     while end > start and json_string[end - 1] != '}':
#       end -= 1
#     if end == start:
#       end = len(json_string)

#     chunks.append(json_string[start:end])
#     start = end
#   return chunks
# data = json.dumps({
#   "earth": {
#     "europe": [
#       {"name": "Paris", "type": "city", "info": 1},
#       {"name": "Thames", "type": "river", "info": 1},
#       {"name": "Thames", "type": "river", "info": 1},
#       {"name": "Thames", "type": "city", "info": 1},
#     ],
#     "america": [
#       {"name": "Texas", "type": "state", "info": 1},
#     ]
#   }
# })

# chunk_size = 100
# chunks = split_json_into_chunks(data, chunk_size)

# print("Chunks:")
# for chunk in chunks:
#   print(chunk)