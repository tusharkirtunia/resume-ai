from collections import OrderedDict


class LRUCache:
    def __init__(self, max_size=256):
        self.max_size = max_size
        self.store = OrderedDict()

    def get(self, key):
        if key not in self.store:
            return None
        self.store.move_to_end(key)
        return self.store[key]

    def set(self, key, value):
        self.store[key] = value
        self.store.move_to_end(key)
        if len(self.store) > self.max_size:
            self.store.popitem(last=False)
            