#   AUTHOR: Sibyl System
#     DATE: 2018-03-06
#     DESC: docvector clustering

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
from sklearn.cluster import KMeans
from preprocessors.prep_db_handle import CPrepDbHandle

# 初始化绘图库，禁用GUI
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

#全局变量
doc_hidden_info_path = '/home/caonimabi/develop/job_data_mining/clusters/models/doc_hidden_info.txt'

def save_figure(x,y):
    plt.figure()
    plt.plot(x,y)
    plt.savefig("./figures/cluster_loss.jpg")
    plt.close("all")
    

class CKmeansDocs():
    def __init__(self):
        self.doc_cluster_dict={}
        self.doc_hidden_info = {}
        self.vector_cluster_dict={}
        self.cluster_detail=[]
        
    def __reset__(self):
        self.doc_cluster_dict={}
        self.doc_hidden_info = {}
        self.vector_cluster_dict={}
        self.cluster_detail=[]
        
    def __prepare_doc_hidden_info(self):
        with open(doc_hidden_info_path) as f:
            self.doc_hidden_info = json.loads(f.read())
        
    # 按照离中心点的距离，聚类内容排序
    def _refine_clusters(self):
        for label in self.doc_cluster_dict.keys():
            docs = self.doc_cluster_dict[label]
            vectors = np.array(self.vector_cluster_dict[label])
            centroid = sum(vectors)/len(vectors)
            self.cluster_detail.append(centroid)
        
        
            distances = np.linalg.norm(vectors-centroid,axis=1)
            doc_info_list = []
            for idx in range(len(docs)):
                doc_info_tuple = (
                    docs[idx], 
                    distances[idx], 
                )
                doc_info_list.append(doc_info_tuple)
                
            # 可根据词向量离质心平均距离、平均IDF值进行排序
            doc_info_list = sorted(doc_info_list, key=lambda tup: tup[1],reverse=True)
            doc_info_list = [doc_info[0] for doc_info in doc_info_list]   # 外显时只展示部分结果
            # self.cluster_detail.append((str(centroid), len(doc_info_list), doc_info_list))  #[0:100]
            self.cluster_detail.append((len(doc_info_list), doc_info_list))  #[0:100]
            
        self.cluster_detail = sorted(self.cluster_detail, key=lambda tup: tup[0])
        
        
    def _multi_clustering(self):
        doc_list = []
        vector_list = []
        optimal_inertia = float('inf')
        optimal_kmeans = None
        optimal_clusters = 0
        
        cluster_size_axis = np.linspace( 10, 149, 140 ,dtype="float64")     # 10 到 149
        inertia_size_axis = np.zeros(140, dtype='float64')
        
        
        for doc_url, hidden_info in self.doc_hidden_info.items():
            
            vector_str =    hidden_info[0]      # hidden_info[0]字符串化的文档向量
            title =     hidden_info[1]      # hidden_info[1]文档标题
            tags_str =  hidden_info[2]      # hidden_info[2]字符串化的文档标签
            is_ready =  hidden_info[3]      # hidden_info[3]布尔，文档是否适合聚类
            
            doc_list.append(title)
            vector = np.array([float(elem) for elem in json.loads(vector_str)])
            if is_ready:
                vector_list.append(vector)
            
        Xvector = np.array(vector_list)
        print("There are %s total docs"%(len(doc_list)))
        
        # 从10-150聚类 比较质点距离
        for cluster_size in range(50,51):
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
                self.doc_cluster_dict[label].append(doc_list[idx])
                self.vector_cluster_dict[label].append(vector_list[idx])
            except:
                self.doc_cluster_dict[label]=[doc_list[idx]]
                self.vector_cluster_dict[label]=[vector_list[idx]]
    
    # 保存将机器最后的聚类结果
    def _save_clusters(self):
        print_list(self.cluster_detail,params={'newline':True})
        # np.save('./models/kmeans_topics',np.array(self.cluster_detail))
            
    # 构造word2vector训练数据
    def _run(self):
        self.__prepare_doc_hidden_info()
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
    kmeans = CKmeansDocs()
    kmeans.process()
    
    
    
