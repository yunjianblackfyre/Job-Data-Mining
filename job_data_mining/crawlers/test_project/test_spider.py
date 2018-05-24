#   AUTHOR: Sibyl System
#     DATE: 2018-04-18
#     DESC: test info

from crawlers.universal_spider import *
from crawlers.crawler_db_handle import CCrawlerDbHandle

class TestSpider(UniversalSpider):
    custom_settings = {
        'DNSCACHE_ENABLED':True,
        'ROBOTSTXT_OBEY':False,
        'RETRY_ENABLED':True,
        'DOWNLOAD_TIMEOUT':30,
        'DOWNLOAD_DELAY':0.1,
        'CONCURRENT_REQUESTS':32,
        'HTTPERROR_ALLOW_ALL':True, # 允许所有类型的返回通过中间件，调试用，发布时关闭
        'CONCURRENT_REQUESTS_PER_DOMAIN':32,
        'CONCURRENT_REQUESTS_PER_IP':32,
        'COOKIES_ENABLED':True,
        'DOWNLOADER_MIDDLEWARES':{
            #'crawlers.middlewares.downloader.exception_response.ExceptionResponse': 100
            #'middlewares.downloader.record_status_code.RecordStatusCodeMiddleware': 110,
        },
        'ITEM_PIPELINES':{
            #'crawlers.universal_spider.UniversalPipeline':100
        }
    }
    
    def __init__(self):
        self.headers = self.HEADERS
        self.name = 'TestSpider'
    
    def start_requests(self):
        meta = {}
        meta['row'] = {}
        meta['parse'] = 'parse_detail'  # 标记回调函数
        meta['row']['Fmenu_url'] = 'http://cp14-ccp2-2.play.bokecc.com/flvs/ca/Qxh7R/ubcyCLoJWI-2.flv?t=1524993720&key=6A59A81669EC20E51F7FC60D8C02598C&upid=1434341524986520278&pt=0&pi=1'
        meta['row']['Fcategory'] = 'newarticles'
        request_url = 'http://cp14-ccp2-2.play.bokecc.com/flvs/ca/Qxh7R/ubcyCLoJWI-2.flv?t=1524993720&key=6A59A81669EC20E51F7FC60D8C02598C&upid=1434341524986520278&pt=0&pi=1'
        print(request_url)
        yield Request( request_url, headers=self.headers, meta=meta, callback=getattr(self,meta['parse']), dont_filter=False )
    
    # 解析子页面
    def parse_detail(self, response):
        out = open("./haha.flv",'wb') ## Open temporary file as bytes
        out.write(response.body)
        
    # 关闭爬虫时调用
    def closed(self, reason):
        print("detail response count:%s"%(self.detail_response_count))
        print("CLOSE_REASON:%s" % reason)

if __name__ == '__main__':
    try:
        runner = CrawlerRunner()
        runner.crawl(TestSpider)
        d = runner.join()
        d.addBoth(lambda _: reactor.stop())
        reactor.run()
    
    except Exception as e:
        print(traceback.format_exc())