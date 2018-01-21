#   AUTHOR: Sibyl System
#     DATE: 2018-01-03
#     DESC: Doc-matrix builder

'''
详细说明：
将新词加入结巴分词，建立文档-关键词矩阵
该矩阵将用于下一步的主题提取计算
该文件未完待续...
'''

import re
import math
import json
import sys
import os
from foundations.utils import *
import jieba
import jieba.posseg as pseg
from stop_words import STOP_WORDS_ENG
from full_stop_words import STOP_WORDS as FULL_STOP_WORDS
from preprocessors.prep_db_handle import CPrepDbHandle

NEW_WORDS_PATH = './new_words/'

class DWMatrixBuilder:
    def __init__(self):
        self.new_words = {}     # 新词列表
        self.new_words_eng = {}     # 新单词列表
        self.stop_words = set(FULL_STOP_WORDS)
        self.stop_words_eng = set(STOP_WORDS_ENG)
        
    def reset(self):
        self.new_words = {}     # 新词列表
        self.new_words_eng = {}     # 新单词列表
        
    # 聚合新词，分中英两部分词
    def make_new_words(self):
        # 初始化变量
        filename_pattern = '^new_words\_\d+\.txt$'
        filename_pattern_eng = '^new_words\_eng\_\d+\.txt$'
        files = os.listdir(NEW_WORDS_PATH)
        new_word_files = []
        new_word_eng_files = []
        new_word_dict_list = []
        new_word_eng_dict_list = []
        
        # 获取文件名列表
        for file in files:
            new_word_files.extend( re.findall(filename_pattern, file) )
            new_word_eng_files.extend( re.findall(filename_pattern_eng, file) )
            
        # 读取汉语新词文件到内存
        for file in new_word_files:
            try:
                with open(NEW_WORDS_PATH+file,'r') as f:
                    new_word_dict_list.append(json.loads(f.read()))
            except:
                print(traceback.format_exc())
                
        # 读取英语新词文件到内存
        for file in new_word_eng_files:
            try:
                with open(NEW_WORDS_PATH+file,'r') as f:
                    new_word_eng_dict_list.append(json.loads(f.read()))
            except:
                print(traceback.format_exc())
                
        # 聚合所有汉语新词
        for new_word_dict in new_word_dict_list:
            for key, value in new_word_dict.items():
                if key not in self.stop_words:
                    try:
                        self.new_words[key]+=value
                    except:
                        self.new_words[key]=value
                    
        # 聚合所有英文新词
        for new_word_eng_dict in new_word_eng_dict_list:
            for key, value in new_word_eng_dict.items():
                if key not in self.stop_words_eng:
                    try:
                        self.new_words_eng[key]+=value
                    except:
                        self.new_words_eng[key]=value
    
    # 将新词加入结巴分词器
    def renew_jieba(self):
        file_name = './new_words/new_words.txt'
        with open(file_name, 'w') as f:
            f.write(json.dumps(self.new_words))
            
        file_name = './new_words/new_words_eng.txt'
        with open(file_name, 'w') as f:
            f.write(json.dumps(self.new_words_eng))
            
        # 将文件写成jieba可读的形式
        # 例如 机器学习 nv 612
        # 标注 词  词性（这里n是名词，v是动词） 词频
        file_name = './new_words/new_words4jieba.txt'
        with open(file_name, 'w') as f:
            for key, value in self.new_words.items():
                line = '%s %s vn\n'%( key, str(value) ) # 按照ICTPOS标记法，将所有新词标记为动名词
                f.write(line)
                
        # 更新结巴分词器
        file_name = './new_words/new_words4jieba.txt'
        jieba.load_userdict(file_name)
    
    # 对文档进行预处理
    def content_preprocess(self, content):
        # 过滤符号
        content = re.sub('\s+',' ',content)
        
        # 若本文档为英文，则跳过
        eng_words = re.findall('[a-zA-Z]{2,}',content)
        none_eng_words = re.findall('[\u4e00-\u9fff]',content)
        eng_ratio = len(eng_words)/( len(none_eng_words)+0.001 )
        
        if eng_ratio >= 0.25:
            return ''
        
        content = content.replace('智能','智慧')
        content = content.replace('个性','性格')
        content = content.replace('并发','霰发')
        content = content.replace('并行','霰行')
        return content
        
    # 对词列表进行预处理
    def words_preprocess(self, words_info):
        chosen_flags = set(['ns', 'n', 'vn'])
        words = []
        eng_words = []
        for word, flag in words_info:
            if flag in chosen_flags:
                words.append(word)
            elif flag == 'eng' and word in self.new_words_eng.keys():
                eng_words.append(word)
        return words, eng_words
    
    # 构造矩阵
    def run(self, job_infos):
        for job_info in job_infos:
            content = job_info['content']
            job_id = job_info['job_id']
            content = self.content_preprocess(content)
            if content:
                words_info = pseg.cut(content)
                words, eng_words = self.words_preprocess(words_info)
                print('--------job info---------')
                print(content)
                print(set(words))
                print(set(eng_words))
                
    # 总结内存消耗量
    def summarize_mem_csmp(self):
        raise TypeError
        # print('size of word2entr_dict:',sys.getsizeof(self.word2entr_dict)/(1024*1024),'MB')
    
    # 主过程
    def process(self,job_infos):
        print('cluster new words')
        self.make_new_words()
        print('dump result, renew jieba database')
        self.renew_jieba()
        print('read content')
        self.run(job_infos)
        print('process finished, now reset to initial state')
        self.reset()
        # self.summarize_mem_csmp()

if __name__ == '__main__':
    #with open('./sample.txt', 'r') as file:
    #    content = file.read()
    matrix_builder = DWMatrixBuilder()
    
    temp_db = CPrepDbHandle()
    
    where = "Fjob_summary!='' order by Fauto_id limit 100 offset 0"
    field_list = ['Fjob_summary as content', 'Fauto_id as job_id']
    temp_db.set_db_table('db_job','t_zhilian_detail')
    results = temp_db.query(field_list, where)
    #contents = ['结衣我老婆，saber我老婆，两仪我老婆']
    job_infos = [result for result in results]
    matrix_builder.process(job_infos)
    
    
    
