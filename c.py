from streams import connectionData
from consumers.consumer import XBTApp
import asyncio
from functools import partial

app = XBTApp(
            connection_data=connectionData, 
            couch_host="",
            couch_username="", 
            couch_password="", 
            id = "XBTApp",
            broker = "kafka://localhost:9092",
            topic_partitions=5
            )

for cd in app.connection_data:
    topic_name = cd.get("topic_name")
    if "id_api" in cd:
        topic = app.topic(topic_name)
        app.agent(topic)(partial(app.process_api_agent, cd))
        print(f"API initialized for topic: {topic_name}")
    

if __name__ == "__main__":
    app.main()


