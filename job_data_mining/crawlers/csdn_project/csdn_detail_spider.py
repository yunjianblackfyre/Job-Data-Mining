#   AUTHOR: Sibyl System
#     DATE: 2018-01-02
#     DESC: csdn detail info

from crawlers.universal_spider import *
from crawlers.status import StatusCode
from crawlers.config import csdn_detail_item_rule
from crawlers.config import csdn_menu_parse_rule
from crawlers.config import csdn_detail_parse_rule
from crawlers.config import csdn_pro_user_parse_rule
from crawlers.config import csdn_raw_user_parse_rule
from crawlers.crawler_db_handle import CCrawlerDbHandle

MAX_RETRY_TIME = 2  # 最多重试两次

def mark_task(db, URL, status_code, retry_time=0):
    db.set_db_table('alashoo','t_csdn_task')
    where = "Ftask_url='%s'"%(URL)
    datau = {
        "Flstate":          status_code,
        "Fretry_time":      retry_time,
        "Fmodify_time":     time_now()
    }
    db.update(datau,where)
    db.commit()

class CsdnDetailItemBuilder(RowBuilder):
    def build_row_from_custom(self):
        self.data_res['Fimage'] = ''
        self.data_res['Flstate'] = 2    # 入库时定位为已完成态
        self.data_res['Fcreate_time'] = time_now()
        self.data_res['Fmodify_time'] = time_now()
        
    def wind_up(self):
        mark_task(self._db, self.data["Fh5_url"],StatusCode.STAT_TASK_SUCCESS.value)

class CsdnDetailItem(UniversalItem):
    settings = Field()
    row_builder = CsdnDetailItemBuilder()

class CsdnDetailSpider(UniversalSpider):

    def __init__(self):
        self.headers = self.HEADERS
        self.name = 'CsdnDetailSpider'
        self._db = CCrawlerDbHandle()
        self.max_pull_down = 10000 # 手动设定
        
    # 失败请求会写通用表
    def inform_failure(self, retry_time, request, response):
        # 参数检测
        if retry_time >= MAX_RETRY_TIME:
            mark_task(self._db, request.url,StatusCode.STAT_TASK_FAILED.value, retry_time)
        elif retry_time >=0:
            mark_task(self._db, request.url,StatusCode.STAT_TASK_RETRY.value, retry_time)
        else:
            print("retry time cannot be negative")
    
    def start_requests(self):
        parse_func_list = ['parse_detail']
        request_list = self.get_failed_req( parse_func_list, MAX_RETRY_TIME )
        
        # 先处理上次爬取失败的请求
        if request_list:
            for request_info in request_list:
                meta = json.loads(request_info['Fmeta'])
                meta[REQ_FAIL_MARK] = True     # 提醒中间件，成功的请求要回写状态
                request_url = request_info['Furl']
                callback_func = request_info['Fcall_back']
                yield Request( request_url, headers=self.headers, meta=meta, callback=getattr(self,callback_func), dont_filter=False )
        
        
        # 开始本次请求
        self._db.set_db_table('alashoo','t_csdn_task')
        field_list = ['Fauto_id','Fauthor','Ftask_url','Ftags']
        
        while(True):
            # where = "Fauto_id = 20187 limit 100" # 测试用
            where = "Flstate=%s order by Fcreate_time desc limit 1000"%(StatusCode.STAT_TASK_INIT.value)
            
            DB_res = self._db.query( field_list, where )
            
            if not DB_res:
                print('No new taks found')
                break
                
            for item in DB_res:
                mark_task(self._db, item["Ftask_url"],StatusCode.STAT_TASK_START.value)
                meta = {}
                meta['row'] = {
                    "Fauto_id":     item["Fauto_id"],
                    "Fh5_url":      item["Ftask_url"],
                    "Fauthor":      item["Fauthor"],
                    "Ftags":        item["Ftags"]
                }
                meta['parse'] = 'parse_detail'  # 标记回调函数
                request_url = item['Ftask_url']
                
                print(request_url)
                yield Request( request_url, headers=self.headers, meta=meta, callback=getattr(self,meta['parse']), dont_filter=True )
        
    # 解析子页面
    def parse_detail(self, response):
        try:
            # 解析页面，获取元数据
            row_list = []
            row = response.meta['row']
            pn_url_list = []
            content_sel = Selector(response)
            parse_html(csdn_detail_parse_rule, content_sel, row, row_list, pn_url_list, html_clean=False)
            for row in row_list:
                # 由于原始文本带有大量连续换行符，十分难看，这里做一下简单预处理
                if row['Fcontent'] and row['Ftitle']:
                    # self.load_detail_item(row)
                    yield self.load_detail_item(row)
                    
                    # 如果能在文章中匹配出csdn的文章url，就发出
                    deep_urls = []# re.findall('http:\/\/blog.csdn.net\/\w+\/article\/details\/\d+',row['Fcontent'])
                    for deep_url in deep_urls:
                        meta = {}
                        meta['row'] = {}
                        meta['row']['Fh5_url'] = deep_url
                        meta['row']['Ftags'] = ''
                        meta['parse'] = 'parse_detail'
                        request_url = deep_url
                        print('sent a deep request:%s'%(deep_url))
                        yield Request( request_url, headers=self.headers, meta=meta, callback=getattr(self,meta['parse']), dont_filter=False )
                        
        except:
            # 解析的页面结构变化，报警
            print(traceback.format_exc())
    
    # 构建爬取条目
    def load_detail_item(self, data):
    
        # 标签字段预处理
        tag_stream = data['Ftags']
        if tag_stream and ',' in tag_stream:
            tag_stream = '|'.join([tag for tag in tag_stream.split(',') if tag.strip()])
            data['Ftags'] = tag_stream
        
        # 标题预处理
        data['Ftitle'] =        clean_html(data['Ftitle'])
        
        # 发布时间预处理
        data['Fpost_time'] = gettime_from_string(clean_html(data['Fpost_time']))
        
        # 阅读数量预处理
        data['Fread_num'] =     clean_html(data['Fread_num'])
        num_list = re.findall('\d+',data['Fread_num'])
        if num_list:
            data['Fread_num'] = num_list[0]
        else:
            data['Fread_num'] = '0'
        
        #data.pop('Fcontent')
        #print_dict(data)
        
        item = CsdnDetailItem()
        item['row'] = {}
        item['settings'] = csdn_detail_item_rule
        item['row'] = data
        return item
        
    # 关闭爬虫时调用
    def closed(self, reason):
        self._db.destroy()
        print("CLOSE_REASON:%s" % reason)

if __name__ == '__main__':
    try:
        runner = CrawlerRunner()
        runner.crawl(CsdnDetailSpider)
        d = runner.join()
        d.addBoth(lambda _: reactor.stop())
        reactor.run()
    
    except Exception as e:
        print(traceback.format_exc())