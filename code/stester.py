import asyncio
import websockets
import time
from collections import deque

class WebSocketMonitor:
    def __init__(self, num_connections, server_uri):
        self.num_connections = num_connections
        self.server_uri = server_uri
        self.websocket_connections = []
        self.rtt_averages = [deque(maxlen=5) for _ in range(num_connections)]

    async def connect_to_websocket(self, index):
        uri = self.server_uri
        async with websockets.connect(uri) as websocket:
            self.websocket_connections.append(websocket)
            while True:
                start_time = time.time()
                message = f"Hello from WebSocket {index}"
                await websocket.send(message)

                response = await websocket.recv()
                end_time = time.time()
                rtt = end_time - start_time

                self.update_rtt_average(index, rtt)

                print(f"WebSocket {index} - RTT: {rtt:.4f} seconds (Avg: {self.get_average_rtt(index):.4f} seconds)")

                await asyncio.sleep(1)

    def update_rtt_average(self, index, rtt):
        self.rtt_averages[index].append(rtt)

    def get_average_rtt(self, index):
        if self.rtt_averages[index]:
            return sum(self.rtt_averages[index]) / len(self.rtt_averages[index])
        else:
            return 0

if __name__ == "__main__":
    num_connections = 10
    server_uri = "ws://your-websocket-server-url"

    monitor = WebSocketMonitor(num_connections, server_uri)

    # Create and run multiple WebSocket clients concurrently
    tasks = [monitor.connect_to_websocket(i) for i in range(num_connections)]
    asyncio.get_event_loop().run_until_complete(asyncio.gather(*tasks))