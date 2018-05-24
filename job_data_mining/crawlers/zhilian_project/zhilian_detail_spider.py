#   AUTHOR: Sibyl System
#     DATE: 2018-01-02
#     DESC: zhilian job detailed info

from crawlers.universal_spider import *
from crawlers.status import StatusCode
from crawlers.config import zhilian_detail_item_rule
from crawlers.config import zhilian_detail_parse_rule
from crawlers.crawler_db_handle import CCrawlerDbHandle

JOB_INFO_FIELDS = {
    '公司规模：':'Fcorp_size',
    '公司性质：':'Fcorp_type',
    '公司行业：':'Fcorp_category',
    '公司主页：':'Fcorp_url',
    '公司地址：':'Fcorp_location'
}

MAX_RETRY_TIME = 2  # 最多重试两次

def mark_task(db, URL, status_code, retry_time=0):
    db.set_db_table('db_crawlers','t_zhilian_task')
    where = "Ftask_url='%s'"%(URL)
    datau = {
        "Flstate":          status_code,
        "Fretry_time":      retry_time,
        "Fmodify_time":     time_now()
    }
    db.update(datau,where)
    db.commit()

class ZhilianDetailItemBuilder(RowBuilder):
    def build_row_from_custom(self):
        info_list = [info_item for info_item in \
                        self.data['Fcorp_info'].split() if info_item.strip()]
        for idx in range(len(info_list)):
            if info_list[idx] in JOB_INFO_FIELDS.keys():
                field_name = JOB_INFO_FIELDS[info_list[idx]]
                try:
                    self.data_res[field_name] = info_list[idx + 1]
                except:
                    self.data_res[field_name] = ''
        
        self.data_res['Flstate'] = 0        # 0-标记为初始态
        self.data_res['Fcreate_time'] = time_now()
        self.data_res['Fmodify_time'] = time_now()
        
    def wind_up(self):
        mark_task(self._db, self.data["Fjob_url"],StatusCode.STAT_TASK_SUCCESS.value)

class ZhilianDetailItem(UniversalItem):
    settings = Field()
    row_builder = ZhilianDetailItemBuilder()

class ZhilianDetailSpider(UniversalSpider):
    def __init__(self):
        self.HEADERS['Host'] = 'jobs.zhaopin.com'
        self.headers = self.HEADERS
        self._db = CCrawlerDbHandle()
        self.name = 'ZhilianDetailSpider'
        self.clean_failed_req = False
    
    # 招聘信息详情页请求
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
        self._db.set_db_table('db_crawlers','t_zhilian_task')
        field_list = ['Ftask_url']
        
        while(True):
            # where = "Ftask_url not in (select Fjob_url from db_crawlers.t_zhilian_detail)" # 测试用
            where = "Flstate=%s order by Fcreate_time desc limit 1000"%(StatusCode.STAT_TASK_INIT.value)
            
            DB_res = self._db.query( field_list, where )
            
            if not DB_res:
                print('No new taks found')
                break
                
            for item in DB_res:
                mark_task(self._db, item["Ftask_url"],StatusCode.STAT_TASK_START.value)
                meta = {}
                meta['row'] = {
                    "Fjob_url":     item["Ftask_url"],
                }
                meta['parse'] = 'parse_detail'  # 标记回调函数
                request_url = item['Ftask_url']
                
                print(request_url)
                yield Request( request_url, headers=self.headers, meta=meta, callback=getattr(self,meta['parse']), dont_filter=True )
    
    # 解析招聘信息详情页
    def parse_detail(self, response):
        try:
            # 解析页面，获取元数据
            row_list = []
            row = response.meta['row']
            pn_url_list = []
            content_sel = Selector(response)
            parse_html(zhilian_detail_parse_rule, content_sel, row, row_list, pn_url_list,html_clean=False)
            
            for row in row_list:
                yield self.load_detail_item(row)
        except:
            # 解析的页面结构变化，报警
            print(traceback.format_exc())
            
    # 构建爬取条目
    def load_detail_item(self, data):
        item = ZhilianDetailItem()
        item['row'] = {}
        item['settings'] = zhilian_detail_item_rule
        
        data['Fjob_name']       = clean_html(data['Fjob_name'])
        data['Fjob_salary']     = clean_html(data['Fjob_salary'])
        data['Freq_year']       = clean_html(data['Freq_year'])
        data['Fpos_count']      = clean_html(data['Fpos_count'])
        data['Fjob_location']   = clean_html(data['Fjob_location'])
        data['Fjob_type']       = clean_html(data['Fjob_type'])
        data['Freq_edu']        = clean_html(data['Freq_edu'])
        data['Fjob_category']   = clean_html(data['Fjob_category'])
        data['Fcorp_name']      = clean_html(data['Fcorp_name'])
        data['Fcorp_info']      = clean_html(data['Fcorp_info'])
        data['Fcorp_summary']   = clean_html(data['Fcorp_summary'])
        
        item['row'] = data
        return item

if __name__ == '__main__':
    try:
        runner = CrawlerRunner()
        runner.crawl(ZhilianDetailSpider)
        d = runner.join()
        d.addBoth(lambda _: reactor.stop())
        reactor.run()
    
    except Exception as e:
        print(traceback.format_exc())