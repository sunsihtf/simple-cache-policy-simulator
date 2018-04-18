from replacement_algorithm import general


class LRU(general.ReplaceAlgo):
    def __init__(self, cache_capacity, stat_flag = False, stat_output = ''):
        general.ReplaceAlgo.__init__(self, cache_capacity)
        self.stat_flag = stat_flag
        if stat_flag:
            self.f_stat_out = open('lru_' + stat_output, 'w', newline='\n')

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
            self.cache_stack.move_to_end(key) # update
            if self.trigger:
                self.cache_stack[key].stat_count += 1
            return True
        else:
            return False

    def set(self, object): # object: (key, value)
        self.cache_stack[object[0]] = general.Node(object[1])
        self.cache_size += object[1]

    def evict(self, value):
        while self.cache_size + value > self.cache_capacity:
            ob = self.cache_stack.popitem(last=False)
            self.cache_size -= ob[1].size
            if self.trigger and self.stat_flag:
                self.f_stat_out.write('{} {}\n'.format(ob[0], ob[1].stat_count))

    def my_release(self):
        if self.stat_flag:
            self.f_stat_out.close()
