#   AUTHOR: Sibyl System
#     DATE: 2018-01-02
#     DESC: zhilian job list info

from crawlers.universal_spider import *
from crawlers.config import zhilian_task_parse_rule
from crawlers.config import zhilian_menu_parse_rule
from crawlers.config import zhilian_task_item_rule
from crawlers.crawler_db_handle import CCrawlerDbHandle

ZHILIAN_TASK_LIST = [
  #{"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=北京&p=1&isadv=0","data":{"Flocation":"北京"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=上海&p=1&isadv=0","data":{"Flocation":"上海"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=广州&p=1&isadv=0","data":{"Flocation":"广州"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=深圳&p=1&isadv=0","data":{"Flocation":"深圳"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=天津&p=1&isadv=0","data":{"Flocation":"天津"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=武汉&p=1&isadv=0","data":{"Flocation":"武汉"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=西安&p=1&isadv=0","data":{"Flocation":"西安"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=成都&p=1&isadv=0","data":{"Flocation":"成都"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=大连&p=1&isadv=0","data":{"Flocation":"大连"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=长春&p=1&isadv=0","data":{"Flocation":"长春"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=沈阳&p=1&isadv=0","data":{"Flocation":"沈阳"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=南京&p=1&isadv=0","data":{"Flocation":"南京"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=济南&p=1&isadv=0","data":{"Flocation":"济南"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=青岛&p=1&isadv=0","data":{"Flocation":"青岛"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=杭州&p=1&isadv=0","data":{"Flocation":"杭州"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=苏州&p=1&isadv=0","data":{"Flocation":"苏州"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=无锡&p=1&isadv=0","data":{"Flocation":"无锡"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=宁波&p=1&isadv=0","data":{"Flocation":"宁波"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=重庆&p=1&isadv=0","data":{"Flocation":"重庆"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=郑州&p=1&isadv=0","data":{"Flocation":"郑州"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=长沙&p=1&isadv=0","data":{"Flocation":"长沙"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=福州&p=1&isadv=0","data":{"Flocation":"福州"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=厦门&p=1&isadv=0","data":{"Flocation":"厦门"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=哈尔滨&p=1&isadv=0","data":{"Flocation":"哈尔滨"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=石家庄&p=1&isadv=0","data":{"Flocation":"石家庄"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=合肥&p=1&isadv=0","data":{"Flocation":"合肥"}},
  {"url":"http://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&jl=惠州&p=1&isadv=0","data":{"Flocation":"惠州"}}
]

class ZhilianTaskItemBuilder(RowBuilder):
    def build_row_from_custom(self):
        self.data_res['Fstate'] = TASK_STATE['init']
        self.data_res['Fcreate_time'] = time_now()
        self.data_res['Fmodify_time'] = time_now()

class ZhilianTaskItem(UniversalItem):
    settings = Field()
    row_builder = ZhilianTaskItemBuilder()

class ZhilianTaskSpider(UniversalSpider):
    def __init__(self):
        self.HEADERS['Host'] = 'sou.zhaopin.com'
        self.headers = self.HEADERS
        self.name = 'ZhilianTaskSpider'
        self.clean_failed_req = False
    
    # 招聘信息菜单页请求
    def start_requests(self):
        parse_func_list = ['parse_menu','parse_task']
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
            for task in ZHILIAN_TASK_LIST:
                meta = {}
                meta['row']=task['data']
                meta['parse']='parse_menu'  # 标记回调函数
                request_url = task['url']
                yield Request( request_url, headers=self.headers, meta=meta, callback=getattr(self,meta['parse']), dont_filter=True )
    
    # 装载爬取条目
    def load_task_item(self, data):
        item = ZhilianTaskItem()
        item['row'] = {}
        item['settings'] = zhilian_task_item_rule
        item['row']['Ftask_url'] = data['Ftask_url']
        item['row']['Fcategory'] = data['Ftask_name']
        return item
    
    # 解析菜单页
    def parse_menu(self, response):
        try:
            # 解析页面，获取元数据
            row_list = []
            row = response.meta['row']
            pn_url_list = []
            content_sel = Selector(response)
            parse_html(zhilian_menu_parse_rule, content_sel, row, row_list, pn_url_list)
            
            # 元数据处理
            shiny_row_list = []
            black_word_1 = '不限'
            black_word_2 = '软件/互联网开发/系统集成'
            for row_item in row_list:
                if black_word_1 not in row_item['Fmenu_name'] and \
                   black_word_2 not in row_item['Fmenu_name']:
                   row_item['Fmenu_url']=urljoin("https://"+self.HEADERS['Host'],row_item['Fmenu_url'])
                   shiny_row_list.append(row_item)
            
            # 招聘信息列表页请求
            for row_item in shiny_row_list:
                meta = {}
                meta['row'] = row_item
                meta['parse'] = 'parse_task'
                request_url = row_item['Fmenu_url']
                yield Request( request_url, headers=self.headers, meta=meta, callback=getattr(self,meta['parse']), dont_filter=True )
        except:
            # 页面结构变化，报警
            print(trace_back.format_exc())
    
    # 解析招聘信息列表页
    def parse_task(self, response):
        
        try:
            # 解析页面，获取元数据
            content_sel = Selector(response)
            row_list = []
            row = response.meta['row']
            pn_url_list = []
            parse_html(zhilian_task_parse_rule, content_sel, row, row_list, pn_url_list)
            
            print('next page:',pn_url_list)
            # 产生最终数据行
            for row_item in row_list:
                yield self.load_task_item(row_item)
                
            # 提交下一页请求
            if pn_url_list:
                pn_url = pn_url_list[0]
                meta = response.meta
                yield Request( pn_url, headers=self.headers, meta=meta, callback=getattr(self,meta['parse']), dont_filter=True )
        except:
            # 解析的页面结构变化，报警
            print(trace_back.format_exc())
        
            
        
    '''
     #用于单个req测试
    def start_requests(self):
        url = "https://sou.zhaopin.com/jobs/searchresult.ashx?bj=160000&sj=2043&jl=%E5%8C%97%E4%BA%AC&p=1&isadv=0"
        yield Request( url, headers = self.headers, callback=self.parse_test, dont_filter=True )

    def parse_test(self, response):
        print(response)
        try:
            content_sel = Selector(response)
            sel_list=content_sel.css('#newlist_list_content_table > table')
            for sel in sel_list:
                try:
                    print(sel.css('td.zwmc > div > a::attr(href)').extract()[0])
                    print(clean_html(sel.css('td.zwmc > div > a').extract()[0]))
                except:
                    pass
                # print(clean_html(sel.css('td.zwmc > div > a').extract()[0]))
        except:
            # 解析的页面结构变化，报警
            print(trace_back.format_exc())
    '''

if __name__ == '__main__':
    try:
        runner = CrawlerRunner()
        runner.crawl(ZhilianTaskSpider)
        d = runner.join()
        d.addBoth(lambda _: reactor.stop())
        reactor.run()
    
    except Exception as e:
        print(traceback.format_exc())