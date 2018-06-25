'''
Online prefetcher with replacement policy lru. 
We only prefetch photos with resolution m5 uploaded between [t_prefetch, currenttime). 
Note that since we don't know size of resolution m5 of some photo that not exists in our trace, a virtual m5 is prefetched whose size is the average of all existing m5 photos. And, we prefetch all photo with resolution m5!
To test custom trace, you need to manualy modify sizes in __init__(), such as self.size_XX.
'''
from replacement_algorithm import general, common
import collections
import pdb


class OnLine_LRU(general.ReplaceAlgo):
    def __init__(self, cache_capacity, p_interval, p_mode1, p_mode2, f_uploaded, smart_evict_flag=False, freq_threshold=1, timeout=6, stat_flag=False, stat_output='', smart_evict2_flag=False):
        general.ReplaceAlgo.__init__(self, cache_capacity)
        self.f_prefetch = open(f_uploaded)
        self.prefetch_interval = p_interval
        self.t_prefetch = -1
        self.reserve_line = []
        self.mode = p_mode1
        self.mode2 = p_mode2 == 0
        self.size_m5 = 16484 # m5 is the highest resolution, and the average size of resolution m5 is 16KB
                             # (34.78%)
        self.size_c5 = 40960 # c5 is the second highest resolution, its size is 40KB (14.98%)
        self.size_m0 = 16484 # m0 is the third highest resolution, its size is 16KB (13.35%)
        self.size_b5 = 77824 # b5 is the forth highest resolution, its size is 76KB (12.95%)
        self.size_c0 = 53248 # c0 is the fifth highest resolution, its size is 52KB (7.44%)
        self.size_b0 = 118784 # b0 is the sixth highest resolution, its size is 116KB (6.37%)
        self.size_a0 = 4096 # a0 is the seventh highest resolution, its size is 4KB (5.38%)
        self.size_a5 = 4096 # a5 is the lowest resolution, its size is 4KB (4.75%)

        # stat_flag is used to count freq of both prefetched and non-prefetched
        # object in their lifetime, thus we can infer whether they exceed
        # threshold and should be evict.
        self.stat_flag = stat_flag
        self.smart_evict_flag = smart_evict_flag
        self.smart_evict2_flag = smart_evict2_flag
        if stat_flag:
            self.f_stat_out = open('lru_prefetch_' + stat_output, 'w', newline='\n')
        if smart_evict_flag:
            # Ghost queue only contains prefetched photos' meta data, when a
            # photo timeout or freq is lower then threshold, it is evicted
            # preferentially.
            self.No_prefetch = 1 # the No.prefetch to prefetch
            self.timeout = timeout
            self.freq_threshold = freq_threshold
            self.smart_evict_queue = collections.OrderedDict()
        if smart_evict2_flag:
            self.smart_evict2_table = dict()

    def my_release(self):
        self.f_prefetch.close()
        if self.stat_flag:
            self.f_stat_out.close()

    def query(self, s):
        if self.t_prefetch == -1: # initial
            self.t_prefetch = s[4]
        if common.diff_time_in_second(self.t_prefetch, s[4]) > self.prefetch_interval:
            self.prefetch(s[4])
            if self.smart_evict_flag:
                self.No_prefetch += 1
        key = s[0] + s[1] + s[2]
        value = s[3]
        if self.get(key):
            if self.smart_evict_flag:
                if key in self.smart_evict_queue:
                    self.smart_evict_queue[key][1] += 1
                    if self.smart_evict_queue[key][1] > self.freq_threshold:
                        del self.smart_evict_queue[key]
            if self.smart_evict2_flag:
                id = key[0:-2]
                rez = key[-2:]
                for x in range(len(self.smart_evict2_table[id])):
                    if self.smart_evict2_table[id][x][0] == rez:
                        self.smart_evict2_table[id][x][1] += 1
            if self.trigger:
                self.cache_stack[key].stat_count += 1
                self.hc += 1
                self.bhc += value
        else:
            self.evict(value)
            ob = [key, general.Node(value)]
            self.set(ob)
            if self.smart_evict2_flag:
                self.smart2_set(key, 1)
            if self.trigger:
                self.write2disk += value
                self.transportfrombackend += value
        if self.trigger:
            self.tc += 1
            self.tbc += value

    def get(self, key):
        if key in self.cache_stack:
            self.cache_stack.move_to_end(key)
            return True
        else:
            return False

    def set(self, ob): # ob: object: (key, value)
        self.cache_stack[ob[0]] = ob[1]
        self.cache_size += ob[1].size

    def smart_set(self, key):
        self.smart_evict_queue[key] = [self.No_prefetch, 0] # No.  prefetch, freq

    def smart2_set(self, key, freq):
        id = key[0:-2]
        rez = key[-2:]
        if id in self.smart_evict2_table:
            self.smart_evict2_table[id].append([rez, freq])
        else:
            self.smart_evict2_table[id] = [[rez, freq]] # resolution, freq

    def evict(self, value):
        while self.cache_size + value > self.cache_capacity:
            if self.smart_evict_flag: # smart evict
                smart_evict()
            elif self.smart_evict2_flag: # smart evict 2
                ob = self.cache_stack.popitem(last=False)
                self.cache_size -= ob[1].size
                self.smart_evict2(ob[0])
            else: # normal evict
                ob = self.cache_stack.popitem(last=False)
                self.cache_size -= ob[1].size
            if self.trigger and self.stat_flag: # does not work in smart evict 2!!!
                self.f_stat_out.write('{} {} {}\n'.format(ob[0], ob[1].source_flag, ob[1].stat_count))
    
    def smart_evict(self):
        if len(self.smart_evict_queue) and \
           self.No_prefetch - next(iter(self.smart_evict_queue.values()))[0] > self.timeout:
            ghost_ob = self.smart_evict_queue.popitem(last=False)
            ob = self.cache_stack.popitem(ghost_ob[0])
        else:
            ob = self.cache_stack.popitem(last=False)
            if ob[0] in self.smart_evict_queue: # should never exec on theory
                del self.smart_evict_queue[ob[0]]
        self.cache_size -= ob[1].size
        if self.smart_evict2_flag:
            self.smart_evict2(ob[0])
    
    def smart_evict2(self, key):
        id = key[0:-2]
        rez0 = key[-2:]
        group_evict_list = []
        for x in self.smart_evict2_table[id]:
            if x[0] == rez0:
                group_evict_list.append(x)
            else:
                if x[1] < 2: # this can be a tunable parameter
                    self.cache_size -= self.cache_stack[id + x[0]].size
                    del self.cache_stack[id + x[0]]
                    group_evict_list.append(x)
        for x in group_evict_list:
            self.smart_evict2_table[id].remove(x)
        if not self.smart_evict2_table[id]:
            del self.smart_evict2_table[id]

    def prefetch(self, currenttime):
        while True:
            if self.reserve_line:
                if self.mode2:
                    self.prefetch_sel(self.reserve_line[1], common.align4k(int(self.reserve_line[2])))
                else:
                    self.prefetch_sel2(self.reserve_line[1], common.align4k(int(self.reserve_line[2])))
            line = self.f_prefetch.readline().strip().split()
            if int(line[0]) < self.t_prefetch: # ignore old images
                continue
            self.t_prefetch = int(line[0])
            if self.t_prefetch >= currenttime:
                self.reserve_line = line
                break
            if self.mode2:
                self.prefetch_sel(line[1], common.align4k(int(line[2])))
            else:
                self.prefetch_sel2(line[1], common.align4k(int(line[2])))

    def prefetch_sel(self, key, value):
        if self.mode > 0:
            self.insert_prefetch(key, value, 'm5', self.size_m5)
            if self.mode > 1:
                self.insert_prefetch(key, value, 'c5', self.size_c5)
                if self.mode > 2:
                    self.insert_prefetch(key, value, 'm0', self.size_m0)
                    if self.mode > 3:
                        self.insert_prefetch(key, value, 'b5', self.size_b5)
                        if self.mode > 4:
                            self.insert_prefetch(key, value, 'c0', self.size_c0)
                            if self.mode > 5:
                                self.insert_prefetch(key, value, 'b0', self.size_b0)
                                if self.mode > 6:
                                    self.insert_prefetch(key, value, 'a5', self.size_a5)
                                    if self.mode > 7:
                                        self.insert_prefetch(key, value, 'a0', self.size_a0)

    def prefetch_sel2(self, key, value):
        if self.mode == 1:
            self.insert_prefetch(key, value, 'm5', self.size_m5)
        elif self.mode == 2:
            self.insert_prefetch(key, value, 'c5', self.size_c5)
        elif self.mode == 3:
            self.insert_prefetch(key, value, 'm0', self.size_m0)
        elif self.mode == 4:
            self.insert_prefetch(key, value, 'b5', self.size_b5)
        elif self.mode == 5:
            self.insert_prefetch(key, value, 'c0', self.size_c0)
        elif self.mode == 6:
            self.insert_prefetch(key, value, 'b0', self.size_b0)
        elif self.mode == 7:
            self.insert_prefetch(key, value, 'a5', self.size_a5)
        elif self.mode == 8:
            self.insert_prefetch(key, value, 'a0', self.size_a0)

    def insert_prefetch(self, key, value, resolution, resolution_size):
        if key[-2:] == resolution:
            _key = key
            _value = value
        else:
            _key = key[:-2] + resolution
            _value = resolution_size
        if _key not in self.cache_stack:
            self.evict(_value)
            ob = [_key, general.Node(_value)]
            ob[1].source_flag = 1 # 1 -> a prefetch file, 0(default) -> a non_prefetch_file
            ob[1].stat_count = 0
            self.set(ob)
            if self.smart_evict_flag:
                self.smart_set(_key)
            if self.smart_evict2_flag:
                self.smart2_set(_key, 0)
            if self.trigger:
                self.write2disk += _value
                self.transportfrombackend += _value
