from streams import connectionData
from consumers.consumer import XBTApp
import asyncio

consumer = XBTApp(connectionData)

if __name__ == "__main__":
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    _loop.run_until_complete(consumer.start())

# if __name__ == "__main__":
#     asyncio.run(consumer.initiate_strems())
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     loop.run_until_complete(consumer.app.main())
