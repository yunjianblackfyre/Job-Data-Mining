# coding=utf-8
import requests
import sys
import hashlib
import urllib
from io import BytesIO
from PIL import Image
from common.upload_pic_handle import CUploadPicHttpHandle
from common.log import *

# 超时时间和重试次数
TIMEOUT = 5
RETRY_TIME = 2
# 请求重试装饰器
def retry(retry_time):
    def decorator(func):
        def wrapper(*args, **kwargs):
            count = 0
            while count <= retry_time:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    count += 1
                    log_error(e)
                    return
        return wrapper
    return decorator

class Image_tool():
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:46.0) Gecko/20100101 Firefox/51.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh,zh-HK;q=0.8,zh-CN;q=0.7,en-US;q=0.5,en;q=0.3,el;q=0.2',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'DNT': '1',
    }
    __default_url = 'https://p.qpic.cn/wyp_pic/duc2TvpEgSR8ZLHHOK1GVYNvdGjd9e5lTBicwcKpqnuqN0udOs08TnMu3PeuFPND9'

    def __init__(self):
        self.headers = self.HEADERS

    # 重新设置headers
    def reset_headers(self, headers):
        self.headers = headers

    # cdn的默认图片
    @classmethod
    def get_default_url(cls):
        return cls.__default_url

    @retry(RETRY_TIME)
    def download_img(self, url):
        url_info = list(urllib.parse.urlparse(url))
        url_domain = url_info[1]
        self.headers['Host'] = url_domain
        res = requests.get(url, headers=self.headers)
        img = BytesIO()
        img.write(res.content)
        return img

    # 将读取到的文件内容转换成文件流
    def img2stream(self, content):
        img = BytesIO()
        img.write(content)
        return img

    # 转换图片为统一格式
    def convert_img(self, image):
        try:
            img = Image.open(image)
        except Exception as e:
            log_error(e)
            return image
        if img.format != 'JPEG':
            if img.mode != 'RGB':
                img = img.convert(mode='RGB')
            image = BytesIO()
            img.save(image, format='JPEG')
        return image

    # 压缩图片大小
    def press_img(self, image):
        size = sys.getsizeof(image.getvalue())
        # 大于512K的图片进行等比例压缩
        if size < 512*1024:
            return image

        try:
            img = Image.open(image)
        except Exception as e:
            log_error(e)
            return image
        width, height = img.size
        new_width = 1080
        new_height = 1920
        new_img = BytesIO()
        if width > new_width and height > new_height:
            if width <= height:
                new_height = int(new_width * height / width)
            else:
                new_width = int(new_height * width / height)
            img = img.resize((new_width, new_height), Image.ANTIALIAS)
            img.save(new_img, 'JPEG')
        else:
            img = img.resize((width, height), Image.ANTIALIAS)
            img.save(new_img, 'JPEG')
        return new_img

    # 将图片上传到CDN
    def upload_img(self, identity, img, default):
        dsturl = default
        try:
            content = img.getvalue()
            data = {'pic_id': identity, 'data': content}
            op = CUploadPicHttpHandle(data)
            tmp = op.process()
            log_debug("cdn return info is: %s" % str(tmp))
            if tmp[0] == 0:
                dsturl = tmp[1]
        except Exception as e:
            log_debug("uploadimg error is %s" % e)
            return dsturl

        pos = dsturl.find(':')
        if pos != -1:
            dsturl = "https" + (dsturl[pos:len(dsturl)]).strip()
        return dsturl

    # 合并以上步骤提供的接口
    def convert_cdn_url(self, url, default=None):
        """ default为cdn上传失败默认返回(现在失败默认返回原地址)
        """
        default = url if default is None else default

        img = self.download_img(url)
        # 图片下载失败返回原地址
        if img is None:
            log_debug('Raw image url: %s' % url)
            return url
            # return self.__default_url
        img = self.convert_img(img)
        img = self.press_img(img)
        identity = self.str2md5(url)
        cdn_url = self.upload_img(identity, img, default)
        log_debug('Image identity: %s' % (identity))
        log_debug('Raw image url: %s, Converted image url: %s' % (url, cdn_url))
        return cdn_url

    # 已下载图片文件流上传转换CDN地址
    def img_convert_cdn_url(self, url, content, default=None):
        """ default为cdn上传失败默认返回(现在失败默认返回原地址)
        """
        default = url if default is None else default
        img = self.img2stream(content)
        # 图片下载失败返回原地址
        if img is None:
            log_debug('Raw image url: %s' % url)
            return url
            # return self.__default_url
        img = self.convert_img(img)
        img = self.press_img(img)
        identity = self.str2md5(url)
        cdn_url = self.upload_img(identity, img, default)
        log_debug('Image identity: %s' % (identity))
        log_debug('Raw image url: %s, Converted image url: %s' % (url, cdn_url))
        return cdn_url

    # 字符串转md5
    def str2md5(self, url):
        m = hashlib.md5()
        m.update(url.encode('utf-8'))
        return m.hexdigest()


if __name__ == '__main__':
    Image_tool.get_default_url()