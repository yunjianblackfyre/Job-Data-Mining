#   AUTHOR: Sibyl System
#     DATE: 2018-02-11
#     DESC: Word-weight builder

'''
详细说明：
全量读取读取文档-关键词矩阵
1.将关键词同步到词数据表
2.将关键词对应文档的权重同步到词-文档权重数据表
'''

import json
import sys
import os
import numpy as np
from foundations.utils import *
from search.srch_db_handle import CSrchDbHandle

idf_value_array_file = '/home/caonimabi/develop/job_data_mining/preprocessors/numpy_array/idf_value_array.npy'
idf_wordidx_array_file = '/home/caonimabi/develop/job_data_mining/preprocessors/numpy_array/idf_wordidx_array.npy'
tfidf_value_array_file = '/home/caonimabi/develop/job_data_mining/preprocessors/numpy_array/tfidf_value_array.npy'
tfidf_wordidx_array_file = '/home/caonimabi/develop/job_data_mining/preprocessors/numpy_array/tfidf_wordidx_array.npy'
tfidf_Docidx_array_file = '/home/caonimabi/develop/job_data_mining/preprocessors/numpy_array/tfidf_Docidx_array.npy'
id2Word_file = '/home/caonimabi/develop/job_data_mining/preprocessors/mapping_dict/id2Word.txt'

class CWordWeightBuilder:
    def __init__(self):
        self._arr_tfidf = []
        self._arr_tfidf_wordidx = []
        self._arr_tfidf_Docidx = []
        self.id2Word = {}
        self.stop_watch = StopWatch()
        
    def _init_db(self):
        self._db = CSrchDbHandle()
    
    # 获取反词频词典
    @staticmethod
    def get_wordidf_info():
        arr_idf =         np.load(idf_value_array_file)
        arr_idf_wordidx = np.load(idf_wordidx_array_file)
        with open(id2Word_file,'r') as f:
            id2Word = json.loads(f.read())
        word_idf_info = {}
        
        for idx in range(len(arr_idf)):
            weight = arr_idf[idx]
            word_id = arr_idf_wordidx[idx]
            word = id2Word[str(word_id)]
            word_idf_info[word] = weight
        return word_idf_info
        
    def _load_word_info(self):
        self._arr_tfidf =         np.load(tfidf_value_array_file)
        self._arr_tfidf_wordidx = np.load(tfidf_wordidx_array_file)
        self._arr_tfidf_Docidx =  np.load(tfidf_Docidx_array_file)
        
        with open(id2Word_file,'r') as f:
            self.id2Word = json.loads(f.read())
            
        print(len(self._arr_tfidf))
        
    def _save_word_table(self):
        self._db.set_db_table('db_job','t_key_word')
        for word in self.id2Word.values():
            where_exist = "Fkey_word='%s' and Flstate=1"%(word)
            data = {
                'Fkey_word':word,
                'Flstate':1,
                'Fcreate_time':time_now(),
                'Fmodify_time':time_now()
            }
            if not self._db.query(['*'], where_exist):
                self._db.insert(data)
                self._db.commit()
                
    def _save_word_weight_table(self):
        self._db.set_db_table('db_job','t_word_weight')

        for idx in range(len(self._arr_tfidf)):
            weight = self._arr_tfidf[idx]
            word_id = self._arr_tfidf_wordidx[idx]
            Doc_id = self._arr_tfidf_Docidx[idx]
            word = self.id2Word[str(word_id)]
            
            weight = float(weight)
            Doc_id = int(Doc_id)
            
            where_exist = "Fword='%s' and Fdoc_id='%s' and Flstate=1"%(word, Doc_id)
            weight_id = self._db.query(['Fauto_id'], where_exist)
            if not weight_id:
                datai = {
                    'Fword':word,
                    'Fdoc_id':Doc_id,
                    'Fweight':weight,
                    'Flstate':1,
                    'Fcreate_time':time_now(),
                    'Fmodify_time':time_now()
                }
                self._db.insert(datai)
            else:
                weight_id = weight_id[0]['Fauto_id']
                where_update = "Fauto_id='%s'"%(weight_id)
                datau = {
                    'Fweight':weight,
                    'Fmodify_time':time_now()
                }
                self._db.update(datau,where_update)
            self._db.commit()
            
    def _save_word_weight_table_fast(self):
        self._db.set_db_table('db_job','t_word_weight')
        field_list = ['Fword','Fdoc_id','Fweight','Fcreate_time','Fmodify_time']
        data_list_limit = 100000
        data_list = []
        self.stop_watch.reset()
        len_arr_tfidf = len(self._arr_tfidf)
        
        for idx in range(len_arr_tfidf):
        
            weight = self._arr_tfidf[idx]
            word_id = self._arr_tfidf_wordidx[idx]
            Doc_id = self._arr_tfidf_Docidx[idx]
            
            word = self.id2Word[str(word_id)]
            Doc_id = int(Doc_id)
            weight = float(weight)
            create_time = time_now()
            update_time = time_now()
            
            element = str((word, Doc_id, weight, create_time, update_time))
            data_list.append(element)
            
            if ( idx%data_list_limit==0 and idx > 0 ) or idx >= len_arr_tfidf-1: 
                self._db.update_batch(field_list, data_list)
                self._db.commit()
                
                print('done loading %s rows, %s seconds passed'\
                      %(len(data_list), self.stop_watch.get_elapsed_seconds()))
                data_list = []
                      
            
    def _run(self):
        self._save_word_table()
        self._save_word_weight_table_fast()
        
    
    # 主过程
    def process(self):
        try:
            print('init db handler')
            self._init_db()
            print('load word info')
            self._load_word_info()
            print('run...')
            self._run()
        except:
            print(traceback.format_exc())
        

if __name__ == '__main__':
    #word_weight_builder = CWordWeightBuilder()
    #word_weight_builder.process()
    print_dict(CWordWeightBuilder.get_wordidf_info())
    
    
    
