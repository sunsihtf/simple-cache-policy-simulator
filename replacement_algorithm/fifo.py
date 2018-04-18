from replacement_algorithm import general
import collections


class FIFO(general.ReplaceAlgo):
    def __init__(self, cache_capacity):
        general.ReplaceAlgo.__init__(self, cache_capacity)

    def query(self, s):
        key = s[0] + s[1] + s[2]
        value = s[3]
        if self.get(key):
            if self.trigger:
                self.hc += 1
                self.bhc += value
        else:
            self.evict(value)
            self.set((key, value))
            if self.trigger:
                self.write2disk += value
                self.transportfrombackend += value
        if self.trigger:
            self.tc += 1
            self.tbc += value


    def get(self, key):
        if key in self.cache_stack:
            return True
        else:
            return False

    def set(self, object): # object: (key, value)
        self.cache_stack[object[0]] = object[1]
        self.cache_size += object[1]

    def evict(self, value):
        while self.cache_size + value > self.cache_capacity:
            ob = self.cache_stack.popitem(last=False)
            self.cache_size -= ob[1]
    
    def my_release(self):
        pass
