'''
s3lru programming structure:
query:          MRU <- |....queue3....|....queue2....|....queue1....| <- LRU
cache map:             |.cache_stack3.|.cache_stack2.|.cache_stack..|
cache size:            |.cache_size3..|.cache_size2..|..............|
                       |.................cache_size.................|
'''
from replacement_algorithm import general
import collections


class SLRU(general.ReplaceAlgo):
    def __init__(self, cache_capacity):
        general.ReplaceAlgo.__init__(self, cache_capacity)
        self.cache_stack2 = collections.OrderedDict()
        self.cache_stack3 = collections.OrderedDict()
        self.cache_size2 = 0
        self.cache_size3 = 0

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
        return_flag = True
        if key in self.cache_stack3:
            self.cache_stack3.move_to_end(key)
        elif key in self.cache_stack2:
            ob = [key, self.cache_stack2.pop(key)]
            self.cache_stack3[ob[0]] = ob[1]
            self.cache_size3 += ob[1].size
            self.cache_size2 -= ob[1].size
        elif key in self.cache_stack:
            ob = [key, self.cache_stack.pop(key)]
            self.cache_stack2[ob[0]] = ob[1]
            self.cache_size2 += ob[1].size
        else:
            return_flag = False
        self.balance()
        return return_flag

    def set(self, object): # object: (key, value)
        self.cache_stack[object[0]] = general.Node(object[1])
        self.cache_size += object[1]

    def evict(self, value):
        while self.cache_size + value > self.cache_capacity:
            ob = self.cache_stack.popitem(last=False)
            self.cache_size -= ob[1].size

    def balance(self):
        while self.cache_size3 > self.cache_capacity // 3:
            ob = self.cache_stack3.popitem(last=False)
            self.cache_stack2[ob[0]] = ob[1]
            self.cache_size3 -= ob[1].size
            self.cache_size2 += ob[1].size
        while self.cache_size2 > self.cache_capacity // 3:
            ob = self.cache_stack2.popitem(last=False)
            self.cache_stack[ob[0]] = ob[1]
            self.cache_size2 -= ob[1].size
                
    def my_release(self):
        pass
