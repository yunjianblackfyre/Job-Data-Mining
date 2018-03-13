#COPYRIGHT: Tencent flim
#   AUTHOR: SIBYL SYSTEM
#     DATE: 2016-07-19
#     DESC: crawler utils

# 智联招聘，任务入库
zhilian_task_item_rule = {
    'item_format':{
        'Fcategory':{'type':'str','req':True,'dup':False},
        'Ftask_url':{'type':'str','req':True,'dup':True} # 以任务的URL为基准进行UPDATE
    },
    'item_db':'db_job',
    'item_table':'t_zhilian_task',
    'write_table_method':'update', # 方法为更新（另外还有条件insert和无条件insert）
}

# 智联招聘，职位搜索首页，职位菜单爬取规则
zhilian_menu_parse_rule = {
    'fields':{
        #'Fmain':'#search_jobtype_tag > a' # 如果是列表，就只会提取列表的第一个元素
    },
    'children_path':'#search_jobtype_tag > a',   # 此处必须提取多个元素
    'children':
    {
        'fields':{
            'Fmenu_url':'a::attr(href)', # 如果是列表，就只会提取列表的第一个元素
            'Fmenu_name':'a'
        }
    }
}

# 智联招聘，职位搜索首页，任务爬取规则
zhilian_task_parse_rule = {
    'fields':{
        #'Fmain':'#search_jobtype_tag > a' # 如果是列表，就只会提取列表的第一个元素
    },
    'children_path':'#newlist_list_content_table > table',   # 此处必须提取多个元素
    'children':
    {
        'fields':{
            'Ftask_url':'td.zwmc > div > a::attr(href)', # 如果是列表，就只会提取列表的第一个元素
            'Ftask_name':'td.zwmc > div > a'
        }
    },
    'page_next':'li.pagesDown-pos > a::attr(href)'
}

zhilian_detail_item_rule = {
    'item_format':{
        'Fjob_title':       {'type':'str','req':True,'dup':False},
        'Fjob_salary':      {'type':'str','req':False,'dup':False},
        'Fjob_pubdate':     {'type':'str','req':False,'dup':False},
        'Fjob_experience':  {'type':'str','req':False,'dup':False},
        'Fjob_count':       {'type':'str','req':False,'dup':False},
        'Fjob_location':    {'type':'str','req':False,'dup':False},
        'Fjob_type':        {'type':'str','req':False,'dup':False},
        'Fjob_minreq':      {'type':'str','req':False,'dup':False},
        'Fjob_name':        {'type':'str','req':True,'dup':False},
        'Fjob_url':         {'type':'str','req':True,'dup':True},
        'Fjob_summary':     {'type':'str','req':True,'dup':False},
        
        'Fcorp_name':       {'type':'str','req':False,'dup':False},
        'Fcorp_size':       {'type':'str','req':False,'dup':False},
        'Fcorp_type':       {'type':'str','req':False,'dup':False},
        'Fcorp_category':   {'type':'str','req':False,'dup':False},
        'Fcorp_url':        {'type':'str','req':False,'dup':False},
        'Fcorp_location':   {'type':'str','req':False,'dup':False},
        'Fcorp_summary':    {'type':'str','req':False,'dup':False}
    },
    'item_db':'db_job',
    'item_table':'t_zhilian_detail',
    'write_table_method':'update', # 方法为更新（另外还有条件insert和无条件insert）
}

# 智联详情页爬取
zhilian_detail_parse_rule = {
    'fields':{
        'Fjob_title':       'div.fixed-inner-box > div.inner-left.fl > h1',
        'Fjob_salary':      'div.terminalpage.clearfix > div.terminalpage-left > ul > li:nth-child(1) > strong',
        'Fjob_pubdate':     'div.terminalpage.clearfix > div.terminalpage-left > ul > li:nth-child(3) > strong',
        'Fjob_experience':  'div.terminalpage.clearfix > div.terminalpage-left > ul > li:nth-child(5) > strong',
        'Fjob_count':       'div.terminalpage.clearfix > div.terminalpage-left > ul > li:nth-child(7) > strong',
        'Fjob_location':    'div.terminalpage.clearfix > div.terminalpage-left > ul > li:nth-child(2) > strong',
        'Fjob_type':        'div.terminalpage.clearfix > div.terminalpage-left > ul > li:nth-child(4) > strong',
        'Fjob_minreq':      'div.terminalpage.clearfix > div.terminalpage-left > ul > li:nth-child(6) > strong',
        'Fjob_name':        'div.terminalpage.clearfix > div.terminalpage-left > ul > li:nth-child(8) > strong',
        'Fjob_summary':     'div.terminalpage.clearfix > div.terminalpage-left > div.terminalpage-main.clearfix > div > div:nth-child(1)',
        
        'Fcorp_name':       'div.terminalpage.clearfix > div.terminalpage-right > div.company-box > p > a',
        'Fcorp_info':       'div.terminalpage.clearfix > div.terminalpage-right > div.company-box > ul',    # 之后拆分至各种字段
        'Fcorp_summary'     :'div.terminalpage.clearfix > div.terminalpage-left > div.terminalpage-main.clearfix > div > div:nth-child(2)'
    }
}

# 智联招聘，任务入库
vijob_task_item_rule = {
    'item_format':{
        'Fcategory':{'type':'str','req':True,'dup':False},
        'Ftask_url':{'type':'str','req':True,'dup':True} # 以任务的URL为基准进行UPDATE
    },
    'item_db':'db_job',
    'item_table':'t_vijob_task',
    'write_table_method':'update', # 方法为更新（另外还有条件insert和无条件insert）
}

# 智联招聘，职位搜索首页，任务爬取规则
vijob_task_parse_rule = {
    'fields':{
        #'Fmain':'#search_jobtype_tag > a' # 如果是列表，就只会提取列表的第一个元素
    },
    'children_path':'#resultList > div',   # 此处必须提取多个元素
    'children':
    {
        'fields':{
            'Ftask_url':'div.el > p > span > a::attr(href)', # 如果是列表，就只会提取列表的第一个元素
            'Ftask_name':'div.el > p > span > a'
        }
    },
    'page_next':'#resultList > div.dw_page > div > div > div > ul > li.bk > a'
}