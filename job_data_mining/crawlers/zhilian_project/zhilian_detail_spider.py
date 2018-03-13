# coding=utf-8
# 不习惯用CSS路径的同学，可以在【CSS-XPATH转换】处修改 但是改了就不要找我维护这玩意儿了！！
from crawlers.universal_spider import *
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

class ZhilianDetailItemBuilder(RowBuilder):
    # 通过自定义方法加载字段，被重写的几率较高
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
        
        self.data_res['Flstate'] = 1
        self.data_res['Fcreate_time'] = time_now()
        self.data_res['Fmodify_time'] = time_now()

class ZhilianDetailItem(UniversalItem):
    settings = Field()
    row_builder = ZhilianDetailItemBuilder()

class ZhilianDetailSpider(UniversalSpider):
    def __init__(self):
        self.HEADERS['Host'] = 'jobs.zhaopin.com'
        self.headers = self.HEADERS
        self.name = 'ZhilianDetailSpider'
        self.clean_failed_req = False
        
    def start_requests(self):
        parse_func_list = ['parse_detail']
        request_list = self.get_failed_req( parse_func_list )

        if request_list:
            self.clean_failed_req = True    # 提醒中间件，成功的请求要回写状态
            for request_info in request_list:
                meta = json.loads(request_info['Fmeta'])
                request_url = request_info['Furl']
                callback_func = request_info['Fcall_back']
                yield Request( request_url, headers=self.headers, meta=meta, callback=getattr(self,callback_func), dont_filter=True )
        else:
            
            # 开始重新全量爬取
            temp_db = CCrawlerDbHandle()
            temp_db.set_db_table('db_job','t_zhilian_task')
            field_list = ['Ftask_url']
            
            offset = 0
            while(1):
                where = "Ftask_url!='' order by Ftask_id limit 1000 offset %s"%(offset)
                res = temp_db.query( field_list, where )
                offset += 1000
                if not res:
                    print('Offset endded here ',offset)
                    break
                for item in res:
                    meta = {}
                    meta['row'] = {}
                    meta['parse'] = 'parse_detail'  # 标记回调函数
                    meta['row']['Fjob_url'] = item['Ftask_url']  
                    request_url = item['Ftask_url']
                    print(request_url)
                    yield Request( request_url, headers=self.headers, meta=meta, callback=getattr(self,meta['parse']), dont_filter=True )
            temp_db.destroy()
            '''
            meta = {}
            meta['row'] = {}
            meta['parse'] = 'parse_detail'  # 标记回调函数
            meta['row']['Fjob_url'] = 'http://jobs.zhaopin.com/531406533250043.htm'
            request_url = 'http://jobs.zhaopin.com/531406533250043.htm'
            print(request_url)
            yield Request( request_url, headers=self.headers, meta=meta, callback=getattr(self,meta['parse']), dont_filter=True )
            '''
    
    # 解析菜单
    def parse_detail(self, response):
        try:
            # 解析页面，获取元数据
            row_list = []
            row = response.meta['row']
            pn_url_list = []
            content_sel = Selector(response)
            parse_html(zhilian_detail_parse_rule, content_sel, row, row_list, pn_url_list)
            
            for row in row_list:
                yield self.load_detail_item(row)
        except:
            # 解析的页面结构变化，报警
            print(traceback.format_exc())
            
    # 装载最终行数据
    def load_detail_item(self, data):
        item = ZhilianDetailItem()
        item['row'] = {}
        item['settings'] = zhilian_detail_item_rule
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