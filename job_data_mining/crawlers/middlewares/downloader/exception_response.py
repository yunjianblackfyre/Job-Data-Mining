from scrapy import signals
from pydispatch import dispatcher
from crawlers.crawler_db_handle import CCrawlerDbHandle
from crawlers.utils import *


#logger = logging.getLogger(__name__)

class ExceptionResponse(object):
    """This middleware enables working with sites that change the user-agent"""

    def __init__(self, debug=False):
        self.db = CCrawlerDbHandle()
        self.db.set_db_table('db_job', 't_failed_task')
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self):
        self.db.destroy()

    def process_response(self, request, response, spider):
        status_code = response.status
        if status_code == 200:
            if spider.clean_failed_req:
                self.inform_success(request, spider)
            return response

        record_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print("ERROR RESPONSE STATUS is: %s, url: %s, time: %s" % (status_code, response.url, record_time))
        try:
            # 更新视频源可用性状态
            self.inform_failure(request, spider)
        except Exception as e:
            print("MIDDLEWARE PROCESS RESPONSE:%s" % e)

        return response
        
    def process_exception(self, request, exception, spider):
        print('can not access %s' % request.url)
        self.inform_failure(request, spider)

    # 发现请求失败，写数据库
    def inform_failure(self, request, spider):
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
                'Fstate':TASK_STATE['failure'],
                'Fmeta':json.dumps(request.meta),
                'Fmodify_time':time_now(),
            }
            self.db.update(datau, where)
        else:
            datai = {
                'Fcrawler_name':spider.name,
                'Fcall_back':request.meta['parse'],
                'Furl':request.url,
                'Fstate':TASK_STATE['failure'],
                'Fmeta':json.dumps(request.meta),
                'Fmethod':request.method,
                'Fencoding':request.encoding,
                'Fretry_times':1,
                'Fcreate_time':time_now(),
                'Fmodify_time':time_now(),
            }
            self.db.insert(datai)
        self.db.commit()
    
    # 发现请求成功，写数据库
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
                'Fstate':TASK_STATE['down_succ'],
                'Fmeta':json.dumps(request.meta),
                'Fmodify_time':time_now(),
            }
            self.db.update(datau, where)
            self.db.commit()