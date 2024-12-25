from typing import TypedDict, Any

class Command(TypedDict):
    command: str
    args: Any

    def to_dict(set):
        return {
            "command": set["command"],
            "args": set["args"]
        }

class Queue:
    def __init__(self):
        self.queue: list[Command] = []

    def put(self, item: Command):
        self.queue.append(item)

    def get(self):
        if len(self.queue) == 0:
            return None
        return self.queue.pop(0)
    
    def clear(self):
        # Empty the queue
        self.queue = []

    def empty(self):
        return len(self.queue) == 0
    
    def qsize(self):
        return len(self.queue)
    
    def __len__(self):
        return len(self.queue)
    
    def __str__(self):
        return str(self.queue)

    def to_dict(self):
        # Convert the queue to a serializable format (a list)
        return {'queue': self.queue}

    def from_dict(self, data):
        # Initialize the queue from a dictionary format
        self.queue = data.get('queue', [])
    
    # Optional: Customize the serialization behavior
    def __getstate__(self):
        # Return the state that should be serialized
        return self.to_dict()

    def __setstate__(self, state):
        # Restore the state from the serialized data
        self.from_dict(state)
