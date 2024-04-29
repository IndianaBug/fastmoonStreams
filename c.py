from streams import connectionData
from consumers.consumer import XBTApp
import asyncio
# import inspect
# import faust


# init_signature = inspect.signature(faust.App.__init__)
# for param in init_signature.parameters.values():
#     print(param)

consumer = XBTApp(
                 connection_data=connectionData, 
                 database="mockCouchDB",
                 database_folder="mochdb_onmessage", 
                 couch_host="",
                 couch_username="", 
                 couch_password="", 
                 mode="production",
                 id = "XBTApp",
                 broker = "kafka://localhost:9092")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(consumer.start_streams())


