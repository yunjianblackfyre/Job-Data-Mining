#   AUTHOR: Sibyl System
#     DATE: 2018-03-03
#     DESC: word2vector encapsulation

'''
详细说明：
训练词向量
'''

import re
import math
import json
import sys
import os
from foundations.utils import *
from gensim.models import Word2Vec
from gensim.models.word2vec import LineSentence

test_data_path = './training_data/w2v_sentence.txt'
model_save_path = './model/w2v_model'

class MyWord2Vector():
    def __init__(self):
        self.training_data_file = test_data_path
        
    def __reset__(self):
        pass
        
    # 构造word2vector训练数据
    def _run(self):
        sentences = LineSentence(self.training_data_file)
        model = Word2Vec(sentences, size=10, window=6, min_count=1, workers=4,compute_loss=True)
        model.save(model_save_path)
        print(len(model.wv.index2word))
        '''
        for word in model.wv.index2word:
            word2vector_dict[word]=model.wv[word]
        '''
                
    # 总结内存消耗量
    def _summarize_mem_csmp(self):
        pass
    
    # 主过程
    def process(self):
        print('word2vector start training...')
        self._run()
        self.__reset__()
        

if __name__ == '__main__':
    #with open('./sample.txt', 'r') as file:
    #    content = file.read()
    word2vector = MyWord2Vector()
    word2vector.process()
    
    
    
