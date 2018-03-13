#COPYRIGHT: Tencent flim
#   AUTHOR: SIBYL SYSTEM
#     DATE: 2016-07-19
#     DESC: crawler utils

import html
from foundations.utils import *
from urllib.parse import urlparse
from urllib.parse import parse_qsl
from urllib.parse import urljoin
from scrapy.selector import Selector
from scrapy.http.cookies import CookieJar

# 任务状态码
TASK_STATE = {
    'init': 1,
    'downloading': 2,
    'failure': 3,
    'down_succ': 4,
    'exception': 5,
    'fetch_fail': 6,
    'fetch_succ': 7,
    'mix_succ': 8
}

# 宏
html_unescape = lambda v: html.unescape(v)

# 从返回对象中提取出完整的cookie字符串
def cookie_from_jar(response):
    cookie_jar = response.meta['cookiejar']
    cookie_jar.extract_cookies(response, response.request)
    cookie_string_list = []
    for cookie in cookie_jar:
        # dump_object(cookie)
        cookie_string = '='.join([cookie.name, cookie.value])
        cookie_string_list.append(cookie_string)
    cookie_res_string = ';'.join(cookie_string_list)
    return cookie_res_string

# 清理HTML标签
def clean_html(element):
    # element = ''.join(element.split())
    element = html_unescape(element)
    element = re.sub('<[^<>]+>','\n',element)
    element = element.strip()
    return element

# 通用HTML解析方法
# PARAMS 1.parse_rule 解析规则，类型为JSON
#        2.content_sel 网页存储器，类型为Selector
#        3.row 数据行存储器，类型为dict
#        4.row_list 最终数据存储器，类型为list
def parse_html(parse_rule, content_sel, row, row_list, pn_url_list):
    # 参数检测
    if not ( isinstance(parse_rule, dict) and isinstance(content_sel, Selector) ):
        print("parse_rule or content_sel type error")
        raise TypeError
        
    # 初始化变量
    fields = parse_rule.get('fields',{})
    children_path = parse_rule.get('children_path','')
    children = parse_rule.get('children',{})
    sel_list = []
    
    # 变量类型检测
    if not ( 
             isinstance(fields, dict) and 
             isinstance(children_path, str) and 
             isinstance(children, dict) 
           ):
        print("variables type error")
        raise TypeError
    
    # 开始提取字段信息
    for key, value in fields.items():
        try:
            row[key] = clean_html( content_sel.css(value).extract()[0] )
        except Exception as e:
            print('field extraction failed, %s, path %s'%(str(e),value) )
            row[key] = str(e)
            
    # 判断是否为叶节点
    if not children_path:
        new_row = copy.deepcopy(row)
        row_list.append(new_row)
        return
            
    # 开始提取子叶列表
    try:
        sel_list = content_sel.css(children_path)
    except Exception as e:
        print('children extraction failed, %s, path %s'%(str(e)),children_path )
        
    # 开始提取下一页URL
    
    if parse_rule.get('page_next'):
        path = parse_rule['page_next']
        try:
            pn_url_list.extend( content_sel.css(path).extract())
        except:
            print('next page url extraction failed')
    
    # 进入子叶作为下一个节点递归
    for sel in sel_list:
        parse_html(children, sel, row, row_list, pn_url_list)
        
if __name__ == '__main__':
    mystring = "<body>hahaha<div>hehehe</div>xixi</body>"
    print( clean_html(mystring) )
    pass