#   AUTHOR: Sibyl System
#     DATE: 2018-03-06
#     DESC: wordvector clustering

'''
详细说明：
将计算完成的词向量装进数据库
t_word_detail
'''

import re
import math
import json
import sys
import os
import numpy as np
from foundations.utils import *
from foundations.log import CLog
from config.inits import LOG_CFG
from preprocessors.batch_proc import *
from gensim.models import Word2Vec
from preprocessors.prep_db_handle import CPrepDbHandle

#全局变量
model_save_path = '/home/caonimabi/develop/job_data_mining/clusters/models/w2v_model'
DB_UPDATE_BATCH_SIZE = 10000   # 单次更新DB的行数，视内存大小而定
    
class CVectorLoader(BatchProc):
    def __init__(self):
        super(CVectorLoader, self).__init__("word_vector_loader",3)
        self.word_vector = {}
        self.model = Word2Vec.load(model_save_path)
        
    def _reset_monitor(self):
        super(CVectorLoader, self)._reset_monitor()
        self.word_vector = {}
        
    def _find_vectors(self,item):
        word = item["Fword"]
        self.word_vector[word] = self.model.wv[word]
    
    # 将每批处理结果讯息打印日志
    def gen_batch_report(self):
        UPlay       = self.abyss["UPlay"]
        UPoison     = self.abyss["UPoison"]
        URdead      = self.abyss["URdead"]
        Usurvive    = self.abyss["Usurvive"]
        
        if UPlay!=0:
            self.logger.log_info("You played %s times, survive %s times, \
            poisoned %s times, died %s times.\n \
                survival rate: %s, poison rate: %s, death rate: %s."\
                %(UPlay, Usurvive, UPoison, URdead, \
                    Usurvive/(UPlay), UPoison/UPlay, URdead/UPlay))
        else:
            self.logger.log_info("You processed zero content, please check your Sql")
        
    def update_word_vector(self):
        self._db.set_db_table('db_hiddens','t_word_detail')
        field_list = ['Fword','Fword_vector','Fmodify_time']
        data_list = []
        
        for word, vector in self.word_vector.items():
            modify_time = time_now()
            vector_string = json.dumps([str(num) for num in list(vector)])
            element = str((word, vector_string, modify_time))
            data_list.append(element)
        
        self._db.update_batch(field_list, data_list)
        self._db.commit()
            
    def process_doc(self,item):
        try:
            self._find_vectors(item)
        except Exception as e:
            self._failsafe(e,item)
        finally:
            self._bonfire()
            
    def run(self,items):
        for item in items:
            self.process_doc(item)
        
        self.update_word_vector()
        self.gen_batch_report()
        self._reset_monitor()
    
    def main(self):
        self.init_db()
        self.init_log()
        step = 10000
        offset = 0
        
        #self.logger.log_info('step:%s, offset:%s' %(step,offset))
        
        while(True):
            where = "Fauto_id between %s and %s"%(offset+1,offset+step)
            field_list = ['*']
            self._db.set_db_table('db_hiddens','t_word_detail')
            items = self._db.query(field_list, where)
            self._db.commit()
            
            if not items:
                break
            self.run(items)
            offset += step
            # break
        self.close()
        

if __name__ == '__main__':
    #with open('./sample.txt', 'r') as file:
    #    content = file.read()
    loader = CVectorLoader()
    loader.main()
    
    
    
