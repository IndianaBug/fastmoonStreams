import faust

class consumer():
    
    def __init__(self, )



class consumer():
    
    def __init__(self, database="mockCouchDB", database_folder="mochdb_onmessage", couch_host="", couch_username="", couch_password="", mode="production"):
        self.database_name = database
        self.database_folder = database_folder
        if self.database_name == "CouchDB":
            self.db = aiocouch.Server(couch_host)
            self.db.resource.credentials = (couch_username, couch_password)
            self.ws_latencies = {}
    

app = faust.App("streaming-app")

orders_topics = ["topic1", "topic2", "topic3"]  # Example list of topics

# Define the decorator function
def create_decorated_agent(topic):
    @app.agent(topic)
    async def process_order(orders):
        async for order in orders:
            # Process each order using regular Python
            total_price = order.price * order.quantity
            await send_order_received_email(order.account_id, order)

# Loop through your topics and apply the decorator to each one
for topic in orders_topics:
    create_decorated_agent(topic)

# Start the Faust app
if __name__ == "__main__":
    app.main()