#   AUTHOR: Sibyl System
#     DATE: 2018-01-03
#     DESC: Doc-matrix builder

'''
详细说明：
将新词加入结巴分词，建立文档-关键词矩阵
该矩阵将用于下一步的主题提取计算
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

class CDWMatBuilder:
    def __init__(self):
        self.new_words = {}     # 新词列表
        self.new_words_eng = {}     # 新单词列表
        self.stop_words = set(FULL_STOP_WORDS)
        self.stop_words_eng = set(STOP_WORDS_ENG)
        self.id2Doc = {}
        self.id2Word = {}
        self.id2DWcnt = {}
        self.word2info = {}
        self.word_count = 0
        self.Doc_count = 0
        self.none_zero_entries = 0
        
    def __reset__(self):
        self.new_words = {}     # 新词列表
        self.new_words_eng = {}     # 新单词列表
        self.id2Doc = {}
        self.id2Word = {}
        self.id2DWcnt = {}
        self.word2info = {}
        self.word_count = 0
        self.Doc_count = 0
        self.none_zero_entries = 0
        
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
        eng_words = []
        for word, flag in words_info:
            if flag in chosen_flags:
                words.append(word)
            elif flag == 'eng' and word in self.new_words_eng.keys():
                eng_words.append(word.upper())
        return words, eng_words
        
    # 装载 文档-词语 基础信息
    def _load_base_info(self, words, job_id):
        word2freq = {}
        unique_words = set(words)
        
        self.id2DWcnt[job_id]=0
        for word in words:
            try:
                word2freq[word]+=1
            except:
                word2freq[word]=1
            finally:
                self.id2DWcnt[job_id]+=1
        
        self.id2Doc[job_id] = tuple([(key, value) for key, value in word2freq.items()])
        self.Doc_count += 1
                
        for word in unique_words:
            self.none_zero_entries += 1
            try:
                self.word2info[word][1]+=1
            except:
                self.word2info[word] = np.array([self.word_count,1])
                self.id2Word[self.word_count]=word
                self.word_count +=1
                
                
    # 构造矩阵
    def _run(self, job_infos):
        # 构建基础信息
        for job_info in job_infos:
            content = job_info['content']
            job_id = job_info['job_id']
            content = self._content_preprocess(content)
            if content:
                words_info = pseg.cut(content)
                words, eng_words = self._words_preprocess(words_info)
                words.extend(eng_words)
                self._load_base_info(words, job_id)
                
        # print_dict(self.id2Doc)
        # print_dict(self.id2DWcnt)
        # print_dict(self.word2info)
        
        #print('--------matrix building start--------')
                
        # 初始化TFIDF稀疏矩阵计算容器
        arr_tfidf_wordidx =  np.zeros(self.none_zero_entries, dtype='int32')
        arr_tfidf_Docidx =   np.zeros(self.none_zero_entries, dtype='int32')
        arr_Doc_num =        np.zeros(self.none_zero_entries, dtype='float64')
        arr_word_count =     np.zeros(self.none_zero_entries, dtype='float64')
        arr_Doc_word_count = np.zeros(self.none_zero_entries, dtype='float64')
        arr_word_Doc_count = np.zeros(self.none_zero_entries, dtype='float64')
        arr_tfidf          = np.zeros(self.none_zero_entries, dtype='float64')
        
        # 填装TFIDF稀疏矩阵计算容器
        Doc_num = self.Doc_count
        loop_count = 0
        for key, value in self.id2Doc.items():
            Doc_idx = key
            Doc_word_count = self.id2DWcnt[key]
            for word_tuple in value:
                word = word_tuple[0]
                
                arr_tfidf_wordidx[loop_count] =  self.word2info[word][0]
                arr_tfidf_Docidx[loop_count] =   Doc_idx                    
                arr_Doc_num[loop_count] =        Doc_num                    # (4)
                arr_word_count[loop_count] =     word_tuple[1]              # (1)
                arr_Doc_word_count[loop_count] = Doc_word_count             # (3)
                arr_word_Doc_count[loop_count] = self.word2info[word][1]    # (2)
                
                #print("Doc_idx:%s word_idx:%s word:%s word_count:%s, word_Doc_count:%s"%\
                #     (arr_tfidf_Docidx[loop_count], arr_tfidf_wordidx[loop_count], word, \
                #        arr_word_count[loop_count], arr_word_Doc_count[loop_count]))
                loop_count += 1
                
        # 计算TFIDF稀疏矩阵
        arr_tfidf = (np.log(arr_Doc_num/arr_word_Doc_count))*(arr_word_count/arr_Doc_word_count)
        
        # 单独计算词IDF，用于增量数据
        word_idx_list = []
        word_Doc_count_list = []
        for key, value in self.word2info.items():
            word_idx_list.append(value[0])
            word_Doc_count_list.append(value[1])
            
        arr_idf_wordidx = np.array(word_idx_list, dtype='int32')
        arr_word_Doc_count = np.array(word_Doc_count_list, dtype='float64')
        arr_Doc_num = np.ones(self.word_count,dtype='float64')*(self.Doc_count)
        arr_idf = np.zeros(self.word_count,dtype='float64')
        arr_idf = np.log( arr_Doc_num/arr_word_Doc_count )
        
        np.save('./numpy_array/tfidf_value_array',arr_tfidf)
        np.save('./numpy_array/tfidf_wordidx_array',arr_tfidf_wordidx)
        np.save('./numpy_array/tfidf_Docidx_array',arr_tfidf_Docidx)
        np.save('./numpy_array/idf_value_array',arr_idf)
        np.save('./numpy_array/idf_wordidx_array',arr_idf_wordidx)
        with open('./mapping_dict/id2Word.txt','wb') as out: 
            out.write(bytes(json.dumps(self.id2Word).encode()))
        
        # 测试计算结果
        temp_dict = {}
        for loop_count in range(len( arr_tfidf )):
            tfidf = arr_tfidf[loop_count]
            word_idx = arr_tfidf_wordidx[loop_count]
            word = self.id2Word[word_idx]
            Doc_idx = arr_tfidf_Docidx[loop_count]
            try:
                temp_dict[Doc_idx].append((word,tfidf))
            except:
                temp_dict[Doc_idx] = [(word,tfidf)]
        # print_dict(temp_dict)
        
    # 总结内存消耗量
    def _summarize_mem_csmp(self):
        #print('size of word2info:',get_size(self.word2info)/(1024*1024),'MB')
        #print('size of id2Doc:',get_size(self.id2Doc)/(1024*1024),'MB')
        print('size of Doc-Word matrix: %s by %s'%(self.Doc_count, self.word_count))
    
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
    matrix_builder = CDWMatBuilder()
    
    temp_db = CPrepDbHandle()
    
    where = "Fjob_summary!='' order by Fauto_id limit 200000 offset 0"
    field_list = ['Fjob_summary as content', 'Fauto_id as job_id']
    temp_db.set_db_table('db_job','t_zhilian_detail')
    results = temp_db.query(field_list, where)
    #contents = ['结衣我老婆，saber我老婆，两仪我老婆']
    job_infos = [result for result in results]
    matrix_builder.process(job_infos)
    
    
    
