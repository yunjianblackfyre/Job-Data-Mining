#   AUTHOR: Sibyl System
#     DATE: 2018-01-03
#     DESC: new words extraction

'''
详细说明：
本新词提取算法来自于网文：
互联网时代的社会语言学：基于SNS的文本数据挖掘
链接：http://www.matrix67.com/blog/archives/5044
感谢UP主提供的简单而又强大的算法！
'''

import re
import math
import json
import sys
from foundations.utils import *
from preprocessors.prep_db_handle import CPrepDbHandle
from stop_words import STOP_WORDS,STOP_WORDS_ENG
from stop_words import STOP_PATTERNS
from full_stop_words import STOP_WORDS as FULL_STOP_WORDS

MAX_TOLERANCE = 5       # 新词最大长度
FREE_LVL_THRESH = 1.4   # 自由度阈值
SLD_LVL_THRESH = 40     # 凝固度阈值

class NewWordExtract:
    
    # 初始化
    def __init__(self,tolerance):
        self.tolerance = tolerance
        self.word2prob = {}     # 词概率
        self.word2entr_dict = {}  # 词索引表
        self.word2sld_lvl = {}  # 凝固度
        self.word2free_lvl = {} # 自由度
        self.words = []         # 词列表
        self.new_words = {}     # 新词列表
        self.new_words_eng = {}     # 新单词列表
        self.word2idf = {}    # 词所属文档数
        self.len_contents = 0
        self.len_words = 0
        self.stop_words = set(STOP_WORDS)
        self.stop_words_eng = set(STOP_WORDS_ENG)
        self.stop_word_pattern = STOP_PATTERNS
        self.full_stop_words = FULL_STOP_WORDS
        
    # 每次处理完一本书，重置
    def reset(self):
        self.word2prob = {}     # 词概率
        self.word2entr_dict = {}  # 词索引表
        self.word2sld_lvl = {}  # 凝固度
        self.word2free_lvl = {} # 自由度
        self.words = []         # 词列表
        self.new_words = {}     # 新词列表
        self.new_words_eng = {}     # 新单词列表
        self.word2idf = {}    # 词所属文档数
        self.len_contents = 0
        self.len_words = 0
    
    # 总结内存消耗量
    def summarize_mem_csmp(self):
        print('size of word2entr_dict:',sys.getsizeof(self.word2entr_dict)/(1024*1024),'MB')
        print('size of word2prob:',sys.getsizeof(self.word2prob)/(1024*1024),'MB')
        print('size of word2sld_lvl:',sys.getsizeof(self.word2sld_lvl)/(1024*1024),'MB')
        print('size of word2free_lvl:',sys.getsizeof(self.word2free_lvl)/(1024*1024),'MB')
        print('size of words:',sys.getsizeof(self.words)/(1024*1024),'MB')
    
    # 统计出可疑停用词，例如：智能（包含停用词“能”），大并发（包含停用词“并”）
    def suspicious_stop_words(self):
        single_stop_words = []
        suspicious_info_list = []
        for stop_word in self.full_stop_words:
            if len(stop_word) == 1:
                single_stop_words.append(stop_word)
                
        # 将停用字（例如：“的”，“使”）做成列表，将包含此词的高自由度词当做可疑停用词
        single_stop_words = set(single_stop_words)
        
        for free_word in self.word2free_lvl.keys():
            for sword in free_word:
                if sword in single_stop_words:
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
    
    # 单份招聘信息的预处理
    def content_preprocess(self,content):
        # 过滤标点符号
        content = re.sub('\W+',' ',content)
        
        # 若本文档为英文，则跳过
        eng_words = re.findall('[a-zA-Z]{2,}',content)
        none_eng_words = re.findall('[\u4e00-\u9fff]',content)
        eng_ratio = len(eng_words)/( len(none_eng_words)+0.001 )
        if eng_ratio >= 0.25:
            return ''
            
        # 提取英文单词
        for eng_word in eng_words:
            try:
                self.new_words_eng[eng_word]+=1
            except:
                self.new_words_eng[eng_word]=1
        
        # 正则处理停用词
        for pattern in self.stop_word_pattern:
            content = re.sub(pattern,'',content)
            
        # 替换停用词（垂直领域的写死逻辑）
        content = content.replace('智能','智慧')
        content = content.replace('个性','性格')
        content = content.replace('并发','霰发')
        content = content.replace('并行','霰行')
        
        # 去除停用词
        for stop_word in self.stop_words:
            content = content.replace(stop_word,'')
            
        return content
    
    # 创造新词列表
    def make_words(self,contents):
        tolerance = self.tolerance
        for content in contents:
            content = self.content_preprocess(content)
            if content:
                total_words = re.findall('[\u4e00-\u9fff]|[a-zA-Z]+|\s+',content)
                self.words.extend(total_words)
        
    # 计算新词基本属性：
    # 1.词概率
    # 2.左右邻词列表
    def calc_base_property( self ):
        tolerance = self.tolerance
        if tolerance > MAX_TOLERANCE or tolerance < 2:
            raise Exception(1,'tolerance exceded')
            
        # 初始化变量
        self.len_words = (len(self.words)-tolerance + 1)*tolerance
        self.len_contents = len(self.words)
            
        for idx in range(self.len_contents):
            #if idx%( int(self.len_contents/100) )==0:
            #    print('processing progress:%s'%(idx/(self.len_contents/100)) )
                
            for offset in range(0,tolerance):
                edge = idx+offset+1
                if edge > self.len_contents:
                    break
                
                # 提取候选词
                this_word = ''.join( self.words[idx:edge] )
                has_space = True if re.findall('\s+',this_word) else False
                is_chi = True if not re.findall('^[a-zA-Z]+$',this_word) and offset > 0 else False
                
                # 填装词->频率映射
                if this_word not in self.word2prob.keys():
                    self.word2prob[this_word] = 1/self.len_words
                else:
                    self.word2prob[this_word] += 1/self.len_words
                    
                # 若本词有空格，不予处理
                if has_space:
                    continue
                    
                # 填装词->左右邻词列表
                right_idx = idx-1
                left_idx = idx+offset+1
                
                '''
                左右邻词列表构造说明：
                每个词的左右邻词列表长度通常有几千以上，如果全由词典存储内存消耗十分巨大
                所以在存储时用字符串编码。需要操作时，则将字符串解码为列表。虽然编码与解码
                过程消耗时间，约之前的1.5倍，但是消耗的内存空间减少4倍，使得4GB内存
                虚拟机可以一次性处理4万份招聘信息，总文字量相当于2本《资本论》
                '''
                
                if this_word in self.word2entr_dict.keys() and is_chi:
                    left_word = self.words[right_idx].strip() if right_idx > -1 else ''
                    right_word = self.words[left_idx].strip() if left_idx < self.len_contents else ''

                    # 填装左邻词列表
                    if left_word:
                        left_word_tuple = self.word2entr_dict[this_word]['left_word']
                        left_word_list = [item for item in left_word_tuple[0].split('|') if item]
                        left_wordidx_list = [item for item in left_word_tuple[1].split('|') if item]
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
                        self.word2entr_dict[this_word]['left_word'] = (left_word_str, left_idx_str)
                        
                    # 填装右邻词列表
                    if right_word:
                        right_word_tuple = self.word2entr_dict[this_word]['right_word']
                        right_word_list = [item for item in right_word_tuple[0].split('|') if item]
                        right_wordidx_list = [item for item in right_word_tuple[1].split('|') if item]
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
                        self.word2entr_dict[this_word]['right_word'] = (right_word_str, right_idx_str)
                    
                elif is_chi:
                    left_word = self.words[right_idx].strip() if right_idx > -1 else ''
                    right_word = self.words[left_idx].strip() if left_idx < self.len_contents else ''

                    right_word_tuple = (right_word,'1') if right_word else ('','')
                    left_word_tuple = (left_word,'1') if  left_word else ('','')
                    self.word2entr_dict[this_word]={'right_word':right_word_tuple,'left_word':left_word_tuple}
    
    # 计算新词高级属性
    # 1.自由度
    # 2.凝固度
    def calc_advanced_property(self):
        for word in self.word2entr_dict.keys():
            sld_lvl = self.calc_word_sld_lvl(word)
            free_lvl = self.calc_word_free_lvl(word)
            
            if free_lvl > FREE_LVL_THRESH and sld_lvl > SLD_LVL_THRESH:
                self.word2sld_lvl[word] = sld_lvl      # 凝固度
                self.word2free_lvl[word] = free_lvl    # 自由度
                self.new_words[word] = int(self.word2prob[word]*self.len_words) # 新词与词频
                
        # word_free_list = sorted(self.word2free_lvl.items(), key=lambda d: d[1])
        # print_list(word_free_list)
    
    # 计算凝固度
    def calc_word_sld_lvl(self,word):
        if re.findall('^[a-zA-Z]+$',word):
            return 2*SLD_LVL_THRESH
            
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
        if re.findall('^[a-zA-Z]+$',word):
            return 2*FREE_LVL_THRESH
            
        right_word_tuple = self.word2entr_dict[word]['right_word']
        left_word_tuple = self.word2entr_dict[word]['left_word']
        right_freq_list = [int(item) for item in right_word_tuple[1].split('|') if item]
        left_freq_list = [int(item) for item in left_word_tuple[1].split('|') if item]
        
        prev_entropy = self.calc_words_entropy(left_freq_list)
        nrev_entropy = self.calc_words_entropy(right_freq_list)
        entropy = min([prev_entropy, nrev_entropy])
        return min([prev_entropy, nrev_entropy])
    
    # 计算左右邻词列表的熵
    def calc_words_entropy(self, freq_list):
        entropy = 0.0
        divider = sum(freq_list)
        for value in freq_list:
            entropy -= (value/divider)*math.log(value/divider)
        return entropy
    
    # 新词提取主过程
    def process(self):
        print('finish making words')
        self.calc_base_property()
        print('finish calcing base property')
        self.calc_advanced_property()
        print('finish calcing advance property')
        self.summarize_mem_csmp()
        print('finish saving dictionary')
        # self.suspicious_stop_words()

if __name__ == '__main__':

    temp_db = CPrepDbHandle()
    word_tool = NewWordExtract(tolerance=4)
    
    # 一次处理一本书
    chapters = 40       # 每本书章节数 
    books = 5           # 书本的数量
    chapter_size = 1000 # 每章节页数
    
    for book in range(books):
        for chapter in range(book*chapters, book*chapters + chapters):
            # print('book index:',book)
            # print('chapter_index:',chapter)
            print('page offset:',chapter*chapter_size)

            where = "Fjob_summary!='' order by Fauto_id limit %s offset %s"%(chapter_size, chapter*chapter_size)
            field_list = ['Fjob_summary']
            temp_db.set_db_table('db_job','t_zhilian_detail')
            results = temp_db.query(field_list, where)
            
            contents = [result['Fjob_summary'] for result in results]
            
            word_tool.make_words(contents)
        word_tool.process()
        
        # 写文档
        file_name = './new_words/new_words_%s.txt'%(book)
        with open(file_name, 'w') as f:
            f.write(json.dumps(word_tool.new_words))
            
        file_name = './new_words/new_words_eng_%s.txt'%(book)
        with open(file_name, 'w') as f:
            f.write(json.dumps(word_tool.new_words_eng))
            
        # 重置新词提取器
        word_tool.reset()
        
    temp_db.destroy()


'''
# 单次测试用
if __name__ == '__main__':
    #with open('./sample.txt', 'r') as file:
    #    content = file.read()
    
    #with open('./sample.txt', 'r') as file:
    #    content = file.read()
    
    temp_db = CPrepDbHandle()
    word_tool = NewWordExtract(tolerance=4)
    
    contents = ['最是人间留不住，朱颜辞镜花辞树']
    word_tool.make_words(contents)
    word_tool.process()
    with open('result.txt', 'w') as f:
        f.write(json.dumps(word_tool.new_words))
    word_tool.reset()
        
    temp_db.destroy()
'''