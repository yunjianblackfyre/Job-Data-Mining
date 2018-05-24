#   AUTHOR: Sibyl System
#     DATE: 2018-04-21
#     DESC: crawler scheduler

import sys
import time
import multiprocessing
from scrapy.crawler import CrawlerProcess
from csdn_task_spider import CsdnTaskSpider
from csdn_detail_spider import CsdnDetailSpider
from csdn_image_spider import CsdnImageSpider

class SceneCsdnTask(object):
    
    def __init__(self):
        self.process = CrawlerProcess()

    def run(self):
        self.process.crawl(SceneCsdnTask)
        self.process.start()
        
class SceneCsdnDetail(object):
    def __init__(self):
        self.process = CrawlerProcess()

    def run(self):
        self.process.crawl(SceneCsdnDetail)
        self.process.start()

class SceneCsdnImage(object):
    def __init__(self):
        self.process = CrawlerProcess()

    def run(self):
        self.process.crawl(SceneCsdnImage)
        self.process.start()


def sched(cmd=None):
    if cmd == 'SceneCsdnTask':
        so = SceneCsdnTask()
    elif cmd == 'SceneCsdnDetail':
        so = SceneCsdnDetail()
    elif cmd == 'SceneCsdnImage':
        so = SceneCsdnImage()
    else:
        print("unkown cmd:%s"%(cmd) )
    so.run()

if __name__ == '__main__':
    cmd = sys.argv[1]
    sched(cmd)
    
    
