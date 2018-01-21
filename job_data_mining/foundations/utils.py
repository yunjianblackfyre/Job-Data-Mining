#   AUTHOR: Sibyl System
#     DATE: 2018-01-01
#     DESC: static methods and variables

import time
import json
import re
import copy
import traceback

# 通用类型转换
def tryconvert(value, default, *types):
    for t in types:
        try:
            if value == None:
                return default
            else:
                return t(value)
        except:
            continue
    return default

int_data_convert = lambda v: tryconvert(v, 0, int)
str_data_convert = lambda v: tryconvert(v, '', str)
time_now = lambda: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

# 全局变量
TYPE_CONVERT_MAP = {
    'str':str_data_convert,
    'int':int_data_convert,
}

# 数据类型默认值
TYPE_DEFAULT_VALUE_MAP = {
    'str':'',
    'int':0,
}

# 通用对象详情打印
def dump_object(obj):
   for attr in dir(obj):
       if hasattr( obj, attr ):
           print( "obj.%s = %s" % (attr, getattr(obj, attr)))
           
# 通用调试组
def print_dict(dict_src):
    for key, value in dict_src.items():
        print(key,':',str(value))
        
def print_list(list_src):
    for item in list_src:
        print(item)

# 通用计时器
class StopWatch(object):

    def __init__(self):
        self.reset()
        
    def get_elapsed_milliseconds(self):
        return "%0.2f"  % ((time.time()-self._start_time)*1000)
    
    def reset(self):
        self._start_time = time.time()