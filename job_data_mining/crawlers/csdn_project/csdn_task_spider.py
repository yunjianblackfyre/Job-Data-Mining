#   AUTHOR: Sibyl System
#     DATE: 2018-01-02
#     DESC: csdn task crawler

from crawlers.universal_spider import *
from scrapy.exceptions import CloseSpider
from crawlers.config import csdn_task_item_rule
from crawlers.config import csdn_menu_parse_rule
from crawlers.config import csdn_pro_user_parse_rule
from crawlers.config import csdn_raw_user_parse_rule
from crawlers.crawler_db_handle import CCrawlerDbHandle

category_list = [
    'news',
    'ai',
    'cloud',
    'blockchain',
    'news',
    'db',
    'career',
    'game',
    'engineering',
    'web',
    'mobile',
    'iot',
    'ops',
    'fund',
    'lang',
    'arch',
    'avi',
    'sec',
    'other'
]

MAX_RETRY_TIME = 2  # 最多重试两次

class CsdnTaskItemBuilder(RowBuilder):
    def build_row_from_custom(self):
        self.data_res['Flstate'] = 0    # 入库时定位为初始状态
        self.data_res['Fcreate_time'] = time_now()
        self.data_res['Fmodify_time'] = time_now()

class CsdnTaskItem(UniversalItem):
    settings = Field()
    row_builder = CsdnTaskItemBuilder()

class CsdnTaskSpider(UniversalSpider):
    def __init__(self):
        self.headers = self.HEADERS
        self.name = 'CsdnTaskSpider'
        self._db = CCrawlerDbHandle()
        self.max_pull_down = 10000 # 手动设定
        self.insert_count = 0
    
    def start_requests(self):
        parse_func_list = ['parse_menu','parse_dyn_menu']
        request_list = self.get_failed_req( parse_func_list, MAX_RETRY_TIME )
        
        # 先处理上次爬取失败的请求
        if request_list:
            for request_info in request_list:
                meta = json.loads(request_info['Fmeta'])
                meta[REQ_FAIL_MARK] = True     # 提醒中间件，成功的请求要回写状态
                request_url = request_info['Furl']
                callback_func = request_info['Fcall_back']
                yield Request( request_url, headers=self.headers, meta=meta, callback=getattr(self,callback_func), dont_filter=False )
        '''
        else:
        for idx in range(self.max_pull_down):
            for category in category_list:
                url = 'https://www.csdn.net/api/articles?type=more&category=%s&shown_offset=0&zenegao=%s'%(category,idx)
                meta = {}
                meta['row'] = {}
                meta['parse'] = 'parse_dyn_menu'  # 标记回调函数
                meta['row']['Fmenu_url'] = url
                meta['row']['Fcategory'] = category
                request_url = url
                yield Request( request_url, headers=self.headers, meta=meta, callback=getattr(self,meta['parse']), dont_filter=False )
                
        '''
        # 请求新文章模块
        url = 'https://blog.csdn.net/nav/newarticles'
        meta = {}
        meta['row'] = {}
        meta['parse'] = 'parse_menu'  # 标记回调函数
        yield Request( url, headers=self.headers, meta=meta, callback=getattr(self,meta['parse']), dont_filter=False )
        
        
    def parse_menu(self, response):
        try:
            # 解析页面，获取元数据
            row_list = []
            row = response.meta['row']
            pn_url_list = []
            content_sel = Selector(response)
            parse_html(csdn_menu_parse_rule, content_sel, row, row_list, pn_url_list)
            
            for row in row_list:
                shown_offset = row["Fshown_offset"]
                if re.match("\d+",shown_offset):
                    url = 'https://www.csdn.net/api/articles?type=more&category=newarticles&shown_offset=%s'%(shown_offset)
                    meta = {}
                    meta['row'] = {}
                    meta['parse'] = 'parse_dyn_menu'  # 标记回调函数
                    meta['row']['Fcategory'] = 'newarticles'
                    yield Request( url, headers=self.headers, meta=meta, callback=getattr(self,meta['parse']), dont_filter=False )
                        
        except:
            # 解析的页面结构变化，报警
            print(traceback.format_exc())
    
    # 解析动态主页
    def parse_dyn_menu(self, response):
        try:
            response_dict = json.loads(response.body.decode())
            row_list = response_dict['articles']
            next_offset = response_dict['shown_offset']
            # print('dyn elements:',len(row_list))
            
            for row in row_list:
                if row.get('user_url'):
                    # 开始本次请求
                    meta = {}
                    meta['row'] = {}
                    meta['row']['Fauthor'] = row.get('nickname')
                    meta['parse'] = 'parse_user'  # 标记回调函数
                    request_url = row['user_url']
                    yield Request( request_url, headers=self.headers, meta=meta, callback=getattr(self,meta['parse']), dont_filter=False )
            
            # 如果类型为“最新文章”，则继续下拉
            if response.meta['row']['Fcategory']=='newarticles':
                meta = {}
                meta['row'] = {}
                meta['parse'] = 'parse_dyn_menu'  # 标记回调函数
                meta['row']['Fcategory'] = 'newarticles'
                request_url = 'https://www.csdn.net/api/articles?type=more&category=newarticles&shown_offset=%s'%(next_offset)
                yield Request( request_url, headers=self.headers, meta=meta, callback=getattr(self,meta['parse']), dont_filter=False )
        except:
            # 解析的页面结构变化，报警
            print(traceback.format_exc())
            
    def parse_user(self, response):
        if self.insert_count > ONE_TIME_MAXINSERT:
            raise CloseSpider   # 已经达到最大数据插入数，关闭爬虫
        else:
            print("item inserted.. %s"%(self.insert_count))
        try:
            row_list = []
            row = response.meta['row']
            pn_url_list = []
            content_sel = Selector(response)
            #print('raw user table:',content_sel.css('#article_list > div'))
            #print('pro user table:',content_sel.css('li.blog-detail > ul.blog-units.blog-units-box'))
            #print('next:',content_sel.css('a[rel=next]::attr(href)'))
            
            if content_sel.css(csdn_pro_user_parse_rule['children_path']):
                user_parse_rule = csdn_pro_user_parse_rule
            else:
                user_parse_rule = csdn_raw_user_parse_rule
                
            parse_html(user_parse_rule, content_sel, row, row_list, pn_url_list)
            
            for row in row_list:
                yield self.load_task_item(row)
                   
            # 提交下一页请求
            if pn_url_list:
                pn_url = pn_url_list[0]
                # pn_url = 'http:' + pn_url
                print('next page url found:',pn_url)
                meta = response.meta
                yield Request( pn_url, headers=self.headers, meta=meta, callback=getattr(self,meta['parse']), dont_filter=True )
        except:
            # 解析的页面结构变化，报警
            print(traceback.format_exc())
    
    
    # 构建爬取条目
    def load_task_item(self, data):
        print_dict(data)
        item = CsdnTaskItem()
        item['row'] = {}
        item['row']["Fauthor"] = data.get("Fauthor","")
        item['row']["Ftask_url"] = data.get("Fh5_url","")
        item['row']["Ftags"] = ''
        item['settings'] = csdn_task_item_rule
        return item
    
        
    # 关闭爬虫时调用
    def closed(self, reason):
        print("CLOSE_REASON:%s" % reason)

if __name__ == '__main__':
    try:
        runner = CrawlerRunner()
        runner.crawl(CsdnTaskSpider)
        d = runner.join()
        d.addBoth(lambda _: reactor.stop())
        reactor.run()
    
    except Exception as e:
        print(traceback.format_exc())