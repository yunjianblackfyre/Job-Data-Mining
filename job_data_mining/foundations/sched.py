#   AUTHOR: Sibyl System
#     DATE: 2018-04-21
#     DESC: sched

import time
import sched
import datetime
import threading

SECONDS_PER_DAY = 24*60*60

class CSched():
    
    def __init__(self, func, args=(), mode=0):
        self._func = func
        self._args = args
        self._mode = mode    #0:按间隔执行；1：按时间执行
        self._delay = None   #seconds
        self._day = None
        self._hour = None
        self._min = None
        self._sec = None
        
    def set_mode(self, mode):
        self._mode = mode
    
    def set_time(self, hour=0, minute=0, second=0):
        self._hour = hour
        self._min = minute
        self._sec = second

    def set_date(self, day=0, hour=0, minute=0, second=0):
        self._day = day
        self._hour = hour
        self._min = minute
        self._sec = second

    def set_delay(self, delay):
        self._delay = delay
    
    def get_delay(self):
        if self._mode == 0 and self._delay is not None:
            return self._delay
        elif self._mode == 1 and None not in (self._hour, self._min, self._sec):
            curTime = datetime.datetime.now()
            desTime = curTime.replace(hour=self._hour, minute=self._min, second=self._sec)
            delta = (curTime - desTime).total_seconds()
            if delta > 0:
                skipSec = SECONDS_PER_DAY - delta
            else:
                skipSec = -delta
            return skipSec
        elif self._mode == 2 and None not in (self._day, self._hour, self._min, self._sec):
            curTime = datetime.datetime.now()
            desTime = curTime.replace(hour=self._hour, minute=self._min, second=self._sec)
            delta = (curTime - desTime).total_seconds()
            if delta > 0:
                skipSec = SECONDS_PER_DAY - delta + SECONDS_PER_DAY * self._day
            else:
                skipSec = -delta + SECONDS_PER_DAY * self._day
            return skipSec
        else:
            return 0
    
    def run(self):
        s = sched.scheduler(time.time, time.sleep)
        delay = self.get_delay()
        if delay != 0:
            s.enter(delay, 1, self.threadFunc)
            s.run()

    def threadFunc(self):
        t = threading.Thread(target=self._func, args=self._args)
        t.start()
        t.join()

if __name__ == '__main__':
    print(1)

