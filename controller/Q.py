



class Queue:
    def __init__(self):
        self.queue = []

    def put(self, item):
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