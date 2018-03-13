#   AUTHOR: Sibyl System
#     DATE: 2018-02-27
#     DESC: word2vector sentence builder

'''
详细说明：
将新词加入结巴分词，建立word2vector原始训练数据
'''

import re
import math
import json
import sys
import os
import jieba
import jieba.posseg as pseg
import numpy as np
from foundations.utils import *
from stop_words import STOP_WORDS_ENG
from full_stop_words import STOP_WORDS as FULL_STOP_WORDS
from preprocessors.prep_db_handle import CPrepDbHandle

NEW_WORDS_PATH = './new_words/'

# 被收入关键词的词性
# n-名词 ns-地点名词 nr-人物名词 v-动词 vn-动名词 a-形容词
# MarkedWordClass = ['ns', 'n', 'vn','nr','v', 'a']
MarkedWordClass = ['ns', 'n', 'vn','nr']

class CW2vSentenceBuilder:
    def __init__(self):
        self.new_words = {}     # 新词列表
        self.new_words_eng = {}     # 新单词列表
        self.stop_words = set(FULL_STOP_WORDS)
        self.stop_words_eng = set(STOP_WORDS_ENG)
        
    def __reset__(self):
        self.new_words = {}     # 新词列表
        self.new_words_eng = {}     # 新单词列表
        
    # 聚合新词，分中英两部分词
    def _gen_new_words(self):
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
    
    # 新词预处理
    def _new_word_preprocess(self):
        reserve_word_dict = {}
        pop_words = []
        for key, value in self.new_words.items():
            special_words_1 = re.findall('^[\u4e00-\u9fff]+[a-zA-Z]+$',key)
            special_words_2 = re.findall('^[a-zA-Z]+[\u4e00-\u9fff]+$',key)
            special_words = special_words_1 + special_words_2
            
            if special_words:
                special_word = special_words[0]
                pop_words.append( special_word )
                chi_words = re.findall('[\u4e00-\u9fff]',special_word)
                eng_words = re.findall('[a-zA-Z]',special_word)
                
                if len(chi_words) > 1:
                    reserve_words = (re.findall('[\u4e00-\u9fff]+',special_word))
                    reserve_word = reserve_words[0]
                    try:
                        reserve_word_dict[reserve_word]+=value
                    except:
                        reserve_word_dict[reserve_word]=value
                        
        for key, value in reserve_word_dict.items():
            try:
                self.new_words[key]+=value
            except:
                self.new_words[key]=value
                
        for pop_word in pop_words:
            if pop_word in self.new_words.keys():
                self.new_words.pop(pop_word)
    
    # 将新词加入结巴分词器
    def _renew_jieba(self):
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
    def _content_preprocess(self, content):
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
    def _words_preprocess(self, words_info):
        chosen_flags = set(MarkedWordClass)
        words = []

        for word, flag in words_info:
            if flag in chosen_flags:
                words.append(word)
            elif flag == 'eng' and word in self.new_words_eng.keys():
                words.append(word.upper())
        return words
                
    # 构造word2vector训练数据
    def _run(self, job_infos):
        with open('../clustering/training_data/w2v_sentence.txt', 'w') as file:
            sentence_cache = []    # 句子缓存，一次写入多行，提高写文件效率
            max_size = 10000    # 一次性写入最大句子数：1W句
            job_infos_size = len(job_infos)
            for idx in range(len(job_infos)):
                content = job_infos[idx]['content']
                job_id = job_infos[idx]['job_id']
                content = self._content_preprocess(content)
                if content:
                    words_info = pseg.cut(content)
                    words = self._words_preprocess(words_info)
                    if words:
                        sentence = ' '.join(words)
                        sentence_cache.append(sentence+'\n')
                if len(sentence_cache) >= max_size or idx==(job_infos_size-1):
                    file.writelines(sentence_cache)
                    sentence_cache = []
                
    # 总结内存消耗量
    def _summarize_mem_csmp(self):
        pass
    
    # 主过程
    def process(self,job_infos):
        print('cluster new words')
        self._gen_new_words()
        print('new words preprocess')
        self._new_word_preprocess()
        print('dump result, renew jieba database')
        self._renew_jieba()
        print('read content')
        self._run(job_infos)
        #print('show memory csmp')
        #self._summarize_mem_csmp()
        print('process finished, now reset to initial state')
        
        self.__reset__()
        

if __name__ == '__main__':
    #with open('./sample.txt', 'r') as file:
    #    content = file.read()
    w2v_sentence_builder = CW2vSentenceBuilder()
    
    temp_db = CPrepDbHandle()
    
    where = "Fjob_summary!='' order by Fauto_id limit 200000 offset 0"
    field_list = ['Fjob_summary as content', 'Fauto_id as job_id']
    temp_db.set_db_table('db_job','t_zhilian_detail')
    results = temp_db.query(field_list, where)
    #contents = ['结衣我老婆，saber我老婆，两仪我老婆']
    job_infos = [result for result in results]
    w2v_sentence_builder.process(job_infos)
    
    
    
