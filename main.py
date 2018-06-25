from replacement_algorithm import fifo, lru, slru, offline_prefetch, common, online_prefetch_lru, online_prefetch_slru
import time
import sys
import configparser


class MyError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def process(parameter):
    if method_sel == 'online_lru':
        if not smart_evict_flag:
            fw = open(output + method_sel + '_' + str(parameter[1]) + '_' + str(parameter[0]), 'w')
        else:
            fw = open(output + method_sel + '_' + str(parameter[1]) + '_' + str(parameter[0])
                      + '_' + str(parameter[4][1]) + '_' + str(parameter[4][0]), 'w')
            print('current processing freq_threshold:', parameter[4][1], 'timeout:', parameter[4][0])
    elif method_sel == 'online_slru':
        fw = open(output + method_sel + '_' + str(parameter[1]) + '_' + str(parameter[0]), 'w')
    elif method_sel == 'offpre':
        fw = open(output + method_sel + '_' + str(parameter[0]), 'w')
    elif method_sel == 'lru' or method_sel == 'fifo' or method_sel == 'slru':
        fw = open(output + method_sel, 'w')
    else:
        raise MyError('ERROR: method %s cannot be found!' % (method_sel))
    fw.write('cache capacity\t\thr\t\tbhr\t\twrite2disk\t\ttransportfrombackend\n')
    for cache_capacity in [INITIAL_CACHE_SIZE + INCREASE_CACHE_SIZE_UNIT * i for i in range(CUMULATE_TIMES)]:
        stime = time.time()
        #hc, bhc = 0, 0 # hit count, byte hit count
        #tc, tbc = 0, 0 # total count, total byte count
        if method_sel == 'lru':
            replacement_method = lru.LRU(cache_capacity * GIGABYTE,
                                        stat_flag = statflag,
                                        stat_output = statoutput)
        elif method_sel == 'slru':
            replacement_method = slru.SLRU(cache_capacity * GIGABYTE)
        elif method_sel == 'fifo':
            replacement_method = fifo.FIFO(cache_capacity * GIGABYTE)
        elif method_sel == 'offpre':
            replacement_method = offline_prefetch.OffPre(cache_capacity * GIGABYTE, parameter[0], parameter[1])
        elif method_sel == 'online_lru':
            if smart_evict_flag:
                replacement_method = online_prefetch_lru.OnLine_LRU(cache_capacity * GIGABYTE,
                                                               parameter[0],
                                                               parameter[1],
                                                               parameter[2],
                                                               parameter[3],
                                                              smart_evict_flag=True,
                                                              freq_threshold=parameter[3][1],
                                                              timeout=parameter[3][0],
                                                              stat_flag = statflag,
                                                              stat_output = statoutput,
                                                              smart_evict2_flag = smf2)
            else:
                replacement_method = online_prefetch_lru.OnLine_LRU(cache_capacity * GIGABYTE,
                                                               parameter[0],
                                                               parameter[1],
                                                               parameter[2],
                                                               parameter[3],
                                                               stat_flag = statflag,
                                                               stat_output = statoutput,
                                                               smart_evict2_flag = smf2)
        elif method_sel == 'online_slru':
            replacement_method = online_prefetch_slru.OnLine_SLRU(cache_capacity * GIGABYTE,
                                                           parameter[0],
                                                           parameter[1],
                                                           parameter[2],
                                                           parameter[3])
        else:
            raise MyError('ERROR: method %s cannot be found!' % (method_sel))

        print('evaluating method: ', method_sel, '        cache size: %d'%(cache_capacity))
        with open(trace_file, 'r') as fp:
            for line in fp:
                lists = line.strip().split()
                t = int(lists[0])
                key = lists[1]
                _spec = lists[2]
                _format = lists[3]
                value = common.align4k(int(lists[4]))
                if t > WARM_LEN:
                    replacement_method.set_trigger()
                replacement_method.query((key, _spec, _format, value, t))

        print(replacement_method.output())
        replacement_method.my_release()
        fw.write(str(cache_capacity) + '\t\t' + replacement_method.output() + '\n')
        fw.flush()

        print("--- %s seconds ---" % (time.time() - stime))
    fw.close()

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read(sys.argv[1])

    # input file & result file prefix
    # log sample:
    #   timestamp file_hash resolution1(type) resolution2(specification) file_size uploaded_time(unix timestamp) latency
    #   20160201224853 V4t8sRRn4.3pFb7EKAN m 5 16080 1453635471 49
    # note: file_hash determines a logical image, file_hash+resolution1+resolution2 determines a unique physical image.
    trace_file = config['settings']['TRACE']
    output = config['settings']['OUTPUT_PREFIX']

    # method option
    #   lru         normal lru alg
    #   slru        normal slru alg
    #   fifo        normal fifo alg
    #   offpre      offline optimal prefetch method with lru alg
    #   online_lru  online prefetch method with lru alg
    #   online_slru online prefetch method with s3lru alg
    method_set = config['settings']['METHOD'].split() # fifo, lru, offpre, online1, online2

    # common parameter
    GIGABYTE = 1024 ** 3
    INCREASE_CACHE_SIZE_UNIT = int(config['settings']['INCREASE_CACHE_SIZE_UNIT'])
    INITIAL_CACHE_SIZE = int(config['settings']['INITIAL_CACHE_SIZE'])
    CUMULATE_TIMES = int(config['settings']['CUMULATE_TIMES'])
    WARM_LEN = int(config['settings']['WARM_LEN'])

    # prefetch parameter
    # uploaded infomation file path
    upload_file = config['settings']['UPLOADED_INFO']
    # prefetch_mode: 0~8. 1 means prefetch 1 resolution. similarly... only support online prefetch
    prefetch_mode = [int(x) for x in config['settings']['PREFETCH_MODE'].split()]
    # prefetch_mode2: 0 or 1. Suppose prefetch_mode=3, 0 means prefetch resolution 1 to 3, 1 means only prefetch 3.
    # only support online prefetch
    prefetch_mode2 = int(config['settings']['PREFETCH_MODE2'])
    prefetch_interval = [int(x) for x in config['settings']['PREFETCH_INTERVAL'].split()] # 1: realtime, 600: 10min, 3600: 1hour

    smart_evict_flag = False
    smf2 = False # smart evict 2 flag
    if int(config['settings']['SMART_EVICT_FLAG']) == 1:
        smart_evict_flag = True
        _ft = [int(x) for x in config['settings']['FREQ_THRESHOLD'].spilt()] #ft: freq threshold
        _tot = [int(x) for x in config['settings']['TIMEOUT_THRESHOLD'].split()] # tot: timeout threshold, switching to various timeout
    if int(config['settings']['SMART_EVICT2_FLAG']) == 1:
        smf2 = True
    
    statflag = False
    statoutput = ''
    if 'lru' in method_set or 'online_lru' in method_set:
        if int(config['settings']['STAT_FLAG']) == 1:
            statflag = True
            statoutput = config['settings']['STAT_OUTPUT']

    print('The Current Settings are:', \
          '\n  TRACE FILE                   = ', config['settings']['TRACE'], \
          '\n  OUTPUT_PREFIX                = ', config['settings']['OUTPUT_PREFIX'], \
          '\n  METHOD                       = ', config['settings']['METHOD'], \
          '\n  INITIAL_CACHE_SIZE/G         = ', config['settings']['INITIAL_CACHE_SIZE'], \
          '\n  INCREASE_CACHE_SIZE_UNIT/GB  = ', config['settings']['INCREASE_CACHE_SIZE_UNIT'], \
          '\n  CUMULATE_TIMES               = ', config['settings']['CUMULATE_TIMES'], \
          '\n  WARM_LEN                     = ', config['settings']['WARM_LEN'])
    if 'online_lru' in method_set or 'online_slru' in method_set or 'offpre' in method_set:
        print('\n  PHOTO INFO FILE              = ', config['settings']['UPLOADED_INFO'], \
              '\n  PREFETCH_MODE                = ', config['settings']['PREFETCH_MODE'], \
              '\n  PREFETCH_MODE2               = ', config['settings']['PREFETCH_MODE2'], \
              '\n  PREFETCH_INTERVAL            = ', config['settings']['PREFETCH_INTERVAL'], \
              '\n  SMART_EVICT_FLAG             = ', config['settings']['SMART_EVICT_FLAG'])
        if smart_evict_flag:
            print('\n FREQ_THRESHOLD                = ', config['settings']['FREQ_THRESHOLD'], \
                  '\n TIMEOUT_THRESHOLD             = ', config['settings']['TIMEOUT_THRESHOLD'])
    if 'lru' in method_set or 'online_lru' in method_set:
        print('\n  STAT_FLAG                    = ', config['settings']['STAT_FLAG'])
        if statflag:
            print('\n  STAT_OUTPUT                  = ', config['settings']['STAT_OUTPUT'])
    if 'online_lru' in model_set:
        print('\n  SMART_EVICT2_FLAG            = ', config['settings']['SMART_EVICT2_FLAG'])
        
    for method_sel in method_set:
        if method_sel == 'online_lru':
            for y in prefetch_interval:
                for x in prefetch_mode:
                    if smart_evict_flag:
                        for ft in _ft:
                            for tot in _tot:
                                smart_evict = [tot, ft]
                                start_time = time.time()
                                process([y, x, prefetch_mode2, upload_file, smart_evict])
                                end_time = time.time()
                                print("--- %s seconds ---" % (end_time - start_time))
                    else:
                        start_time = time.time()
                        process([y, x, prefetch_mode2, upload_file])
                        end_time = time.time()
                        print("--- %s seconds ---" % (end_time - start_time))

        elif method_sel == 'online_slru':
            for y in prefetch_interval:
                for x in prefetch_mode:
                    start_time = time.time()
                    process([y, x, prefetch_mode2, upload_file])
                    end_time = time.time()
                    print("--- %s seconds ---" % (end_time - start_time))
        elif method_sel == 'offpre':
            start_time = time.time()
            for y in prefetch_interval:
                process([y, upload_file])
            end_time = time.time()
            print("--- %s seconds ---" % (end_time - start_time))
        else: # default: fifo or lru or s3lru
            start_time = time.time()
            process([])
            end_time = time.time()
            print("--- %s seconds ---" % (end_time - start_time))
