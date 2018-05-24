#   AUTHOR: Sibyl System
#     DATE: 2018-05-02
#     DESC: generate recommender list

'''
生成用户推荐单
读取用户历史行为，将用户分到以下三个类中
1.重度用户
2.轻度用户
3.一般用户
重度用户属于对某一类文章有较强依赖的用户，
推荐器需要分类器提供用户喜好的文章类列表，最近消费的文章列表
产出推荐单：类文章 相似文章 其他文章 按照火热程度从上到下排序

轻度用户只消费了某几篇文章，暂时没有对某一类文章表示出喜爱
推荐器需要分类器提供用户最近消费的文章列表
产出推荐单：相似文章 其他文章 按照火热程度从上到下排序

一般用户还没有产生明显的行为数据
产出推荐单：当下比较火热的文章，火热程度从上到下进行排序

用户历史应当以下列数据格式为准
{
    时间表                   文章ID     文章类ID        文章向量               行为级别(预留字段)
    obj(2018-05-13):          (11,        70          '["0.1","-0.2","0.3"]'         1)
    obj(2018-05-13):          (12,        15          '["0.2","-0.2","0.4"]'         2)
    obj(2018-05-13):          (13,        60          '["0.1","-0.5","0.1"]'         3)
    obj(2018-05-13):          (09,        55          '["0.9","-0.2","0.7"]'         1)
    obj(2018-05-13):          (07,        50          '["0.3","-0.4","0.3"]'         3)
}

'''

# import ssl
# import requests
# import urllib.request
# from urllib.request import Request

import time
import random
import numpy as np
from numpy import linalg as LA
from foundations.utils import *
from foundations.log import CLog
from config.inits import LOG_CFG
from preprocessors.batch_proc import *
from preprocessors.error import ErrCode
from datetime import timedelta
from confluent_kafka import Consumer, KafkaError,TopicPartition

topic_vector_path =     "/home/caonimabi/develop/job_data_mining/clusters/models/kmeans_topics.npy"
ARTICLE_COVER =         120          # 文章时间覆盖，目前以天为单位
USER_HISTORY_COVER =    90         # 用户历史覆盖，目前以天为单位
FAVORED_THRESH =        5          # 在阅览了同类文章N篇后，判定用户喜欢此类文章
SIMM_THRESH =           0.9         # 相似度阈值

# 假定article_list是一个list of tuples
def intercept_article_list(article_list,intercept_length,article_id_set):
    # 文章列表没有充足的元素，直接返回
    article_list = [article_info for article_info in article_list if article_info[0] not in article_id_set]
    if len(article_list) <= intercept_length:
        article_id_list = [article_info[0] for article_info in article_list]
        
        article_id_set.update(article_id_list)
        article_list = sorted(article_list, key=lambda tup: tup[1], reverse=True)
        return article_list, article_id_set
    
    idx_list = random.sample(range(len(article_list)),intercept_length)
    article_id_list = [article_list[idx][0] for idx in idx_list]
    article_list = [article_list[idx] for idx in idx_list]
    article_list = sorted(article_list, key=lambda tup: tup[1], reverse=True)
    article_id_set.update(article_id_list)
    return article_list, article_id_set

class CRecommender(BatchProc):

    def __init__( self,batch_size,proc_id, proc_num ):
        super(CRecommender, self).__init__("recommender",4)
        self.firelinker = {     # 当前函数为下一个函数提供的数据
            "result":"Usurvive"  # 初始化为“成功”
        }    
        self.abyss = {          # 异常、缺陷信息统计器
            "Usurvive":0,
            "URdead":0,
            "UPoison":0,
            "UPlay":0
        }
        self.batch_size = batch_size
        self.proc_id    = proc_id
        self.proc_num   = proc_num
        
        self.latest_articles = {}
        self.earliest_user_log = ""
        self.kafka_consumer = None
        self.user_history = {}      # 用户ID作为key,用户历史列表作为value
        self.user_recommend = {}
        self.topic_vectors = np.load(topic_vector_path)
        
    def init_kafka_consumer(self,items):
        for item in items:
            self.user_history[item["Fuser_id"]]=[]
            
        self.kafka_consumer = Consumer({
            'bootstrap.servers': 'localhost',
            'group.id': 'mygroup',
            'default.topic.config': {
            'auto.offset.reset': 'largest'
            }
        })
        self.kafka_consumer.subscribe(list(self.user_history.keys()))
        self.kafka_consumer.poll(timeout=1.0)
        
    def __reset_monitor(self):
        self.firelinker = {     # 当前函数为下一个函数提供的数据
            "result":"Usurvive"  # 初始化为“成功”
        }    
        self.abyss = {          # 异常、缺陷信息统计器
            "Usurvive":0,
            "URdead":0,
            "UPoison":0,
            "UPlay":0
        }
        self.kafka_consumer.close()
        self.kafka_consumer = None
        self.user_history = {}
        self.user_recommend = {}
        
    def __bonfire(self):
        result = self.firelinker["result"]
        self.abyss[result]+=1
        self.abyss["UPlay"]+=1
        self.firelinker = {
            "result":"Usurvive"
        }
        
    def __failsafe(self):
        self._db.rollback()
        self.firelinker["result"] = "URdead"
        self.logger.log_info(traceback.format_exc())
            
    # 将每次处理结果讯息打印日志
    def gen_single_report(self,item):
        content_id = item['Fauto_id']
        origin_url = item['Fh5_url']
        result = self.firelinker["result"]
        self.logger.log_info("item with id %s,origin url %s, result:%s"
              %(content_id, origin_url, result))
    
    # 将每批处理结果讯息打印日志
    def gen_batch_report(self):
        UPlay       = self.abyss["UPlay"]
        UPoison     = self.abyss["UPoison"]
        URdead      = self.abyss["URdead"]
        Usurvive    = self.abyss["Usurvive"]
        
        if UPlay!=0:
            self.logger.log_info("You played %s times, survive %s times, \
            poisoned %s times, died %s times.\n \
                survival rate: %s, poison rate: %s, death rate: %s."\
                %(UPlay, Usurvive, UPoison, URdead, \
                    Usurvive/(UPlay), UPoison/UPlay, URdead/UPlay))
        else:
            self.logger.log_info("You processed zero content, please check your Sql")
            
    def load_users_log(self,items):
        for item in items:
            try:
                user_number = item["Fuser_id"]
                self.kafka_consumer.seek(TopicPartition(str(user_number), 0, 0))     # 分区为0，OFFSET为0
                while True:
                    article_id_set = set()
                    msg = self.kafka_consumer.poll(timeout=1.0)
                    if msg is None:
                        break
                    elif msg.error():
                        self.logger.log_info(msg.error())
                        break
                    else:
                        # 加入过滤的逻辑
                        history_dict = json.loads(msg.value().decode())
                        action_date = datetime.strptime(history_dict["action_date"], "%Y-%m-%d %H:%M:%S")
                        if action_date > self.earliest_user_log:
                            article_id = history_dict["article_id"]
                            if article_id not in article_id_set:
                                # 后面两个None分别是article_cluster_id, article_vector
                                history_tuple = (action_date, article_id)
                                self.user_history[user_number].append(history_tuple)
                                article_id_set.add(article_id)
                        else:
                            break
            except Exception as e:
                self.logger.log_error(str(e))
    
    def load_articles_hidden(self):     # 注意，这里可能会抛出文章隐藏信息找不到的异常
        article_id_set = set()
        for user_log in self.user_history.values():
            article_id_set.update([log_item[1] for log_item in user_log])      # log_item[1]指向是文章ID
        
        if len(article_id_set)>1:
            id_range_str = format(tuple(article_id_set))
            where = "Fauto_id in %s"%( id_range_str )
        elif len(article_id_set)==1:
            id_str = list(article_id_set)[0]
            where = "Fauto_id = %s"%(id_str)
        else:
            return
        
        field_list = ["Fauto_id","Fcluster_id","Farticle_vector"]
        self._db.set_db_table("db_hiddens","t_job_documents_hidden")
        DB_res = self._db.query(field_list, where)
        article_info_tmp = {}
        for res in DB_res:
            article_id =            res["Fauto_id"]
            article_cluster_id =    res["Fcluster_id"]
            article_vector =        res["Farticle_vector"]
            article_info_tmp[article_id] = (article_cluster_id, article_vector)
        
        for user_id, history_tuple_list in self.user_history.items():
            for idx in range(len(history_tuple_list)):
                article_time =          history_tuple_list[idx][0]
                article_id =            history_tuple_list[idx][1]
                article_id =            int(article_id)
                article_cluster_id =    article_info_tmp[article_id][0]
                article_vector =        article_info_tmp[article_id][1]
                new_history_tuple = (
                    article_time,
                    article_id,
                    article_cluster_id,
                    article_vector
                )
                self.user_history[user_id][idx] = new_history_tuple
        
    def classify_user(self,history):
        cluster_dict = {}
        self.firelinker["favored_clusters"] = []
        self.firelinker["favored_articles"] = [] # 形如[(1, 20180516),(2,20190618)]
        for action in history:
            action_date =           action[0]
            article_id =            action[1]
            article_cluster_id =    action[2]
            article_vector =        np.array([float(elem) for elem in json.loads(action[3])])
            self.firelinker["favored_articles"].append((article_id,article_cluster_id, article_vector, action_date))
            map_reduce(cluster_dict,article_cluster_id)
            
        for key,value in cluster_dict.items():
            if value >= FAVORED_THRESH:
                self.firelinker["favored_clusters"].append(key)
        
    def gen_simm_article(self):
        raw_result = {}
        for article_info in self.firelinker["favored_articles"]:
            article_id =            article_info[0]
            article_cluster_id =    article_info[1]
            article_vector =        article_info[2]
            action_date =           article_info[3]
            article_comp_list =     self.latest_articles.get(article_cluster_id,[])
            article_candidates =    []
            
            for article_comp in article_comp_list:
                article_comp_id =       article_comp[0]
                article_comp_time =     article_comp[1]
                article_comp_vector =   article_comp[2]
                
                if article_id != article_comp_id:
                    dot_product = np.dot(article_vector, article_comp_vector)
                    norm_product = LA.norm(article_vector)*LA.norm(article_comp_vector)
                    simm = (dot_product/norm_product)
                    if simm > SIMM_THRESH:
                        article_candidates.append((article_comp_id,article_comp_time))
            raw_result[article_id] = article_candidates
        self.firelinker["simm_articles"] = raw_result
    
    def gen_cluster_article(self):
        raw_result = {}
        for cluster_id in self.firelinker["favored_clusters"]:
            raw_result[cluster_id] = [(article_info[0], article_info[1]) for article_info in self.latest_articles[cluster_id]]
        self.firelinker["cluster_articles"] = raw_result
    
    def gen_other_article(self):
        raw_result = {}
        for cluster_id in self.latest_articles.keys():
            article_info_list = self.latest_articles[cluster_id]
            raw_result[cluster_id] = [(article_info[0], article_info[1]) for article_info in article_info_list]      # 每个类取10篇文章
        self.firelinker["other_articles"] = raw_result
        
    def gen_random_article(self):
        simm_articles =         self.firelinker["simm_articles"]
        cluster_articles =      self.firelinker["cluster_articles"]
        other_articles =        self.firelinker["other_articles"]
        
        other_articles_new = {}
        article_id_set = set([])
        for article_id, article_list in simm_articles.items():
            simm_articles[article_id],article_id_set =          intercept_article_list(article_list,3,article_id_set)
            
        for cluster_id, article_list in cluster_articles.items():
            cluster_articles[cluster_id],article_id_set =       intercept_article_list(article_list,4,article_id_set)
            
        if len(other_articles.keys())>10:
            cluster_id_list = random.sample(other_articles.keys(),10)
        else:
            cluster_id_list = list(other_articles.keys())
        for cluster_id in cluster_id_list:
            other_articles_new[cluster_id],article_id_set =     intercept_article_list(other_articles[cluster_id],2,article_id_set)
            
        self.firelinker["other_articles"] = other_articles_new
        
    def gen_result(self,user_id):
        temp_dict = {}
        simm_articles =         self.firelinker["simm_articles"]
        cluster_articles =      self.firelinker["cluster_articles"]
        other_articles =        self.firelinker["other_articles"]
        
        article_id_list = []
        for key,value in simm_articles.items():
            article_id_list.append(key)
            for article in value:
                article_id_list.append(article[0])
        for value in cluster_articles.values():
            for article in value:
                article_id_list.append(article[0])
        for value in other_articles.values():
            for article in value:
                article_id_list.append(article[0])
        article_id_list = list(set(article_id_list))
        
        self.user_recommend[user_id] = ','.join([str(article_id) for article_id in article_id_list])
        
        # 用于演示，发布时记删
        in_string=format(tuple(article_id_list))
        self._db.set_db_table("db_documents","t_job_documents")
        where = "Fauto_id in %s"%(in_string)
        field_list = ["Fauto_id","Ftitle","Fh5_url","Fsummary"]
        DB_res = self._db.query(field_list, where)
        self._db.commit()
        
        for res in DB_res:
            temp_dict[res["Fauto_id"]] = res["Ftitle"]
        
        show_dict = {}
        for docid, value in simm_articles.items():
            new_key = temp_dict[docid]
            print("--------------------------------")
            print("用户投递了职位：%s"%(new_key))
            for article in value:
                new_value = temp_dict[article[0]]
                print("用户被推荐了职位：%s"%(new_value))
                
        for cluster_id, value in cluster_articles.items():
            print("--------------------------------")
            print("根据用户对类%s的喜爱，我们推荐了下列职位"%(cluster_id))
            for article in value:
                new_value = temp_dict[article[0]]
                print("%s"%(new_value))
        
        '''
        print("--------------------------------")
        print("给用户推荐的其他领域的文章")
        for value in other_articles.values():
            for article in value:
                new_value = temp_dict[article[0]]
                print("%s"%(new_value))
        '''
    
    def process_user(self,user_id, history):
        try:
            self.classify_user(history)
            self.gen_simm_article()
            self.gen_cluster_article()
            self.gen_other_article()
            self.gen_random_article()
            self.gen_result(user_id)
        except Exception as e:
            self.__failsafe()
        finally:
            # self.gen_single_report(item)
            self.__bonfire()
            
    def update_user_recmmend(self):
        self._db.set_db_table('db_users','t_user_recommends')
        field_list = ['Fuser_id','Frec_articles','Fmodify_time']
        data_list = []
        for user_id, recommends in self.user_recommend.items():
            modify_time = time_now()
            element = str((user_id, recommends, modify_time))
            data_list.append(element)
        
        self._db.update_batch(field_list, data_list)
        self._db.commit()
        
    def run(self, items):
        try:
            self.init_kafka_consumer(items)
            self.load_users_log(items)
            self.load_articles_hidden()
            for user_id, history in self.user_history.items():
                self.process_user(user_id, history)
            self.update_user_recmmend()
        except Exception as e:
            self.logger.log_error(traceback.format_exc())
        finally:
            self.__reset_monitor()
    
    # 读取最近的文章
    def prepare_articles(self):
        now = datetime.now()
        latest = now + timedelta(days=32-now.day)
        time_cover = timedelta(days=ARTICLE_COVER)
        earliest = latest - time_cover
        self._db.set_db_table("db_hiddens","t_job_documents_hidden")
        where = "Fcreate_time > '%s' and Fcreate_time < '%s' and Frec_state=1"\
                %(earliest, latest)
        field_list = ["Farticle_vector","Fauto_id","Fcluster_id","Fcreate_time"]
        DB_res = self._db.query(field_list, where)
        
        for item in DB_res:
            cluster_id =        item["Fcluster_id"]
            article_id =        item["Fauto_id"]
            article_time =      item["Fcreate_time"]
            article_vector = np.array([float(elem) for elem in json.loads(item["Farticle_vector"])])
            if cluster_id in self.latest_articles.keys():
                self.latest_articles[cluster_id].append((article_id, article_time, article_vector))
            else:
                self.latest_articles[cluster_id] = [(article_id, article_time, article_vector)]
        
    def prepare_user_cover(self):
        now = datetime.now()
        time_cover = timedelta(days=USER_HISTORY_COVER)
        self.earliest_user_log = now - time_cover
        
    def main(self):
        # 初始化各种
        self.init_db()
        self.init_log()
        self.prepare_articles()
        self.prepare_user_cover()
        
        step = self.batch_size*self.proc_num
        offset = self.proc_id*self.batch_size
        
        while(True):
            where = "Fauto_id between %s and %s"%(offset+1,offset+self.batch_size)
            self.logger.log_info('process_id:%s, sql condition:%s' %(self.proc_id,where))
            field_list = ['Fuser_id']
            self._db.set_db_table("db_users","t_user_recommends")
            items = self._db.query(field_list, where)
            self._db.commit()
            
            if not items:
                break
            self.run(items)
            offset += step
            #break
            time.sleep(5)
            
        self.close()
    
def run_task(batch_size,proc_id, proc_num):
    tool = CRecommender(batch_size,proc_id, proc_num)
    tool.main()
    
    
def distribute_task(batch_size):
    p = Pool()           #开辟进程池
    for i in range(2):
        p.apply_async(run_task,args=(batch_size, i, 2))
    p.close() #关闭进程池
    p.join()
    
# 单次测试用
if __name__ == '__main__':
    #distribute_task(1000)
    
    tool = CRecommender(100,0, 1)
    tool.main()