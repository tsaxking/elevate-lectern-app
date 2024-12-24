import argparse
import asyncio

from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server

import threading

from typing import TypedDict, Any
from Q import Queue

class Command(TypedDict):
    command: str
    args: Any

# def server(queue: Queue, ip: str, port: int):
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--ip",
#         default=ip, help="The ip to listen on")
#     parser.add_argument("--port",
#         type=int, default=port, help="The port to listen on")
#     args = parser.parse_args()

#     def handler(name: str, *args):
#         print(name, args)
#         queue.put(Command(
#             command=name,
#             args=args
#         ))

#     dispatcher = Dispatcher()
#     dispatcher.map("/*", handler)

#     server = osc_server.ThreadingOSCUDPServer(
#         (args.ip, args.port), dispatcher)
#     print("Serving on {}".format(server.server_address))
#     server.serve_forever()

# def start_server(queue: Queue, ip: str, port: int):
#     thread = threading.Thread(target=server, args=(queue, ip, port))
#     thread.daemon = True
#     thread.start()

class OSC_Config(TypedDict):
    ip: str
    port: int
    queue: Queue
    threading: bool

class OSC_Server:
    def __init__(self, config: OSC_Config):
        self.ip = config["ip"]
        self.port = config["port"]
        self.queue = config["queue"]
        self.threading = config["threading"]
        self.running = True

    def server(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--ip",
            default=self.ip, help="The ip to listen on")
        parser.add_argument("--port",
            type=int, default=self.port, help="The port to listen on")
        args = parser.parse_args()

        def handler(name: str, *args):
            if not self.running:
                server.server_close()
                return
            print(name, args)
            self.queue.put(Command(
                command=name,
                args=args
            ))

        dispatcher = Dispatcher()
        dispatcher.map("/*", handler)

        server = osc_server.ThreadingOSCUDPServer(
            (args.ip, args.port), dispatcher)
        print("Serving on {}".format(server.server_address))
        server.serve_forever()

    def stop(self):
        self.running = False

    def start(self):
        if self.threading:
            self.thread = threading.Thread(target=self.server)
            self.thread.daemon = True
            self.thread.start()
        else:
            self.server()