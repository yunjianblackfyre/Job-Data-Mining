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
from preprocessors.prep_db_handle import CPrepDbHandle
from preprocessors.zhilian_stop_words import ZHILIAN_STOP_WORDS

# 初始化绘图库，禁用GUI
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

#全局变量
IDF_CEILING = 20
IDF_FLOOR = 0
model_save_path = '/home/caonimabi/develop/job_data_mining/clusters/models/w2v_model'

def save_figure(x,y):
    plt.figure()
    plt.plot(x,y)
    plt.savefig("./figures/cluster_loss.jpg")
    plt.close("all")
    

class CKmeansWords():
    def __init__(self):
        self.allowed_words = set([])
        self.word_cluster_dict={}
        self.vector_cluster_dict={}
        self.centroids = []
        self.cluster_detail=[]
        
    def __reset__(self):
        self.allowed_words = set([])
        self.word_cluster_dict={}
        self.vector_cluster_dict={}
        self.centroids = []
        self.cluster_detail=[]
        
    def _load_allowed_words(self):
        temp_db = CPrepDbHandle()
        temp_db.set_db_table("db_hiddens","t_word_detail")
        where = "Fword_idf >'%s' and Fword_idf <'%s'"%(IDF_FLOOR, IDF_CEILING)
        field_list = ["Fword"]
        words_info = temp_db.query(field_list, where)
        temp_db.commit()
        temp_db.destroy()
        self.allowed_words = set([word_info["Fword"] for word_info in words_info])
    
    # 按照离中心点的距离，聚类内容排序
    def _refine_clusters(self):
        for label in self.word_cluster_dict.keys():
            words = self.word_cluster_dict[label]
            vectors = np.array(self.vector_cluster_dict[label])
            centroid = sum(vectors)/len(vectors)
            self.centroids.append(centroid)
        
            distances = np.linalg.norm(vectors-centroid,axis=1)
            word_info_list = []
            for idx in range(len(words)):
                word_info_tuple = (
                    words[idx], 
                    distances[idx], 
                )
                word_info_list.append(word_info_tuple)
                
            # 可根据词向量离质心平均距离、平均IDF值进行排序
            word_info_list = sorted(word_info_list, key=lambda tup: tup[1],reverse=True)
            word_info_list = [word_info[0] for word_info in word_info_list]   # 外显时只展示部分结果
            self.cluster_detail.append((label, word_info_list))  #[0:100]
            
        self.cluster_detail = sorted(self.cluster_detail, key=lambda tup: tup[0])
        
        
    def _multi_clustering(self):
        model = Word2Vec.load(model_save_path)
        word_list = []
        vector_list = []
        optimal_inertia = float('inf')
        optimal_kmeans = None
        optimal_clusters = 0
        
        cluster_size_axis = np.linspace( 10, 149, 140 ,dtype="float64")     # 10 到 149
        inertia_size_axis = np.zeros(140, dtype='float64')
        
        
        for word in model.wv.index2word:
            if (word in self.allowed_words) and (word not in ZHILIAN_STOP_WORDS):
                word_list.append(word)
                vector_list.append(model.wv[word])
        Xvector = np.array(vector_list)
        print("There are %s total words"%(len(word_list)))
        
        # 从10-150聚类 比较质点距离
        for cluster_size in range(40,41):
            kmeans = KMeans(
                n_clusters=cluster_size, 
                init='k-means++',
                n_init=25,
                precompute_distances=True,
            ).fit(Xvector)
            inertia_size_axis[cluster_size-10] = kmeans.inertia_
            save_figure(cluster_size_axis, inertia_size_axis)
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
    
    # 保存将机器最后的聚类结果
    def _save_clusters(self):
        print_list(self.cluster_detail,params={'newline':True})
        np.save('./models/kmeans_topics',np.array(self.centroids))
            
    # 构造word2vector训练数据
    def _run(self):
        self._load_allowed_words()
        self._multi_clustering()
        self._refine_clusters()
        self._save_clusters()
    
    # 主过程
    def process(self):
        print('kmeans start clustering...')
        self._run()
        self.__reset__()
        

if __name__ == '__main__':
    #with open('./sample.txt', 'r') as file:
    #    content = file.read()
    kmeans = CKmeansWords()
    kmeans.process()
    
    
    
