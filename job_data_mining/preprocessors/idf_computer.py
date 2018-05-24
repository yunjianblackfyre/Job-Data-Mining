#   AUTHOR: Sibyl System
#     DATE: 2018-04-24
#     DESC: 关键词IDF值全量更新

'''
关键词IDF值全量更新
流水批量读取预处理成功的文档
提取文本信息，计数每个词所属文档数
'''

# import ssl
# import requests
# import urllib.request
# from urllib.request import Request

import os
import numpy
import time
import numpy as np
from foundations.log import CLog
from config.inits import LOG_CFG
from foundations.utils import *
from preprocessors.batch_proc import *
from preprocessors.error import ErrCode
from gensim.models.word2vec import LineSentence

SENTENCE_CACHE_SIZE = 1        # 每一份文档大约1MB左右，视内存大小而定
DB_UPDATE_BATCH_SIZE = 10000   # 单次更新DB的行数，视内存大小而定

class IdfComputer(BatchProc):

    def __init__( self ):
        super(IdfComputer, self).__init__("idf_computer",3)
        
        # 后续根据任务的进行会发生改变的变量
        self.word_dict = {}
        self.Doc_count = 0
        self.word_count = 0
        self.id2word = {}
        self.word2idf = {}
        self.word2info = {}
        
    def __gen_words(self, item):
        self.Doc_count += 1
        words = list(item)
        local_word_dict = {}
        filtered_words = []
        filtered_words = filter_words(words,freq_thresh=1,len_thresh=15)
                
        for word in set(filtered_words):
            map_reduce(self.word_dict,word)
        
    def load_base_info(self):
        for word, value in self.word_dict.items():
            try:
                self.word2info[word][1]+=value
            except:
                self.word2info[word] = np.array([self.word_count,value])
                self.id2word[self.word_count]=word
                self.word_count +=1
                
    def compute_idf(self):
        arr_idf_wordidx =  np.zeros(self.word_count, dtype='int32')
        arr_Doc_num     =  np.zeros(self.word_count, dtype='float64')
        arr_word_count  =  np.zeros(self.word_count, dtype='float64')
        arr_idf         =  np.zeros(self.word_count, dtype='float64')
        
        # 填装IDF列表容器
        Doc_num = self.Doc_count
        loop_count = 0
        for key, value in self.word2info.items():
            word_idx = value[0]
            word_count = value[1]
            arr_idf_wordidx[loop_count] =   word_idx
            arr_Doc_num[loop_count] =       Doc_num
            arr_word_count[loop_count] =    word_count
            loop_count += 1
            
        # NUMPY高速运算
        arr_idf = np.log(arr_Doc_num/arr_word_count)
        
        # 计算结果打包
        for loop_count in range(len( arr_idf )):
            idf = arr_idf[loop_count]
            word_idx = arr_idf_wordidx[loop_count]
            word = self.id2word[word_idx]
            self.word2idf[word]=idf
            
    def update_word_detail(self):
        self._db.set_db_table('db_hiddens','t_word_detail')
        field_list = ['Fword','Fword_idf','Fmodify_time']
        data_list = []
        
        for word, idf in self.word2idf.items():
            modify_time = time_now()
            element = str((word, idf, modify_time))
            data_list.append(element)
        
        # 开始批量更新
        step = DB_UPDATE_BATCH_SIZE
        offset = 0              # 偏移量
        len_data = len(data_list)    # 数据总长
        while(offset < len_data):
            left_border = offset
            right_border = (offset + step)
            right_border = len_data if right_border > len_data else right_border
            offset += step
            self._db.update_batch(field_list, data_list[left_border:right_border])
            self._db.commit()
    
    # 将每次处理结果讯息打印日志
    def gen_single_report(self,item):
        content_id = item['Fauto_id']
        origin_url = item['Fh5_url']
        result = self.firelinker["result"]
        self.logger.log_info("item with id %s,origin url %s, result:%s"
              %(content_id, origin_url, result))
    
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
        
    def process_doc(self,item):
        try:
            self.__gen_words(item)
        except Exception as e:
            self._failsafe()
        finally:
            self._bonfire()
            # self.gen_single_report(item)
            
    def process_batch(self,items):
        for item in items:
            self.process_doc(item)
        
        self.gen_batch_report()
        self._reset_monitor()
    
    def wind_up(self):
        self.load_base_info()
        self.compute_idf()
        self.update_word_detail()
        
    def main(self):
        self.init_db()
        self.init_log()
        training_data_path = "/home/caonimabi/develop/job_data_mining/preprocessors/training_data/data_clusters/"
        files = os.listdir(training_data_path)
        counter = 0
        sentences_cache = []
        for file in files:
            self.logger.log_info("file %s loaded"%file)
            sentences = list(LineSentence(training_data_path+file)) # 读到内存中
            sentences_cache.extend(sentences)
            counter += 1
            if counter > SENTENCE_CACHE_SIZE:
                self.logger.log_info("%s files loaded, now load base info"%SENTENCE_CACHE_SIZE)
                self.process_batch(sentences_cache)
                sentences_cache = []
                counter = 0
                
        self.logger.log_info("here is the last shipment")
        self.process_batch(sentences_cache)
        sentences_cache = []
        self.wind_up()
    
# 单次测试用
if __name__ == '__main__':
    tool = IdfComputer()
    tool.main()
    