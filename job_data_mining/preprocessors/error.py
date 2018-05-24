#   AUTHOR: Sibyl System
#     DATE: 2018-04-19
#     DESC: error code 
#           for preprocessing

#!/usr/bin/python
# -*- coding: utf-8 -*-

from enum import IntEnum, unique


@unique
class ErrCode(IntEnum):
    ERR_SUCCESS = 0                         # 成功
    ERR_IMAGE_DOWNLOAD_FAILED = -1          # 图片下载失败
    ERR_IMAGE_TOO_SMALL = -2                # 图片太小
    ERR_POST_DATE_EMPTY = -3                # 文章发布日缺失
    ERR_TAG_EXTRACT_FAILED = -4             # 文章标签提取失败


if __name__ == '__main__':

    print(ErrCode.ERR_PARAM.value)
    print(ErrCode.__getitem__('ERR_LOGIC'))
