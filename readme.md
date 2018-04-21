# Simple Cache Policy Simulator

Simple Cache Policy Simulator is an experimental program to evaluate various cache replacement policy and prefetching method described in our paper _Demysitifying Cache Policies for Photo Stores at Scale: A Tencent Case Study_, which includes:

* traditional replacement policies----fifo, lru and slru(s3lru).
* an optimical offline prefetching module integrated with lru----offpre.
* an online prefetching module integrated with lru----online_lru.
* an online prefetching module integrated with slru(s3lru)----online_slru.

Besides, the online prefetching module with lru supports smart evciting controlled by a switchon.

## Platform

It should be worked on any server/PC with python(>=3.6) environment.

## Usage

The simulator can be run from the command prompt:

```shell
python main.py path_of_argument_file
```

e.g.

```shell
python main.py arguments.txt
```

### Argument file

_arguments.txt_ gives an example of all arguments, either side of `=` are argus and their values.

* `TRACE`
  * path to trace file, e.g.

        TRACE = /home/xxx/workspace/cache_evaluate/trace_all_sample
  * a sample log of trace:

        timestamp pichash format specification size uploadedtime latency
        20160201224853 V4t8sRRn4.3pFb7EKAN m 5 16080 1453635471 49
    _Note_: _`pichash`_ determines a logical photo, _`pichash+format+specification`_ determines a unique physical photo. _`uploadedtime`_ is represented by unix timestamp.

* `UPLOADED_INFO`
  * path to logical photo info containing uploaded timestamp. A log sample:

        UPLOADED_INFO = /home/xxx/workspace/cache_evaluate/pic_info
  * a sample log of uploaded info:

        timestamp filehash size
        20160131112459 V4t8sRRn4.3pFb7EKANm5 16080
    _note_: _`filehash`_ = _`pichash+format+specification` which has been seen in trace. For other resolutions not contained in trace, we use a virtual size of the average size of that resolution.

* `OUTPUT_PREFIX`
  * output file prefix. The file includes hit ratio etc, e.g.

        OUTPUT_PREFIX = hr_
    will output _hr_lru_ if method is _lru_.

* `METHOD = lru | slru | fifo | offpre | online_lru | online_slru`
  * algorithms to be evaluated, it could be a list, e.g.

        METHOD = lru online_lru
    equals to test _Least Recently Used_ and _Online Prefetching with LRU_ respectively.

* `INCREASE_CACHE_SIZE_UNIT` `INITIAL_CACHE_SIZE` `CUMULATE_TIMES`
  * setting a series of cache capacities for multiple tests, e.g.

        INITIAL_CACHE_SIZE        = 30
        INCREASE_CACHE_SIZE_UNIT  = 10
        CUMULATE_TIMES            = 5
    equals to test `method` with cache capacities of 30, 40, 50, 60, 70GB respectively.

* `WARM_LEN`
  * the timestamp after which hit count, net traffic and other infos are counted, e.g.

        WARM_LEN = 20160206000000

* `PREFETCH_MODE = 1 | 2 | 3 | ... | 8`
  * 1 means prefetching 1 resolution. 2 means prefetching 2 resolutinos... Only support online prefetch. It can also be a list. E.g.

        PREFETCH_MODE = 1 3 5 7
    equals to test 1, 3, 5, 7 respectively.

* `PREFETCH_MODE2 = 0 | 1`
  * suppose prefetch_mode=3, 0 means prefetch resolution 1 to 3, 1 means only prefetch 3. Note only support online prefetch. E.g.

        PREFETCH_MODE2 = 0

* `PREFETCH_INTERVAL`
  * the interval bwtween two prefetching. It can also be a list. The unit is second, e.g.

        PREFETCH_INTERVAL = 600
    equals to prefetch with a period of 600 second.

* `SMART_EVICT_FLAG = 0 | 1`
  * smart eviction switchon. E.g.

        SMART_EVICT_FLAG = 1
    equals to open smart eviction.

* `FREQ_THRESHOLD`
  * the threshold that when freq of prefetched photos hit, they will be evicted. It can also be a list. E.g.

        FREQ_THRESHOLD = 2 4 6

* `TIMTOUT_THRESHOLD`
  * the threshold that when time stayed in cache of prefetched photos hit, they will be evicted. It can also be a list. The unit is _PREFETCH_INTERVAL_ E.g.

        TIMEOUT_THRESHOLD = 6 12 18
    equals to set timeout as 1, 2, 3 hours if `PREFETCH_INTERVAL=600`

* `STAT_FLAG = 0 | 1`
  * counting hit and other infos in lifetime switchon. Only works when method is lru or online_lru. E.g.

        STAT_FLAG = 0
    equals to stop counting lifetime statistics.

* `STAT_OUTPUT`
  * output file suffix of lifetime statistics. E.g.

        STAT_OUTPUT = life_time_stat

## Author

**Si Sun**

* [github/sunsihtf](https://github.com/sunsihtf)

If you encounter any problems, please opening them as issues.

## License

MIT License
