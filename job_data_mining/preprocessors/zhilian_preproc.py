#   AUTHOR: Sibyl System
#     DATE: 2018-01-03
#     DESC: csdn文章预处理

'''
csdn资讯预处理程序
预处理结果分为以下几类

1.处理成功，无缺陷
2.处理成功，有缺陷
3.处理失败，有异常

缺陷和异常分为以下两种方式记录
1.单次记录，作为log输出
2.多次记录，作为statistic输出

预处理结果目前写日志文件
后续考虑替换为数据库
因为对预处理结果的观察学习
有助于后续预处理程序的优化
以及对于源数据的认知
'''

# import ssl
# import requests
# import urllib.request
# from urllib.request import Request

import os
import re
import numpy as np
import time
import matplotlib.image as mpimg
import jieba
import jieba.posseg as pseg

from foundations.log import CLog
from config.inits import LOG_CFG
from numpy import linalg as LA
from gensim.models import Word2Vec
from clusters.word2vector import model_save_path
from preprocessors.full_stop_words import STOP_WORDS_ENG, STOP_WORDS
from preprocessors.zhilian_allowed_words import ZHILIAN_ALLOWED_WORDS
from preprocessors.batch_proc import *
from preprocessors.error import ErrCode
from scrapy.selector import Selector
from lxml import etree
from queue import Queue

topic_vector_path = "/home/caonimabi/develop/job_data_mining/clusters/models/kmeans_topics.npy"
min_image_area = 10000
summary_thresh = 15
LWORDS_THRESH = 0.7     # 有时候关键词是新词，不一定能够查询到相应的word_detail，所以这种词数量占了30%以上，就要做相应的容错
TAG_NUM_THRESH = 3

mark_tag_set = set(['n', 'nz', 'vn','eng'])

pattern_dict = {
    ("<\s*","\s+[^<>]*>"):"\n",
    ("<",">"):"\n",
}

# 下列都是有换行效果的html标签
pattern_list = [
    "br",
    "div",
    "p",
    "ul",
    "ol",
    "li",
    "h[1-6]",
    "table",
    "menu",
    "hr",
    "form"
]

def renew_jieba():
    with open("./new_words/filtered_new_words.txt", 'r') as f:
        filtered_new_words_dict = json.loads(f.read())
    
    # 将文件写成jieba可读的形式
    # 例如 机器学习 nv 612
    # 标注 词  词性（这里n是名词，v是动词） 词频
    file_name = './new_words/new_words4jieba.txt'
    with open(file_name, 'w') as f:
        for key, value in filtered_new_words_dict.items():
            line = '%s %s vn\n'%( key, str(value) ) # 按照ICTPOS标记法，将所有新词标记为动名词
            f.write(line)
            
    # 更新结巴分词器
    file_name = './new_words/new_words4jieba.txt'
    jieba.load_userdict(file_name)

def clean_html(content):
    content = html_unescape(content)
    for key in pattern_list:
        for key_type in pattern_dict.keys():
            pattern = key_type[0]+key+key_type[1]
            sub_str = pattern_dict[key_type]
            content = re.sub(pattern,sub_str,content)
    content = re.sub('<[^<>]+>','',content)
    return content
    
def extract_zhilian_detail(content):
    content = clean_html(content)
    target_list = []
    count = 0
    for line in content.split('\n'):
        line = line.strip()
        if line:
            patterns = re.findall("^[\(（【\[]?\s?\d.+",line.strip())
            if patterns:
                count += 1
                target_list.append( patterns[0] )
    if count > 1:
        return ' '.join(target_list)
    else:
        return ''
        
def extract_keyword(keyword_list, line):
    line = line.strip()
    if line:
        words_info = list(pseg.cut(line))
        for word, flag in words_info:
            if flag in mark_tag_set and len(word) > 1: # 一个字的不要
                if flag == "eng":
                    if word not in STOP_WORDS_ENG:
                        keyword_list.append(word.upper())  # 英文统一转为大写
                elif (word not in STOP_WORDS) and (word in ZHILIAN_ALLOWED_WORDS):
                    keyword_list.append(word)

class ZhilianPreproc(BatchProc):

    def __init__( self ):
        super(ZhilianPreproc, self).__init__("zhilian_preproc",3)
        self.word_detail = {}
        self.topic_vectors = np.load(topic_vector_path)
            
    def prepare_word_detail(self):
        self._db.set_db_table("db_hiddens","t_word_detail")
        where = "1"
        field_list = ["count(Fauto_id) as Fcount"]
        count = self._db.query(field_list, where)
        self._db.commit()
        count = count[0]["Fcount"]
        if count > 500000:      # 大于50W就报错
            raise Exception
        else:
            self.logger.log_info("There are %s words detail"%(count))
            
        field_list = ["Fword","Fword_idf","Fword_vector"]
        DB_res = self._db.query(field_list, where)
        self._db.commit()
        
        for item in DB_res:
            word = item["Fword"]
            idf = item["Fword_idf"]
            vector = np.array([float(elem) for elem in json.loads(item["Fword_vector"])])
            self.word_detail[word] = (idf,vector)
        self.logger.log_info("word detail preparation complete")
    

        
    def __gen_words(self, item):
        content_keyword_len = 0
        content_keyword_list = []
        content_keyword_dict = {}
        
        # 分词
        content = extract_zhilian_detail(item["Fcontent"])
        
        eng_words = re.findall('[a-zA-Z]{2,}',content)
        none_eng_words = re.findall('[\u4e00-\u9fff]',content)
        eng_ratio = len(eng_words)/( len(none_eng_words)+0.001 )
        if eng_ratio >= 0.5:
            self.logger.log_info("item with id %s,origin url %s, has too many english words"
                %(item['Fauto_id'], item['Fjob_url']))
            raise Exception
            
        content = re.sub("\s+"," ",content)
        extract_keyword(content_keyword_list, content)
        
        # 过滤词
        content_keyword_list = filter_words(content_keyword_list,freq_thresh=0,len_thresh=15)
        content_keyword_len = len(content_keyword_list)
        
        if content_keyword_len<=TAG_NUM_THRESH:
            self.logger.log_info("item with id %s,origin url %s, has empty content"
                %(item['Fauto_id'], item['Fh5_url']))
            raise Exception
        
        # 计算TF值
        for word in content_keyword_list:
            # content_keyword_dict[word] = 1/content_keyword_len
            map_reduce(content_keyword_dict,word,1/content_keyword_len)
        
        # 结果打包
        self.firelinker["Ftags"] = content_keyword_dict
        self.firelinker["Fcontent"] = clean_html(item["Fcontent"])
        
        '''
        for word in title_keyword:
            map_reduce(title_keyword_dict,word,1)
        self.firelinker["Ftitle_tags"] = title_keyword_dict
        '''
        
    def __compute_docvector(self, item):
        content_keyword_dict = self.firelinker["Ftags"]
        if not content_keyword_dict.keys():
            self.abyss["URdead"]+=1
            raise Exception(ErrCode.ERR_TAG_EXTRACT_FAILED.value, "No tag found in this document")
        
        # 初始化变量
        doc_vector = np.array([0])
        rec_valid = 0   # 推荐可靠度
        analysis = []
        
        # 计算文章向量
        for word in content_keyword_dict.keys():
            word_info = self.word_detail.get(word)
            if word_info:
                rec_valid += 1
                tfidf = word_info[0]*content_keyword_dict[word]
                analysis.append((word,tfidf,word_info[0],content_keyword_dict[word]))
                vector = word_info[1]
                vector = vector/LA.norm(vector)     # 向量归一化处理
                if doc_vector.any():
                    doc_vector += vector*tfidf
                else:
                    doc_vector = vector*tfidf
                    
        rec_valid = rec_valid/len(content_keyword_dict.keys())
        
        # 打印分析结果
        # print("Sort by TFIDF")
        # print_list( sorted(analysis, key=lambda tup: tup[1], reverse=True) )
        analysis = [tag_detail[0] for tag_detail in sorted(analysis, key=lambda tup: tup[1], reverse=True)]
        
        # 归类主题
        max_simm = -1
        selected_topic = 0
        for idx in range(len(self.topic_vectors)):
            dot_product = np.dot(doc_vector, self.topic_vectors[idx])
            norm_product = LA.norm(doc_vector)*LA.norm(self.topic_vectors[idx])
            simm = (dot_product/norm_product)
            if simm > max_simm:
                max_simm = simm
                selected_topic = idx
        
        
        # 结果打包
        self.firelinker["Fcluster_id"] = selected_topic
        self.firelinker["Ftag_detail"] = ','.join(analysis)# json.dumps(analysis)
        self.firelinker["Farticle_vector"] = json.dumps([str(num) for num in list(doc_vector)])
        self.firelinker["Fdoc_ready"]=True if rec_valid >= LWORDS_THRESH else False
        
    # 更新或者插入t_csdn_article表
    def __update_article(self, item):
        self._db.set_db_table("db_documents","t_job_documents")
        where = "Fh5_url='%s'"%(item['Fh5_url'])
        if self._db.query(["Fauto_id"],where):
            datau = {
                'Flstate':      0,
                'Fsummary':     self.firelinker["Fcontent"],
                'Fmodify_time': time_now()
            }
            self._db.update(datau, where)
        else:
            datai = {
                
                'Fh5_url':      item['Fh5_url'],
                'Ftitle':       item['Ftitle'],
                'Fsummary':     self.firelinker["Fcontent"],
                'Flstate':      0,
                'Fmodify_time': time_now(),
                'Fcreate_time': time_now()
            }
            self._db.insert(datai)
            
    def __update_article_hidden(self, item):
        self._db.set_db_table("db_hiddens","t_job_documents_hidden")
        where = "Fh5_url='%s'"%(item['Fh5_url'])
        if self._db.query(["Fauto_id"],where):
            datau = {
                'Fcluster_id':      self.firelinker["Fcluster_id"],
                'Farticle_vector':  self.firelinker["Farticle_vector"],
                'Ftag_detail':      self.firelinker["Ftag_detail"],
                'Frec_state':   1 if self.firelinker['Fdoc_ready'] else 0,
                'Fmodify_time':     time_now()
            }
            self._db.update(datau, where)
        else:
            datai = {
                'Fcluster_id':      self.firelinker["Fcluster_id"],
                'Farticle_vector':  self.firelinker["Farticle_vector"],
                'Ftag_detail':      self.firelinker["Ftag_detail"],
                'Frec_state':   1 if self.firelinker['Fdoc_ready'] else 0,
                'Fh5_url':          item['Fh5_url'],
                'Fmodify_time':     time_now(),
                'Fcreate_time':     time_now()
            }
            self._db.insert(datai)
            
    def mark_result(self, item):
        # mark t_job_documents的时候，注意下面的mark码
        # 0-初始态 1-图片下载开始 2-图片下载完成 3-预处理成功 4-预处理失败
        if self.firelinker["result"]=="URdead":
            lstate=4    # 预处理失败
        else:
            lstate=3    # 预处理成功
            
        self._db.set_db_table('db_documents','t_job_documents')
        where = "Fauto_id='%s'"%(item["Fauto_id"])
        datau = {
            "Flstate":          lstate,
            "Fmodify_time":     time_now()
        }
        self._db.update(datau,where)
    
    # 将每次处理结果讯息打印日志
    def gen_single_report(self,item):
        content_id = item['Fauto_id']
        origin_url = item['Fh5_url']
        title =      item['Ftitle']
        result = self.firelinker["result"]
        print("item with id %s,title %s, origin url %s, result:%s"
              %(content_id, title, origin_url, result))
    
    # 将每批处理结果讯息打印日志
    def gen_batch_report(self):
        UPlay       = self.abyss["UPlay"]
        UPoison     = self.abyss["UPoison"]
        URdead      = self.abyss["URdead"]
        Usurvive    = self.abyss["Usurvive"]
        
        self.logger.log_info("You played %s times, survive %s times, \
        poisoned %s times, died %s times.\n \
               survival rate: %s, poison rate: %s, death rate: %s."\
              %(UPlay, Usurvive, UPoison, URdead, \
                Usurvive/(UPlay), UPoison/UPlay, URdead/UPlay))
        
    def process_doc(self,item):
        try:
            self.__gen_words(item)
            self.__compute_docvector(item)  # 依赖于__gen_words
            
            self.__update_article(item)
            self.__update_article_hidden(item)
        except Exception as e:
            self._failsafe(e, item)
        finally:
            # self.mark_result(item)
            self.gen_single_report(item)
            self._bonfire()
    
    def run(self):
        
        try:
            self.prepare_word_detail()
        except:
            self.logger.log_info(traceback.format_exc())
            return
        
        step = 50000
        start = 0
        offset = 10000
        end = start + offset
        
        while(True):
            where = "Fauto_id between %s and %s"%(start, end)
            # where = "Fauto_id between 0 and 50000"       #t_job_documents已经完成图片下载
            field_list = ["Fauto_id","Fjob_name as Ftitle","Fjob_summary as Fcontent","Fjob_url as Fh5_url"]
            self._db.set_db_table('db_crawlers','t_zhilian_detail')
            items = self._db.query(field_list, where)
            self._db.commit()
            if not items:
                break
            for item in items:
                self.process_doc(item)

            self.gen_batch_report()
            self._reset_monitor()
            
            start += step
            end = start + offset
            # break

# 单次测试用
if __name__ == '__main__':
    tool = ZhilianPreproc()
    tool.main()
    