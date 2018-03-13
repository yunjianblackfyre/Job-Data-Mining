#   AUTHOR: Sibyl System
#     DATE: 2018-03-06
#     DESC: wordvector clustering

'''
详细说明：
词向量聚类
    用kmeans尝试不同的聚类数目N
    并且在单次聚类中初始化M次
    找到最优的N，并且聚类结果
    提交给人工过滤作为最终结果
'''

import re
import math
import json
import sys
import os
import numpy as np
from foundations.utils import *
from gensim.models import Word2Vec
from sklearn.cluster import KMeans
from search.word_weight_builder import CWordWeightBuilder

test_data_path = './training_data/w2v_sentence.txt'
model_save_path = './model/w2v_model'

class MyKmeans():
    def __init__(self):
        self.word_cluster_dict={}
        self.vector_cluster_dict={}
        self.cluster_detail=[]
        
    def __reset__(self):
        self.word_cluster_dict={}
        self.vector_cluster_dict={}
        self.cluster_detail=[]
    
    # 按照离中心点的距离，聚类内容排序
    def _refine_clusters(self):
        wordidf_dict = CWordWeightBuilder.get_wordidf_info()
        for label in self.word_cluster_dict.keys():
            words = self.word_cluster_dict[label]
            vectors = np.array(self.vector_cluster_dict[label])
            centroid = sum(vectors)/len(vectors)
            distances = np.linalg.norm(vectors-centroid,axis=1)
            word_info_list = []
            for idx in range(len(words)):
                word_info_tuple = (
                    words[idx], 
                    distances[idx], 
                    wordidf_dict.get(words[idx],0.0)
                )
                word_info_list.append(word_info_tuple)
                
            # 可根据词向量离质心距离、IDF值进行排序
            word_info_list = sorted(word_info_list, key=lambda tup: tup[2],reverse=True)
            word_info_list = [word_info[0] for word_info in word_info_list]   # 外显时只展示部分结果
            self.cluster_detail.append((len(word_info_list), word_info_list))  #[0:100]
        self.cluster_detail = sorted(self.cluster_detail, key=lambda tup: tup[0])
    
    # 保存将机器最后的聚类结果
    def _save_clusters(self):
        print_list(self.cluster_detail,params={'newline':True})
            
    # 构造word2vector训练数据
    def _run(self):
        model = Word2Vec.load(model_save_path)
        word_list = []
        vector_list = []
        optimal_inertia = float('inf')
        optimal_kmeans = None
        optimal_clusters = 0
        for word in model.wv.index2word:
            word_list.append(word)
            vector_list.append(model.wv[word])
        Xvector = np.array(vector_list)
        
        # 从10-100聚类 比较质点距离
        for cluster_size in range(100,101):
            kmeans = KMeans(
                n_clusters=cluster_size, 
                init='k-means++',
                n_init=25,
                precompute_distances=True,
            ).fit(Xvector)
            print("error scale for %s clusters is %s"%(cluster_size, kmeans.inertia_))
            if kmeans.inertia_ < optimal_inertia:
                optimal_inertia = kmeans.inertia_
                optimal_kmeans = kmeans
                optimal_clusters = cluster_size
                
        print("optimal cluster size is %s with error scale %s"%(optimal_clusters, optimal_inertia))
        Yvectors = optimal_kmeans.labels_
        
        # 将聚类结果打包
        for idx in range(len(Yvectors)):
            label = Yvectors[idx]
            try:
                self.word_cluster_dict[label].append(word_list[idx])
                self.vector_cluster_dict[label].append(vector_list[idx])
            except:
                self.word_cluster_dict[label]=[word_list[idx]]
                self.vector_cluster_dict[label]=[vector_list[idx]]
                
        self._refine_clusters()
        self._save_clusters()
                
    # 总结内存消耗量
    def _summarize_mem_csmp(self):
        pass
    
    # 主过程
    def process(self):
        print('kmeans start clustering...')
        self._run()
        self.__reset__()
        

if __name__ == '__main__':
    #with open('./sample.txt', 'r') as file:
    #    content = file.read()
    kmeans = MyKmeans()
    kmeans.process()
    
    
    
