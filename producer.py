from OriginHub.SupplyEngine import publisher
import asyncio
from streams import streams_data

__name__ = "__main__"

if __name__ == '__main__':
    cryptoProducer = publisher(streams_data)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(cryptoProducer.run_producer())
