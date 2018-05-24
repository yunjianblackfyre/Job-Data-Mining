#   AUTHOR: Sibyl System
#     DATE: 2018-04-25
#     DESC: 

'''
构造word2vector模块所需的训练数据
训练数据构建方法大致描述：
将文本用结巴分词成词序列，并且过滤之，如下：
文档1:C++ 教学 模块 训练 指针
文档2:python3 AI 大数据 人工智能
文档3:区块链 去中心化
......
将这些序列换行保存在一个.txt文件中，预计
该文件的计量单位为G级别
'''

# import ssl
# import requests
# import urllib.request
# from urllib.request import Request

import numpy
import time
import jieba
import jieba.posseg as pseg
import numpy as np
from preprocessors.zhilian_preproc import renew_jieba
from preprocessors.zhilian_preproc import extract_zhilian_detail
from foundations.utils import *
from full_stop_words import STOP_WORDS_ENG, STOP_WORDS
from preprocessors.batch_proc import *
from preprocessors.error import ErrCode
from multiprocessing import Process,Pool

TRAINING_DATA_PATH = "/home/caonimabi/develop/job_data_mining/preprocessors/training_data/data_clusters/"
mark_tag_set = set(['n', 'nz', 'vn','eng'])

def extract_keyword(keyword_list, line):
    line = line.strip()
    if line:
        words_info = list(pseg.cut(line))
        for word, flag in words_info:
            
            # if flag in flag_dict.keys():
            #     flag_dict[flag].add(word)
            # else:
            #     flag_dict[flag] = set([word])

            if flag in mark_tag_set and len(word) > 1: # 一个字的不要
                
                if flag == "eng":
                    if word not in STOP_WORDS_ENG:
                        keyword_list.append(word.upper())  # 英文统一转为大写
                elif word not in STOP_WORDS:
                    keyword_list.append(word)

class TrainDataBuilder(BatchProc):

    def __init__( self,batch_size,proc_id, proc_num ):
        super(TrainDataBuilder, self).__init__("train_data_builder",3)
        self.batch_size = batch_size
        self.proc_id    = proc_id
        self.proc_num   = proc_num
        self.step = 0
        self.offset = 0
        self.result_list = []
        
    def __load_content(self, item):
        content = extract_zhilian_detail(item["Fjob_summary"])

        if not content:
            return
            #self.logger.log_info("item with id %s,origin url %s, has empty content"
            #    %(item['Fauto_id'], item['Fjob_url']))
            #raise Exception
        
        # 检测英文含量是否超标
        eng_words = re.findall('[a-zA-Z]{2,}',content)
        none_eng_words = re.findall('[\u4e00-\u9fff]',content)
        eng_ratio = len(eng_words)/( len(none_eng_words)+0.001 )
        if eng_ratio >= 0.5:
            self.logger.log_info("item with id %s,origin url %s, has too many english words"
                %(item['Fauto_id'], item['Fjob_url']))
            self.logger.log_info(content)
            raise Exception
            
        content = re.sub("\s+"," ",content)
        extract_keyword(self.result_list, content)
        self.result_list.append('\n')
                
    def save2file(self):
        file_name = "_".join(["w2v",str(self.proc_id), str(self.offset), str(self.offset + self.batch_size)])
        file_name = TRAINING_DATA_PATH + file_name + ".txt"
        with open(file_name, 'w') as file_handler:
            sentence_cache = " ".join(self.result_list)
            file_handler.writelines(sentence_cache)
            file_handler.close()
        self.result_list = []
        
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
            self.__load_content(item)
        except Exception as e:
            self._failsafe(e, item)
        finally:
            # self.gen_single_report(item)
            self._bonfire()
        
    def process_batch(self, items):
        # self.flag_dict = {}
        for item in items:          # 这一块用多进程
            self.process_doc(item)
        
        try:
            self.gen_batch_report()
            self.save2file()
        except Exception as e:
            self.logger.log_info(traceback.format_exc())
        finally:
            self._reset_monitor()
        
    def run(self):
        renew_jieba()
        self.step = self.batch_size*self.proc_num
        self.offset = self.proc_id*self.batch_size
        
        self.logger.log_info('step:%s, offset:%s' %(self.step,self.offset))
        while(True):
            where = "Fauto_id between %s and %s"%(self.offset+1,self.offset+self.batch_size)
            # where = "Fauto_id between 18000 and 19000"
            self.logger.log_info('process_id:%s, sql condition:%s' %(self.proc_id,where))
            field_list = ['*']
            self._db.set_db_table('db_crawlers','t_zhilian_detail')
            items = self._db.query(field_list, where)
            self._db.commit()
            
            if not items:
                break
            self.process_batch(items)
            self.offset += self.step
            # break      # 调试用，记删
            time.sleep(2)
        
def run_task(batch_size,proc_id, proc_num):
    tool = TrainDataBuilder(batch_size,proc_id, proc_num)
    tool.main()
    
    
def distribute_task(batch_size):
    p = Pool()           #开辟进程池
    for i in range(2):
        p.apply_async(run_task,args=(batch_size, i, 2))
    p.close() #关闭进程池
    p.join()
    
# 单次测试用
if __name__ == '__main__':
    #distribute_task(10000)
    
    tool = TrainDataBuilder(10000,0, 1)
    tool.main()