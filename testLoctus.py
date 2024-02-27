from locust import User, TaskSet, task, between
import asyncio
import websockets

class WebSocketUser(User):
    wait_time = between(1, 5)

    def on_start(self):
        self.ws = None
        self.loop = asyncio.get_event_loop()

    async def connect(self):
        uri = "wss://example.com/ws"  # Replace with your WebSocket URL
        self.ws = await websockets.connect(uri)

    async def close(self):
        if self.ws:
            await self.ws.close()

    @task
    async def send_message(self):
        try:
            if not self.ws:
                await self.connect()

            message = "Hello, WebSocket!"
            await self.ws.send(message)
            response = await self.ws.recv()
            print(response)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed. Reconnecting...")
            await self.close()
            await self.connect()

class MyWebSocketTasks(TaskSet):
    tasks = [WebSocketUser]

class MyWebSocketLocust(User):
    tasks = [MyWebSocketTasks]
    min_wait = 1000
    max_wait = 5000
