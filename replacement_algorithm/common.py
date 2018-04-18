import time, datetime


def align4k(x):
    if x % 4096 == 0:
        return x
    else:
        return x + 4096 - x % 4096


def convert2unixtime(x):
    return int(time.mktime(datetime.datetime.strptime(x, "%Y%m%d%H%M%S").timetuple()))


def diff_time_in_second(t1, t2):
    d1, h1, m1, s1 = int(t1 % 100000000 / 1000000), int(t1 % 1000000 / 10000), int(t1 % 10000 / 100), int(t1 % 100)
    d2, h2, m2, s2 = int(t2 % 100000000 / 1000000), int(t2 % 1000000 / 10000), int(t2 % 10000 / 100), int(t2 % 100)
    t1_secs = s1 + 60 * m1 + 3600 * h1 + 24 * 3600 * d1
    t2_secs = s2 + 60 * m2 + 3600 * h2 + 24 * 3600 * d2
    return (t2_secs - t1_secs)

