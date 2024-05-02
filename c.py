from streams import connectionData
from consumers.consumer import XBTApp
import asyncio
from functools import partial
import uuid
import faust

app = XBTApp(
            connection_data=connectionData, 
            couch_host="",
            couch_username="", 
            couch_password="", 
            id = "XBTApp",
            broker = "kafka://localhost:9092",
            topic_partitions=5,
            value_serializer='raw'
            )

partial_functions = {}

def create_agent(agent):
    return agent

def agents(connection_data):
    """ Configuration of multiple agents """

    agents = []
    for cd in connection_data:
        topic_name = cd.get("topic_name")
        if "id_api" in cd:
            topic = app.topic(topic_name)
            agent_function = partial(app.process_api_agent, cd)
            agents.append(create_agent(agent_function))
            # app.agent(topic)(create_agent(agent_function))
            # print(f"API initialized for topic: {topic_name}")
    return agents

def attach_agent(agent, cd):
    topic_name = cd.get("topic_name")
    topic = app.topic(topic_name)
    app.agent(topic)(create_agent(agent_function))
            
for agent, cd in enumerate(agents(app.connection_data), app.connection_data):
    attach_agent(agent, cd)
# for cd in app.connection_data:
#     topic_name = cd.get("topic_name")
#     if "id_api" in cd:
#         topic = app.topic(topic_name)
#         agent_function = partial(app.process_api_agent, cd)
#         app.agent(topic)(create_agent(agent_function))
#         print(f"API initialized for topic: {topic_name}")
    

if __name__ == "__main__":
    app.main()


# https://github.com/robinhood/faust/issues/300



# def create_agent(start_topic: str, next_topic: faust.topics.Topic):
#     """Creating a single agent (with the help of closures)
 
#          `start_topic`:  str
#              Just a string that you can use in other functions
#              to figure out how messages in that topic can be
#              transformed

#          `next_topic`:  faust.topics.Topic
#              A faust `app.topic` instance
#     """

#     async def agent(stream):
#         """ Send messages from one topic to another """

#         async for message in stream:
#             if message_should_be_transformed(start_topic):
#                 message = transform_message(start_topic, message)
#             await next_topic.send(value=message)

#     log.info(f"NEW Agent Created: ## Agent - {consumer} ##")

#     return agent

# def agents():
#     """ Configuration of multiple agents """

#     agents = []
#     for topic in topics:
#         agent = create_agent(topic.start, topic.next)
#         agents.append((agent, topic))
#     return agents

# def attach_agent(agent, topic: namedtuple):
#     app.agent(channel=topic.faust, name=f"{topic.start}-agent")(agent)

# for agent, topic in agents():
#     attach_agent(agent, topic)



# https://github.com/robinhood/faust/issues/300