import argparse
import random
import time
from pythonosc import osc_server
from pythonosc.dispatcher import Dispatcher
from system import System, Command

class OscController:
    def __init__(self, system: System, ip_address:str, port:int):
        self.system = system
        self.dispatcher = Dispatcher()

        def command_handler(addr: str, *args):
            self.system.send_command(Command(
                command=addr,
                args=args[0]
            ))
            pass

        self.dispatcher.map("/*", command_handler)

        self.server = osc_server.ThreadingOSCUDPServer((ip_address, port), self.dispatcher)
        self.server.serve_forever()