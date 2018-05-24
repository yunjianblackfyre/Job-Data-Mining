#   AUTHOR: Sibyl System
#     DATE: 2018-01-02
#     DESC: universal spider, father to all spider

import urllib
import random
import os
import requests
import hashlib
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy import Spider, Item, Field
from scrapy import Request
from scrapy.http import FormRequest

from crawlers.crawler_db_handle import CCrawlerDbHandle
from crawlers.utils import *
        
# 条目通用转化类：爬取条目->入库条目
class RowBuilder(object):
    def __init__(self):
        self._db = CCrawlerDbHandle()
    
    # 接受新的条目及其配置
    def update(self, item):
        self.whether_insert = False
        self.data = item['row']         # 基础原始数据，只读
        settings =  item['settings']    # 入库规则配置
        self.item_format = settings['item_format']
        self.item_db = settings['item_db']
        self.item_table = settings['item_table']
        self.write_table_method = settings['write_table_method']
        self.data_res = {}
        
    # 用配置转化
    def build_row_from_item(self):
        for key in self.item_format.keys():
            field_type = self.item_format[key]['type']
            raw_field = self.data.get(key)
            type_convert = TYPE_CONVERT_MAP[field_type]
            self.data_res[key] = type_convert( raw_field )
            is_default = ( TYPE_DEFAULT_VALUE_MAP[self.item_format[key]['type']]==self.data_res[key] )
            is_required = self.item_format[key]['req']
            if is_default and is_required:
                return False # 建立数据行失败
        return True
    
    # 自定义结尾
    def wind_up(self):
        pass
        # raise NotImplementedException
    
    # 自定义转化
    def build_row_from_custom(self):
        self.data_res['Fcreate_time'] = time_now()
        self.data_res['Fmodify_time'] = time_now()
        
    # 写数据库
    def write_database(self):
        self._db.set_db_table(self.item_db,self.item_table)
        # 构造入库条件
        condition_list = []
        update_data = copy.deepcopy(self.data_res)
        for key in self.item_format.keys():
            if self.item_format[key]['dup']:
                condition = key + '=' + '\'' + str(self.data_res[key]) + '\''
                update_data.pop(key)    # 去掉作为更新条件的字段
                condition_list.append(condition)
                
        where = ' and '.join(condition_list)
        print('UPDATE DATABASE CONDITION: %s'%(where))
        field_list = ['*']
        
        # 选择性写库
        if self.write_table_method=='update': # 1.更新
            if self._db.query(field_list, where):
                self.data_res.pop('Fcreate_time')
                self._db.update( update_data, where )
                self._db.commit()
            else:
                self._db.insert( self.data_res )
                self.whether_insert = True
                self._db.commit()
            
        elif self.write_table_method=='insert': # 2.无条件插入
            self._db.insert( self.data_res )
            self._db.commit()
            self.whether_insert = True
            
        elif self.write_table_method=='conditional_insert': # 3.有条件插入
            if not self._db.query(field_list,where):
                self._db.insert( self.data_res )
                self._db.commit()
                self.whether_insert = True
        else:
            print("Please specify a DB writing method")
    
    # 条目转化开始工作
    def process(self,item):
        self.update(item)
        
        if self.build_row_from_item():
            self.build_row_from_custom()
            self.write_database()
            self.wind_up()
        else:
            print('Item is not qualified for writing database')
        return self.whether_insert
        
# 通用爬取条目类
class UniversalItem(Item):
    # define the fields for your item here like:
    row = Field() # row就是一个dict item[row][FXXX]
    row_builder = RowBuilder()
    
# 通用入库流水线类
class UniversalPipeline(object):
    def __init__(self):
        pass
        #self.loger = CLog()
        #self._log_name = 'univeral_pipline'
        #self._log_level = 3
        #self.loger.init(self._log_name, LOG_CFG['dir']+'univeral_project/', self._log_name, self._log_level)

    def close_spider(self, spider):
        print( "close UniversalPipeline" )
        
    def process_item(self, item, spider):
        try:
            if item.row_builder.process(item):
                if 'insert_count' in dir(spider):
                    spider.insert_count+=1
        except Exception as e:
            print(traceback.format_exc())
            print(format(e.args))
            
            
# 通用爬虫类
class UniversalSpider(Spider):
    # 通用配置
    custom_settings = {
        'DNSCACHE_ENABLED':True,
        'ROBOTSTXT_OBEY':False,
        'RETRY_ENABLED':True,
        'DOWNLOAD_TIMEOUT':5,
        'DOWNLOAD_DELAY':0.1,
        'CONCURRENT_REQUESTS':32,
        'HTTPERROR_ALLOW_ALL':True, # 允许所有类型的返回通过中间件，调试用，发布时关闭
        'CONCURRENT_REQUESTS_PER_DOMAIN':32,
        'CONCURRENT_REQUESTS_PER_IP':32,
        'COOKIES_ENABLED':True,
        'DOWNLOADER_MIDDLEWARES':{
            'crawlers.middlewares.downloader.exception_response.ExceptionResponse': 100
            #'middlewares.downloader.record_status_code.RecordStatusCodeMiddleware': 110,
        },
        'ITEM_PIPELINES':{
            'crawlers.universal_spider.UniversalPipeline':100
        }
    }
    
    # 通用请求报头
    HEADERS = {
        'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh,zh-HK;q=0.8,zh-CN;q=0.7,en-US;q=0.5,en;q=0.3,el;q=0.2',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        #'Host': 'neets.cc',
        #'Origin':'http://neets.cc/',
        #'Referer': 'http://neets.cc/',
        'DNT': '1',
    }
    
    # 初始化爬虫
    def __init__(self):
        self.headers = self.HEADERS
        self._db = CCrawlerDbHandle()
        
    # 重新提交上次爬取失败的请求，一次获取最大10000条
    def get_failed_req( self, parse_func_list, max_retry=3 ):
        request_list = []
        temp_db = CCrawlerDbHandle()
        temp_db.set_db_table('db_crawlers','t_failed_task')
        field_list = ['*']
        
        for parse_func in parse_func_list:
            where = "Fcrawler_name='%s' and \
                    Fcall_back='%s' and \
                    Fstate='%s' and Fretry_times < %s order by Fmodify_time limit 10000"\
                    %(self.name, parse_func, TASK_STATE['failure'], max_retry)
            request_list.extend( temp_db.query( field_list, where ))
        temp_db.destroy()
        return request_list
        
    # 关闭爬虫时调用
    def closed(self, reason):
        self._db.destroy()
        print("CLOSE_REASON:%s" % reason)

if __name__ == '__main__':
    pass
