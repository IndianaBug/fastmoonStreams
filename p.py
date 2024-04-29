from producers.connectionManager import producer
import asyncio
from streams import connectionData

__name__ = "__main__"

if __name__ == '__main__':
    cryptoProducer = producer(connectionData)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(cryptoProducer.run_producer())
