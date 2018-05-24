#   AUTHOR: Sibyl System
#     DATE: 2018-01-03
#     DESC: 数据批处理基类

'''
批量数据处理基类
被所有数据批量处理类继承
'''

import re
import math
import json
import sys
from foundations.log import CLog
from config.inits import LOG_CFG
from multiprocessing import Process,Pool
from foundations.utils import *
from preprocessors.prep_db_handle import CPrepDbHandle
from crawlers.utils import *
RETRY_TIMES = 0

def filter_words(sentence,freq_thresh=3,len_thresh=8):
    word_freq = {}
    fine_sentence = []
    # 获取词频
    for word in sentence:
        map_reduce(word_freq,word)
    # 根据词频过滤词
    for word in sentence:
        if word_freq[word] > freq_thresh and len(word) < len_thresh:
            fine_sentence.append(word)
    return fine_sentence

class BatchProc:

    def __init__(self,log_file_name,log_level):
        self.firelinker = {     # 当前函数为下一个函数提供的数据
            "result":"Usurvive"  # 初始化为“成功”
        }    
        self.abyss = {          # 异常、缺陷信息统计器
            "Usurvive":0,
            "URdead":0,
            "UPoison":0,
            "UPlay":0
        }
        self.log_file_name =    log_file_name
        self.log_level =        log_level
        
    def _reset_monitor(self):
        self.firelinker = {     # 当前函数为下一个函数提供的数据
            "result":"Usurvive"  # 初始化为“成功”
        }    
        self.abyss = {          # 异常、缺陷信息统计器
            "Usurvive":0,
            "URdead":0,
            "UPoison":0,
            "UPlay":0
        }
        
    def _bonfire(self):
        result = self.firelinker["result"]
        self.abyss[result]+=1
        self.abyss["UPlay"]+=1
        self.firelinker = {
            "result":"Usurvive"
        }
        
    def _failsafe(self,e,item):
        self._db.rollback()
        self.firelinker["result"] = "URdead"
        self.logger.log_info(traceback.format_exc())
        
    def init_db(self):
        self._db = CPrepDbHandle()
        
    def init_log(self):
        self.logger = CLog()
        self.logger.init( self.log_file_name, LOG_CFG["dir"], self.log_file_name, self.log_level)
        
    def close(self):
        if self._db:
            self._db.destroy()
        self._db = None
    
    def run(self):
        raise NotImplementedException
        
    def main(self):
        try:
            self.init_db()
            self.init_log()
            self.run()
            self.close()
        except:
            self.logger.log_info(traceback.format_exc())
            time.sleep(10)
            global RETRY_TIMES
            if RETRY_TIMES > 0:
                RETRY_TIMES -= 1
                self.main()
            else:
                RETRY_TIMES = 3