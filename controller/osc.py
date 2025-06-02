import argparse
import asyncio
import queue

from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server

import threading

from typing import TypedDict, Any
import Q


class OSC_Config(TypedDict):
    ip: str
    port: int
    queue: Q.SystemQueue
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
            # remove all commas
            name = name.replace(",", "")
            print(name, args)
            self.queue.put(Q.System_Command(
                command=name,
                # args=args
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

class AsyncOSCConfig(TypedDict):
    ip: str
    port: int
    queue: Q.SystemQueue

class AsyncOSCServer:
    def __init__(self, config: OSC_Config):
        self.ip = config["ip"]
        self.port = config["port"]
        self.queue = config["queue"]
        self.running = False
        self.server = None

    def start(self):
        self.running = True
        if self.server is not None:
            print("OSC server already running")
            return
        parser = argparse.ArgumentParser()
        parser.add_argument("--ip",
            default=self.ip, help="The ip to listen on")
        parser.add_argument("--port",
            type=int, default=self.port, help="The port to listen on")
        args = parser.parse_args()

        def handler(name: str, *args):
            try:
                if not self.running:
                    return
                name = name.replace(",", "")
                print(name, args)
                self.queue.put(Q.System_Command(
                    command=name,
                ))
            except Exception as e:
                print(f"Error handling OSC message: {e}")

        dispatcher = Dispatcher()
        dispatcher.map("/*", handler)

        self.server = osc_server.AsyncIOOSCUDPServer(
            (args.ip, args.port),
            dispatcher,
            asyncio.get_event_loop()
        )
        print(f"Serving OSC on {self.ip}:{self.port}")
        asyncio.create_task(self.server.create_serve_endpoint())

    def stop(self):
        self.running = False

    def restart(self):
        self.stop()
        self.start()
