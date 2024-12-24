import json
import threading
from typing import TypedDict

class State(TypedDict):
    height: float

class Preset(TypedDict):
    id: int
    name: str
    state: State

class Show(TypedDict):
    id: int
    name: str
    presets: list[Preset]