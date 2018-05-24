#   AUTHOR: Sibyl System
#     DATE: 2018-04-18
#     DESC: test info

from crawlers.config import csdn_image_item_rule
from crawlers.status import StatusCode
from crawlers.universal_spider import *
from crawlers.crawler_db_handle import CCrawlerDbHandle

csdn_img_file = "/var/lib/tomcat8/webapps/ROOT/article/images/"

local_ip = "http://192.168.1.106:8080/article/images/"

imgfmt_pattern_dict = {
    ".png":"\.png[^a-z]",
    ".jpg":"\.jpg[^a-z]",
    ".gif":"\.gif[^a-z]",
    ".svg":"\.svg[^a-z]",
    ".bmp":"\.bmp[^a-z]",
    ".jpeg":"\.jpeg[^a-z]"
}

imgfmt_pattern_list = [
    ".png",
    ".jpg",
    ".gif",
    ".svg",
    ".bmp",
    ".jpeg"
]

def get_imgfmt(url):
    url_mod = url + '$'
    for imgfmt in imgfmt_pattern_list:
        imgfmt_pattern = imgfmt_pattern_dict[imgfmt]
        if re.search(imgfmt_pattern, url_mod):
            return imgfmt
    return '.jpg'

def deal_images(item):
    # 初始化变量
    content_id = item['Fauto_id']
    content = item['Fcontent']
    create_date = item['Fpost_time'].strftime("%Y%m%d")
    img_count = 0
    
    content_sel = Selector(text=content)
    
    for img_url in [url for url in content_sel.css("img::attr(src)").extract() if url.strip()]:
        img_info = {
            "img_article":content_id,
            "img_url":img_url,
            "create_date":create_date,
            "img_count":img_count,
            "img_fmt":get_imgfmt(img_url)
        }
        img_count+=1
        yield img_info

def download_image(img_info):
    
    try:
        content_id =    img_info["img_article"]
        create_date =   img_info["create_date"]
        img_count =     img_info["img_count"]
        img_fmt =       img_info["img_fmt"]
        img_content =   img_info["img_content"]
        
        dir_path = csdn_img_file + create_date
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
            
        filename = '/'+str(content_id)+"_"+str(img_count)+img_fmt
        image_path = dir_path + filename
        out = open(image_path,'wb') ## Open temporary file as bytes
        out.write(img_content)
        new_img_url = local_ip + create_date + filename
    except:
        print(traceback.format_exc())
        new_img_url = ''
    finally:
        return new_img_url
        
def mark_detail(db, P_key, status_code):
    db.set_db_table('alashoo','t_csdn_detail')
    where = "Fauto_id='%s'"%(P_key)
    datau = {
        "Flstate":          status_code,
        "Fmodify_time":     time_now()
    }
    db.update(datau,where)
    db.commit()

class CsdnImageItemBuilder(RowBuilder):
    def build_row_from_custom(self):
        content_id = self.data_res['Fauto_id']
        self._db.set_db_table("alashoo","t_csdn_detail")
        where = "Fauto_id='%s' limit 1"%(content_id)
        res = self._db.query(['Fimage'],where)
        self._db.commit()
        if res:
            head_img =  res[0]['Fimage']
            if head_img:
                head_imglist = head_img.split(',')
                head_imglist.append(self.data_res['Fimage'])
                head_imglist = list(set(head_imglist))  # 去重
                self.data_res['Fimage'] = ','.join(head_imglist)
        print(self.data_res['Fimage'])
        self.data_res['Fcreate_time'] = time_now()
        self.data_res['Fmodify_time'] = time_now()
        
    def wind_up(self):
        mark_detail(self._db, self.data_res['Fauto_id'],StatusCode.STAT_DETAIL_IMGREADY.value)

class CsdnImageItem(UniversalItem):
    settings = Field()
    row_builder = CsdnImageItemBuilder()
        
class CsdnImageSpider(UniversalSpider):

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
        },
        'ITEM_PIPELINES':{
            'crawlers.universal_spider.UniversalPipeline':100
        }
    }
    
    def __init__(self):
        self.headers = self.HEADERS
        self.name = 'CsdnImageSpider'
        self._db = CCrawlerDbHandle()
    
    def start_requests(self):
        temp_db = CCrawlerDbHandle()
        self._db.set_db_table('alashoo','t_csdn_detail')
        field_list = ['*']
        
        while(True):
            # where = "Fauto_id='67'"
            # where = "Flstate=%s order by Fpost_time desc limit 1000"%(StatusCode.STAT_DETAIL_INIT.value)
            where = "1 order by Fauto_id limit 10000"
            DB_res = self._db.query( field_list, where )
            self._db.commit()
            if not DB_res:
                break
            for item in DB_res:
                mark_detail(self._db, item['Fauto_id'],StatusCode.STAT_DETAIL_IMGSTART.value)
                for img_info in deal_images(item):
                    meta = img_info
                    meta['parse'] = 'parse_detail'  # 标记回调函数
                    request_url = img_info['img_url']
                    if check_url(request_url):
                        yield Request( request_url, headers=self.headers, meta=meta, callback=getattr(self,meta['parse']), dont_filter=False )
                    else:
                        print("request url format error: %s"%(request_url))
    
    # 解析子页面
    def parse_detail(self, response):
        img_info = response.meta
        img_info['img_content'] = response.body
        new_img_url = download_image(img_info)
        img_info['new_img_url'] = new_img_url
        yield self.load_image_item(img_info)
        
    # 构建爬取条目
    def load_image_item(self, img_info):
        data = {
            "Fimage":img_info.get('new_img_url',''),
            "Fauto_id":img_info.get('img_article','')
        }
        item = CsdnImageItem()
        item['row'] = {}
        item['settings'] = csdn_image_item_rule
        item['row'] = data
        return item
        
    # 关闭爬虫时调用
    def closed(self, reason):
        self._db.destroy()
        print("CLOSE_REASON:%s" % reason)

if __name__ == '__main__':
    try:
        runner = CrawlerRunner()
        runner.crawl(CsdnImageSpider)
        d = runner.join()
        d.addBoth(lambda _: reactor.stop())
        reactor.run()
    
    except Exception as e:
        print(traceback.format_exc())