from abc import ABCMeta, abstractmethod
import collections


class ReplaceAlgo(metaclass=ABCMeta):
    def __init__(self, capacity):
        self.cache_capacity = capacity
        self.cache_size = 0
        self.cache_stack = collections.OrderedDict()

        self.write2disk = 0
        self.transportfrombackend = 0
        self.hc = 0
        self.tc = 0
        self.bhc = 0
        self.tbc = 0

        self.trigger = False # start counting hr/bhr/... flag

    @abstractmethod
    def query(self, s):
        pass

    def set_trigger(self):
        self.trigger = True

    def output(self):
        # format: hr bhr write2disk transportfrombackend
        return str(float('{0:.6f}'.format(1.0 * self.hc / self.tc))) + '\t\t' \
               + str(float('{0:.6f}'.format(1.0 * self.bhc / self.tbc))) + '\t\t' \
               + str(self.write2disk) + '\t\t' \
               + str(self.transportfrombackend)

    @abstractmethod
    def my_release(self):
        pass


class Node():
    def __init__(self, size):
        self.size = size        # image size
        self.source_flag = 0    # flag if the node is generated from prefetcher or cache mssing, 0 is cache missing.
        self.stat_count = 1     # statistic the request times of life time in cache

