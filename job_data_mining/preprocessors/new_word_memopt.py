# coding=utf-8

import re
import math
import json
import sys
import zlib
from foundations.utils import *
from preprocessors.prep_db_handle import CPrepDbHandle
from stop_words import STOP_WORDS
from stop_words import STOP_PATTERNS
from full_stop_words import STOP_WORDS as FULL_STOP_WORDS

MAX_TOLERANCE = 5
FREE_LVL_THRESH = 1.4   # 自由度阈值
SLD_LVL_THRESH = 40     # 凝固度阈值

class NewWordExtract:
    # 初始化
    def __init__(self):
        self.word2prob = {}     # 词概率
        self.word2entr_dict = {}  # 词索引表
        self.word2sld_lvl = {}  # 凝固度
        self.word2free_lvl = {} # 自由度
        self.words = []
        self.len_contents = 0
        self.stop_words = STOP_WORDS
        self.stop_word_pattern = STOP_PATTERNS
        self.full_stop_words = FULL_STOP_WORDS
    
    # 重置
    def reset(self):
        self.word2prob = {}     # 词概率
        self.word2entr_dict = {}  # 词索引表
        self.word2sld_lvl = {}  # 凝固度
        self.word2free_lvl = {} # 自由度
        self.words = []
        self.len_contents = 0
    
    # 输出资源消耗信息
    def summarize_mem_csmp(self):
        print('size of word2entr_dict:',sys.getsizeof(self.word2entr_dict)/(1024*1024),'MB')
        print('size of word2prob:',sys.getsizeof(self.word2prob)/(1024*1024),'MB')
        print('size of word2sld_lvl:',sys.getsizeof(self.word2sld_lvl)/(1024*1024),'MB')
        print('size of word2free_lvl:',sys.getsizeof(self.word2free_lvl)/(1024*1024),'MB')
        print('size of words:',sys.getsizeof(self.words)/(1024*1024),'MB')
        
    # 提取可疑的停用词
    def suspicious_stop_words(self):
        single_stop_words = []
        suspicious_info_list = []
        for stop_word in self.full_stop_words:
            if len(stop_word) == 1:
                single_stop_words.append(stop_word)
                
        # 将单个停止词语自由词做成集合，加快查询速度
        
        single_stop_words = set(single_stop_words)
        
        for free_word in self.word2free_lvl.keys():
            for sword in free_word:
                if sword in single_stop_words:
                    # 计算可疑停用词的各项属性
                    free_lvl = self.word2free_lvl[free_word] 
                    sld_lvl = self.word2free_lvl[free_word]
                    prob = self.word2prob[free_word]
                    
                    suspicious = {}
                    #suspicious['free_lvl'] = free_lvl
                    #suspicious['sld_lvl'] = sld_lvl
                    #suspicious['prob'] = prob
                    suspicious['sword'] = sword
                    suspicious['free_word'] = free_word
                    suspicious_info_list.append(suspicious)
                    
        suspicious_info_list = sorted(suspicious_info_list, key=lambda k: k['sword'])
        print_list(suspicious_info_list)
    
    # 建立全局词列表
    def make_words(self,contents):
        for content in contents:
            # 过滤符号
            content = re.sub('\W+',' ',content)
            
            # 正则停用词
            for pattern in self.stop_word_pattern:
                content = re.sub(pattern,'',content)
                
            # 替换停用词
            content = content.replace('智能','智慧')
            content = content.replace('个性','性格')
            content = content.replace('并发','霰发')
            content = content.replace('并行','霰行')
            
            for stop_word in self.stop_words:
                # 过滤停用词
                content = content.replace(stop_word,'')
            
            # 找出单个汉字与单个单词
            self.words.extend(re.findall('[\u4e00-\u9fff]|[a-zA-Z]+',content))
    
    # 计算基础属性
    def calc_base_property( self,tolerance ):
        if tolerance > MAX_TOLERANCE or tolerance < 2:
            raise Exception(1,'tolerance exceded')
            
        # 初始化变量
        self.len_words = (len(self.words)-tolerance + 1)*tolerance
        self.len_contents = len(self.words)
            
        for idx in range(self.len_contents):
            if idx%( int(self.len_contents/100) )==0:
                print('processing progress:%s'%(idx/(self.len_contents/100)) )
                print('dict length:%s, dict size:%s MB'%(len(self.word2prob.keys()), sys.getsizeof(self.word2prob)/(1024*1024)) )
                
            for offset in range(0,tolerance):
                edge = idx+offset+1
                if edge > self.len_contents:
                    break
                    
                this_word = ''.join( self.words[idx:edge] )
                
                # 填装词->频率映射
                if this_word not in self.word2prob.keys():
                    self.word2prob[this_word] = 1/self.len_words
                else:
                    self.word2prob[this_word] += 1/self.len_words
                    
                # 填装词->左右词典
                right_idx = idx-1
                left_idx = idx+offset+1
                
                if this_word in self.word2entr_dict.keys() and offset > 0:
                    left_word = self.words[right_idx] if right_idx > -1 else ''
                    right_word = self.words[left_idx] if left_idx < self.len_contents else ''
                    
                    # 填装左词典
                    if left_word:
                        left_word_tuple = self.word2entr_dict[this_word]['left_word']
                        left_word_str = zlib.decompress(left_word_tuple[0]).decode()
                        left_idx_str = zlib.decompress(left_word_tuple[1]).decode()
                        left_word_list = [item for item in left_word_str.split('|') if item]
                        left_wordidx_list = [item for item in left_idx_str.split('|') if item]
                        try:
                            num_idx = left_word_list.index(left_word)
                            freq = left_wordidx_list[num_idx]
                            freq = str(int(freq)+1)
                            left_wordidx_list[num_idx] = freq
                        except:
                            left_word_list.append(left_word)
                            left_wordidx_list.append('1')
                            
                        left_word_str = '|'.join(left_word_list)
                        left_idx_str = '|'.join(left_wordidx_list)
                        left_word_str = zlib.compress(left_word_str.encode())
                        left_idx_str = zlib.compress(left_idx_str.encode())
                        
                        self.word2entr_dict[this_word]['left_word'] = (left_word_str, left_idx_str)
                        
                        
                    # 填装右词典
                    if right_word:
                        right_word_tuple = self.word2entr_dict[this_word]['right_word']
                        right_word_str = zlib.decompress(right_word_tuple[0]).decode()
                        right_idx_str = zlib.decompress(right_word_tuple[1]).decode()
                        right_word_list = [item for item in right_word_str.split('|') if item]
                        right_wordidx_list = [item for item in right_idx_str.split('|') if item]
                        try:
                            num_idx = right_word_list.index(right_word)
                            freq = right_wordidx_list[num_idx]
                            freq = str(int(freq)+1)
                            right_wordidx_list[num_idx] = freq
                        except:
                            right_word_list.append(right_word)
                            right_wordidx_list.append('1')
                            
                        right_word_str = '|'.join(right_word_list)
                        right_idx_str = '|'.join(right_wordidx_list)
                        right_word_str = zlib.compress(right_word_str.encode())
                        right_idx_str = zlib.compress(right_idx_str.encode())
                        
                        self.word2entr_dict[this_word]['left_word'] = (right_word_str, right_idx_str)
                    
                elif offset > 0:
                    left_word = self.words[right_idx] if right_idx > -1 else ''
                    right_word = self.words[left_idx] if left_idx < self.len_contents else ''

                    left_word = zlib.compress(left_word.encode())
                    right_word = zlib.compress(right_word.encode())
                    left_idx = zlib.compress('1'.encode())
                    right_idx = zlib.compress('1'.encode())
                    empty_str = zlib.compress(''.encode())
                    
                    right_word_tuple = (right_word,right_idx) if right_word else (empty_str,empty_str)
                    left_word_tuple = (left_word,left_idx) if  left_word else (empty_str,empty_str)
                    self.word2entr_dict[this_word]={'right_word':right_word_tuple,'left_word':left_word_tuple}
    
    # 计算高级属性
    def calc_advanced_property(self):
        for word in self.word2entr_dict.keys():
            sld_lvl = self.calc_word_sld_lvl(word)
            free_lvl = self.calc_word_free_lvl(word)
            if free_lvl > 1.4:
                self.word2sld_lvl[word] = sld_lvl      # 凝固度
                self.word2free_lvl[word] = free_lvl    # 自由度
        sld_lvl_list = sorted(self.word2sld_lvl.items(), key=lambda d: d[1])
        with open('./result.txt', 'w') as f:
            f.write(json.dumps(sld_lvl_list))
    
    # 计算凝固度
    def calc_word_sld_lvl(self,word):
        
        words = re.findall('[\u4e00-\u9fff]|[a-zA-Z]+',word)
        len_word = len(words)
        sld_lvl_list = []
        sld_lvl = 0.0
        for idx in range(1,len_word):
            word_1 = ''.join(words[0:idx])
            word_2 = ''.join(words[idx:len_word])
            word_1_prob = self.word2prob[word_1]
            word_2_prob = self.word2prob[word_2]
            word_prob = self.word2prob[word]
            sld_lvl_list.append( word_prob/(word_1_prob*word_2_prob) )
        if sld_lvl_list:
            sld_lvl = min(sld_lvl_list)
        return sld_lvl
    
    # 计算自由度
    def calc_word_free_lvl(self, word):
        # 降低内存开销
        right_word_tuple = self.word2entr_dict[word]['right_word']
        left_word_tuple = self.word2entr_dict[word]['left_word']
        right_idx_str = zlib.decompress(right_word_tuple[1]).decode()
        left_idx_str = zlib.decompress(left_word_tuple[1]).decode()
        
        right_freq_list = [int(item) for item in right_idx_str.split('|') if item]
        left_freq_list = [int(item) for item in left_idx_str.split('|') if item]
        
        prev_entropy = self.calc_words_entropy(left_freq_list)
        nrev_entropy = self.calc_words_entropy(right_freq_list)
        entropy = min([prev_entropy, nrev_entropy])
        return min([prev_entropy, nrev_entropy])
    
    # 计算词列表的熵
    def calc_words_entropy(self, freq_list):
        entropy = 0.0
        divider = sum(freq_list)
        for value in freq_list:
            entropy -= (value/divider)*math.log(value/divider)
        return entropy
    
    def process(self):
        print('finish making words')
        self.calc_base_property(4)
        print('finish calcing base property')
        self.calc_advanced_property()
        print('finish calcing advance property')
        self.summarize_mem_csmp()
        print('finish saving dictionary')
        # self.suspicious_stop_words()

if __name__ == '__main__':
    #with open('./sample.txt', 'r') as file:
    #    content = file.read()
    
    temp_db = CPrepDbHandle()
    word_tool = NewWordExtract()
    
    for offset in range(0,20):
        where = "Fjob_summary!='' limit 1000 offset %s"%(offset*1000)
        field_list = ['Fjob_summary']
        temp_db.set_db_table('db_job','t_zhilian_detail')
        results = temp_db.query(field_list, where)
        #contents = ['结衣我老婆，saber我老婆，两仪我老婆']
        contents = [result['Fjob_summary'] for result in results]
        
        word_tool.make_words(contents)
    word_tool.process()
    temp_db.destroy()