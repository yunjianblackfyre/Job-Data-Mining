#COPYRIGHT: Tencent flim
#   AUTHOR: zanegao
#     DATE: 2016-08-10
#     DESC: tools

from common.exception import Exc


ERROR_BUSINESS_TYPE            = -2015

#plat_type    1-自编辑；2-豆瓣；3-格瓦拉
#third_id    thirdparty_id第三方平台中电影的id
def get_movieid(plat_type, third_id):
    prefixs=['1000','1001','1002','1003']
    if (plat_type>=0) and (plat_type<len(prefixs)):
        return prefixs[plat_type] + third_id
    else:
        raise Exc(ERROR_BUSINESS_TYPE, 'plat_type param is not support')