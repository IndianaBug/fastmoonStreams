from streams import connectionData
from ProcessCenter.ConsumerEngine import StreamApp
import asyncio
from functools import partial
import uuid
import faust
from typing import AsyncIterator
import sys

app = StreamApp(
            connection_data=connectionData, 
            id = "XBT_All_Streams",
            broker = "kafka://localhost:9092",
            topic_partitions=5,
            value_serializer='raw'
            )


def agents(connection_data):
    """ Configuration of multiple agents """
    agents = []
    for cd in connection_data:
        if "id_api" in cd:
            agents.append(app.create_api_agent(cd))
        # elif "id_ws" in cd and cd.get("objective") == "depth":
        #     agents.append(app.create_wsbooks_agent(cd))
        # else:
        #     agents.append(app.create_ws_agent(cd))
    return agents

def attach_agent(agent, cd):
    topic_name = cd.get("topic_name")
    topic = app.topic(topic_name)
    app.agent(topic, name=topic_name)(agent)
            
for agent, cd in zip(agents(app.connection_data), app.connection_data):
    attach_agent(agent, cd)


# async def periodic_cleanup():
#     while True:
#         try:
#             await db.cleanup_old_records('my_topic_dead_messages', 30)
#             logger.info("Old records cleaned up successfully.")
#         except Exception as e:
#             logger.error(f"Error during cleanup: {e}")
#         await asyncio.sleep(86400)  # Run cleanup every 24 hours

if __name__ == "__main__":
    app.main()
