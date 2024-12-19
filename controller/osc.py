import argparse
import random
import time
from pythonosc import osc_server
from pythonosc.dispatcher import Dispatcher
from system import System, COMMANDS

class EventEmitter:
    def __init__(self):
        self.listeners = {}

    def on(self, event, callback):
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(callback)

    def emit(self, event, *args):
        if event in self.listeners:
            for listener in self.listeners[event]:
                listener(*args)

    def off(self, event, callback):
        if event in self.listeners:
            self.listeners[event].remove(callback)

class OscController:
    def __init__(self, system: System, ip_address:str, port:int):
        self.system = system
        self.dispatcher = Dispatcher()

        def command_handler(addr: str, *args):
            self.system.send_command(addr, *args)
            pass

        self.dispatcher.map("/*", command_handler)

        self.server = osc_server.ThreadingOSCUDPServer((ip_address, port), self.dispatcher)
        self.server.serve_forever()