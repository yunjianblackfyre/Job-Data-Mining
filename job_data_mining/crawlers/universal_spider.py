#COPYRIGHT: Tencent flim
#   AUTHOR: SIBYL SYSTEM
#     DATE: 2017-12-24
#     DESC: 1.通用爬虫类，父类
#           实现时用子类继承
#           2.通用的下载流水线
#           3.任何Scrapy框架爬虫
#           都会用到的宏，全局
#           变量，和方法

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
        
# ITEM至数据行转化父类
class RowBuilder(object):
    # 初始化
    def __init__(self):
        self._db = CCrawlerDbHandle()
    
    # 接收到新的ITEM，更新成员
    def update(self, item, settings):
        self.data = item['row']
        self.item_format = settings['item_format']
        self.item_db = settings['item_db']
        self.item_table = settings['item_table']
        self.write_table_method = settings['write_table_method']
        self.data_res = {}
        
    # 通过ITEM加载字段
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
    
    # 通过自定义方法加载字段，被重写的几率较高
    def build_row_from_custom(self):
        self.data_res['Fcreate_time'] = time_now()
        self.data_res['Fmodify_time'] = time_now()
        
    # 写数据库，目前由三种方法
    def write_database(self):
        self._db.set_db_table(self.item_db,self.item_table)
        # 构造where语句
        condition_list = []
        for key in self.item_format.keys():
            if self.item_format[key]['dup']:
                condition = key + '=' + '\'' + str(self.data_res[key]) + '\''
                condition_list.append(condition)
                
        where = ' and '.join(condition_list)
        print('UPDATE DATABASE CONDITION: %s'%(where))
        field_list = ['*']
        
        # 选择性写库
        if self.write_table_method=='update': # 更新
            if self._db.query(field_list, where):
                self.data_res.pop('Fcreate_time')
                self._db.update( self.data_res, where )
            else:
                pass
                self._db.insert( self.data_res )
            self._db.commit()
        elif self.write_table_method=='insert': # 无条件插入
            self._db.insert( self.data_res )
            self._db.commit()
        else:
            if not self._db.query(field_list,where): # 有条件插入
                self._db.insert( self.data_res )
                self._db.commit()
    
    # Start Process
    def process(self,item,settings):
        self.update(item,settings)
        
        if self.build_row_from_item():
            self.build_row_from_custom()
            self.write_database()
        else:
            print('Item is not qualified for writing database')
        
    
class UniversalItem(Item):
    # define the fields for your item here like:
    row = Field() # row就是一个dict item[row][FXXX]
    row_builder = RowBuilder()
    

class UniversalPipeline(object):
    def __init__(self):
        pass
        #self.loger = CLog()
        #self._log_name = 'univeral_pipline'
        #self._log_level = 3
        #self.loger.init(self._log_name, LOG_CFG['dir']+'univeral_project/', self._log_name, self._log_level)

    def close_spider(self, spider):
        print( "close spider" )
        
    def process_item(self, item, spider):
        row = item.get('row',{})
        settings = item.get('settings',{})
        if settings:
            item.row_builder.process(item,settings)
            
# 通用爬虫类
class UniversalSpider(Spider):
    # 通用设置
    custom_settings = {
        'DNSCACHE_ENABLED':True,
        'ROBOTSTXT_OBEY':False,
        'RETRY_ENABLED':True,
        'DOWNLOAD_TIMEOUT':1080,
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
    
    # 请求报头
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
        
    # 重新提交上次爬取失败的请求，一次获取最大10000条
    def get_failed_req( self, parse_func_list ):
        request_list = []
        temp_db = CCrawlerDbHandle()
        temp_db.set_db_table('db_job','t_failed_task')
        field_list = ['*']
        
        for parse_func in parse_func_list:
            where = "Fcrawler_name='%s' and \
                    Fcall_back='%s' and \
                    Fstate='%s' and Fretry_times < 3 order by Fmodify_time limit 10000"\
                    %(self.name, parse_func, TASK_STATE['failure'])
            request_list.extend( temp_db.query( field_list, where ))
        temp_db.destroy()
        return request_list
        
    # 关闭spider时调用
    def closed(self, reason):
        print("CLOSE_REASON:%s" % reason)

if __name__ == '__main__':
    pass
