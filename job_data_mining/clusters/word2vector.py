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

training_data_path = '/home/caonimabi/develop/job_data_mining/preprocessors/training_data/w2v.txt'
model_save_path = '/home/caonimabi/develop/job_data_mining/clusters/models/w2v_model'

class MyWord2Vector():
    def __reset__(self):
        pass
        
    # 构造word2vector训练数据
    def run(self):
        sentences = LineSentence(training_data_path)
        model = Word2Vec(sentences, size=10, window=5, min_count=1, workers=4,compute_loss=True)
        print("Total loss:%s"%model.get_latest_training_loss())
        model.save(model_save_path)
        '''
        for word in model.wv.index2word:
            word2vector_dict[word]=model.wv[word]
        '''
    
    # 主过程
    def process(self):
        print('word2vector start training...')
        self._run()
        self.__reset__()
        

if __name__ == '__main__':
    word2vector = MyWord2Vector()
    word2vector.run()
    
    
    
