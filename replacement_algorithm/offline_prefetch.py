'''
Note: if t_prefetch + prefetch_interval >= currenttime, prefetching pics uploaded within [t_prefetch, currenttime).
'''

from replacement_algorithm import general, common
import collections
import pdb


class OffPre(general.ReplaceAlgo):
    def __init__(self, cache_capacity, p_interval, f_uploaded):
        general.ReplaceAlgo.__init__(self, cache_capacity)
        self.f_prefetch = open(f_uploaded)
        self.prefetch_interval = p_interval
        self.t_prefetch = 20160201164559 # trace start time is 20160201164559
        self.reserve_line = []

    def my_release(self):
        self.f_prefetch.close()

    def query(self, s):
        if common.diff_time_in_second(self.t_prefetch, s[4]) > self.prefetch_interval:
            self.prefetch(s[4])
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
            self.cache_stack.move_to_end(key) # update
            return True
        else:
            return False

    def set(self, ob): # ob: object: (key, value)
        self.cache_stack[ob[0]] = ob[1]
        self.cache_size += ob[1]

    def evict(self, value):
        while self.cache_size + value > self.cache_capacity:
            ob = self.cache_stack.popitem(last=False)
            self.cache_size -= ob[1]

    def prefetch(self, currenttime):
        while True:
            if self.reserve_line and self.reserve_line[1] not in self.cache_stack:
                self.evict(common.align4k(int(self.reserve_line[2])))
                self.set((self.reserve_line[1], common.align4k(int(self.reserve_line[2]))))
                if self.trigger:
                    self.write2disk += common.align4k(int(self.reserve_line[2]))
                    self.transportfrombackend += common.align4k(int(self.reserve_line[2]))
            line = self.f_prefetch.readline().strip().split()
            if int(line[0]) < self.t_prefetch: # ignore old images
                continue
            self.t_prefetch = int(line[0])
            if self.t_prefetch >= currenttime:
                self.reserve_line = line
                break
            if line[1] not in self.cache_stack:
                self.evict(common.align4k(int(line[2])))
                self.set((line[1], common.align4k(int(line[2]))))
                if self.trigger:
                    self.write2disk += common.align4k(int(line[2]))
                    self.transportfrombackend += common.align4k(int(line[2]))
