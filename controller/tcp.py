import asyncio
import Q

class TCPClient:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self.address = writer.get_extra_info('peername')

    async def send(self, payload: str):
        try:
            self.writer.write(payload.encode('utf-8'))
            await self.writer.drain()
            print(f"Sent to {self.address}: {payload}")
        except Exception as e:
            print(f"Error sending to {self.address}: {e}")

    async def recv(self) -> str:
        try:
            data = await self.reader.read(1024)
            if not data:
                return ''
            return data.decode('utf-8').strip()
        except Exception as e:
            print(f"Error receiving from {self.address}: {e}")
            return ''

    def close(self):
        self.writer.close()
        try:
            asyncio.create_task(self.writer.wait_closed())
        except AttributeError:
            pass  # Python <3.7 fallback
        print(f"Closed connection to {self.address}")


class TCPServer:
    def __init__(self, host: str, port: int, queue: Q.SystemQueue):
        print(f"Initializing TCP Server on {host}:{port}")
        self.host = host
        self.port = port
        self.queue = queue
        self.clients: set[TCPClient] = set()
        self.running = False
        self._server = None

    async def start(self):
        if self.running:
            print("TCP Server is already running.")
            return
        try:
            self.running = True
            self._server = await asyncio.start_server(
                self.handle_client, self.host, self.port
            )
            print(f"TCP Server started on {self.host}:{self.port}")

            async with self._server:
                await self._server.serve_forever()
        except Exception as e:
            print(f"Error starting TCP Server: {e}")
            self.running = False
            self._server = None

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        client = TCPClient(reader, writer)
        self.clients.add(client)
        print(f"New client connected: {client.address}")

        try:
            while self.running:
                data = await client.recv()
                if not data:
                    break
                print(f"Received from {client.address}: {data}")
                self.queue.put(Q.System_Command(command=data))
                await client.send(f"Echo: {data}")
        except asyncio.CancelledError:
            pass
        finally:
            client.close()
            self.clients.remove(client)
            print(f"Client disconnected: {client.address}")

    async def stop(self):
        if not self.running:
            print("TCP Server is not running.")
            return

        print("Stopping TCP Server...")
        self.running = False
        for client in list(self.clients):
            client.close()
        self.clients.clear()

        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            print("TCP Server stopped.")
