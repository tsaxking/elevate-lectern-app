from typing import TypedDict, Any

class Command(TypedDict):
    command: str
    args: Any

    def to_dict(set):
        return {
            "command": set["command"],
            "args": set["args"]
        }

class System_Command:
    def __init__(self, command: str):
        self.command = command
        self.args = command.split('/')[1:] # Split by '/' and ignore the first part
        self.who = "all"  # Default to "all" if not specified
        if self.args[0] == 'lectern':
            self.who = "lectern"
            self.args = self.args[1:]
        elif self.args[0] == 'teleprompter':
            self.who = "teleprompter"
            self.args = self.args[1:]

    def to_dict(self):
        return {
            "command": self.command,
            "args": self.args
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
        self.queue = []
    
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

class SystemQueue:
    def __init__(self):
        self.queue: list[System_Command] = []

    def put(self, item: System_Command):
        self.queue.append(item)

    def get(self):
        if len(self.queue) == 0:
            return None
        return self.queue.pop(0)
    
    def clear(self):
        self.queue = []
    
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

    def clear_lectern(self):
        # Clear all commands related to the lectern
        self.queue = [cmd for cmd in self.queue if cmd.who != "lectern"]
    def clear_teleprompter(self):
        # Clear all commands related to the teleprompter
        self.queue = [cmd for cmd in self.queue if cmd.who != "teleprompter"]