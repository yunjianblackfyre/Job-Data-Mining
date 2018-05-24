#   AUTHOR: Sibyl System
#     DATE: 2018-01-02
#     DESC: exception response shall be intercepted here

from scrapy import signals
from pydispatch import dispatcher
from crawlers.crawler_db_handle import CCrawlerDbHandle
from crawlers.utils import *

class ExceptionResponse(object):
    """This middleware enables working with sites that change the user-agent"""

    def __init__(self, debug=False):
        self.db = CCrawlerDbHandle()
        self.db.set_db_table('db_crawlers', 't_failed_task')
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self):
        print("close ExceptionResponse")
        self.db.destroy()

    def process_response(self, request, response, spider):
        status_code = response.status
        if response.status == 200:
            if request.meta.get(REQ_FAIL_MARK,False):
                self.inform_success(request, spider)
            return response

        record_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print("ERROR RESPONSE STATUS is: %s, url: %s, time: %s" % (status_code, response.url, record_time))
        try:
            retry_time = self.inform_failure(request, spider)       # 通报失败，将失败信息收入通用表
            if REQ_FAIL_PROCFUN in dir(spider):                     # 通报失败，执行定制的失败处理方法
                getattr(spider,REQ_FAIL_PROCFUN)(retry_time,request,response)
            
        except Exception as e:
            print("MIDDLEWARE PROCESS RESPONSE:%s" % e)
        return response

    # 失败请求会写通用表
    def inform_failure(self, request, spider):
        # 初始化变量
        retry_time = 0
        
        # 参数检测
        if not spider.name:
            print('spider name not found for request %s'%(request.url))
            return retry_time
        
        # 更新或插入失败请求记录
        field_list = ['*']
        where = "Fcrawler_name='%s' and Fcall_back='%s' and Furl='%s'"\
                    %(spider.name, request.meta['parse'],request.url)
        datar = self.db.query(field_list, where)
        if datar:
            datar = datar[0]
            retry_time = datar['Fretry_times'] + 1
            datau = {
                'Fretry_times':retry_time,
                'Fstate':TASK_STATE['failure'],
                'Fmeta':json.dumps(request.meta),
                'Fmodify_time':time_now(),
            }
            self.db.update(datau, where)
        else:
            retry_time = 0
            datai = {
                'Fcrawler_name':spider.name,
                'Fcall_back':request.meta['parse'],
                'Furl':request.url,
                'Fstate':TASK_STATE['failure'],
                'Fmeta':json.dumps(request.meta),
                'Fmethod':request.method,
                'Fencoding':request.encoding,
                'Fretry_times':retry_time,
                'Fcreate_time':time_now(),
                'Fmodify_time':time_now(),
            }
            self.db.insert(datai)
        self.db.commit()
        return retry_time
    
    # 成功请求回写通用表
    def inform_success(self, request, spider):
        # 参数检测
        if not spider.name:
            print('spider name not found for request %s'%(request.url))
            return 
        
        # 更新或插入失败请求记录
        field_list = ['*']
        where = "Fcrawler_name='%s' and Fcall_back='%s' and Furl='%s'"\
                    %(spider.name, request.meta['parse'],request.url)
        datar = self.db.query(field_list, where)
        if datar:
            datar = datar[0]
            datau = {
                'Fretry_times':datar['Fretry_times'] + 1,
                'Fstate':TASK_STATE['success'],
                'Fmeta':json.dumps(request.meta),
                'Fmodify_time':time_now(),
            }
            self.db.update(datau, where)
            self.db.commit()