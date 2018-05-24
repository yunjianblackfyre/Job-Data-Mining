#!/usr/bin/python
# -*- coding: utf-8 -*-

#   AUTHOR: Sibyl System
#     DATE: 2018-04-21
#     DESC: csdn_proc

import multiprocessing
import threading
import traceback
from foundations.sched import *
from foundations.exception import *
from config.schedules import CSDN_CRAWLER_CFG
from crawlers.csdn_project.scheduler import sched

class CTask(CSched):
    
    def __init__(self, cmd, d_data):
        self._data = d_data
        super(CTask, self).__init__(self.build_func, (cmd,))
    
    def build_func(self, cmd):
        p = multiprocessing.Process(target=sched, args=(cmd,))
        p.start()
        p.join()
    
    def do_task(self):
        if 'mode' in self._data:
            if self._data['mode'] == 0:  
                self.set_delay(self._data['delay'])
            elif self._data['mode'] == 1:
                self.set_time(self._data['hour'], self._data['minute'], self._data['second'])
            elif self._data['mode'] == 2:
                self.set_date(self._data['day'], self._data['hour'], self._data['minute'], self._data['second'])
            else:
                raise Exc(-1,'mode is invalid! data[%s]'%self._data)
            self.set_mode(self._data['mode'])
            while(True):
                self.run()
        else:
            raise Exc(-1,'mode miss! data[%s]'%self._data)
        

def start():
    try:
        threads = []
        for i in CSDN_CRAWLER_CFG.items():
            # if i[0] == 'SceneIqiyiDetail':
            #     for num in range(1):
            #         task = CTask(i[0], i[1])
            #         threads.append(threading.Thread(target=task.do_task))
            # else:
            #     task = CTask(i[0], i[1])
            #     threads.append(threading.Thread(target=task.do_task))
            task = CTask(i[0], i[1])
            threads.append(threading.Thread(target=task.do_task))
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    except Exception as e:
        print(traceback.format_exc())

if __name__ == '__main__':
    start()
