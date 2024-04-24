
import inspect
from aiokafka.admin.client import OffsetAndMetadata
import asyncio
import aiokafka.admin.client as ccc
from aiokafka.producer import producer
from aiokafka import AIOKafkaProducer

# async def rr():
#     admin_client = OffsetAndMetadata() #OffsetAndMetadata(bootstrap_servers='localhost:9092')
#     return admin_client

# admin_client = asyncio.run(rr())  

delete_topics_method = getattr(AIOKafkaProducer, 'stop')
signature = inspect.signature(delete_topics_method)

print("Parameters:")
for param in signature.parameters.values():
    print(f"\t- {param.name} ({param.annotation})")

if delete_topics_method.__doc__:
    print("\nDocstring:")
    print(delete_topics_method.__doc__)
    
    
# members = inspect.getmembers(AIOKafkaProducer)
# for member_name, member in members:
#     print(member_name)
    
    
