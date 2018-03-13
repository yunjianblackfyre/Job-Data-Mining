Job-Data-Mining
========
招聘信息数据挖掘，致力于从各大求职网站挖掘出有用信息
这些招聘信息来自中国各大互联网：智联、拉勾、51jobs等等

Job-Data-Mining, this project is dedicated to find useful information from jobs posted on varies websites
such as zhilian, lagou, 51jobs and so on.

- _Scroll down for English documentation._

效果说明
========
 对爬取到的招聘信息打标签，并计算标签之间的关联性信息，用于推荐或搜索。大致步骤如下：
 * 爬取元数据，数据基本单元为（职位，职位描述） 
 * 职位描述分词打标签，例如将一则“JAVA工程师招聘：要求...工作地点...”提取出JAVA、后台开发等关键词作为标签
 * 关键词聚类：利用聚类算法将关联紧密的标签聚成一类，如下：
   AI大数据类（服务器、机器学习、大数据、推荐系统）
   产品经理类（产品设计、视觉设计、交流能力、市场分析） 
 在取得了这些分类后，推荐系统和搜索引擎可以获得更好的智能效果。

环境搭建流程
=======
* 对个人用户来说，建议使用ubuntu系统，可以大幅度简化安装。不建议用centos
* 本人系统信息:Linux ubuntu 4.13.0-26-generic #29~16.04.2-Ubuntu SMP Tue Jan 9 22:00:44 UTC 2018 x86_64 x86_64 x86_64 GNU/Linux

* 安装python3：
    * sudo apt-get install python3
    * sudo apt-get install python3-pip pip3用于简易安装python第三方

* 安装mysql服务器，客户端
    * sudo apt-get install mysql-server
    * sudo apt-get isntall mysql-client
    * sudo apt-get install libmysqlclient-dev

* 安装python3第三方
    * pip3 install mysql-connector-python python的mysql客户端
    * pip3 install scrapy # 高并发爬虫框架
    * pip3 install gensim # 主题模型

* 创建开发目录
    * 用$username指代用户名
    * 将JOB-DATA-MINING文件夹拷贝至/home/$username/下

* 将工程文件加入环境变量
    * 在当前用户的根目录下的.bashrc文件最后行加入
    * export PYTHONPATH=:/home/$username/JOB-DATA-MINING/job_data_mining
    * 执行source .bashrc使之生效
    * 可用 echo $PYTHONPATH 确定./bashrc是否生效
    
* 安装结巴分词器
    * https://github.com/fxsjy/jieba处下载结巴工程
    * 将jieba-master下的jieba文件夹放置于job-data-mining目录下

系统组成
========
* 采用Scrapy框架爬取数据。亮点：Scrapy经过进一步封装，解析与入库逻辑可配置，减少用户开发量
* 关键词提取采用SNS挖掘方法提取新词，将提取的新词加入结巴词库，随后采用结巴分词器进行分词
* 主题提取采用LDA或者Word2Vector方法（如果使用Word2Vector,则需要用户提供聚类逻辑，比如Kmeans）

自定义爬虫
========
* 该爬虫框架有三部分需要用户自定义，如果用户需要爬取其他网站
   第一：解析路径（css）与爬取结构化化数据（python dict）
   第二：爬取结构化数据转化为入库结构化数据的解析方法（根据本人的爬虫经验，解析到的数据通常需要过滤清洗后方能入库）
   第三：入库结构化数据（python dict）
   
* 如果用户希望用爬虫爬取其他网站，只需要调整少量程序即可实现。
    * 在/job_data_mining/crawlers/config.py文件夹下，可以调整入库规则和网站解析规则
        * 智联招聘：页面信息解析规则
            ```python
            # encoding=utf-8
            zhilian_task_parse_rule = {
                'fields':{
                    #'Fmain':'#search_jobtype_tag > a'
                },
                'children_path':'#newlist_list_content_table > table',
                'children':
                {
                    'fields':{
                        'Ftask_url':'td.zwmc > div > a::attr(href)',
                        'Ftask_name':'td.zwmc > div > a'
                    }
                },
                'page_next':'li.pagesDown-pos > a::attr(href)'
            }
            ```
        * fields标记了在本页面需要爬取的单一元素
        * children_path标记了本页面需要爬取的列表
        * parse_html方法接受zhilian_task_parse_rule作为爬取规则，输出一个dict列表作为元数据
        * 用户可以在请求的回调解析方法内自定义处理元数据的方法
            
    * 用户可以自定义scrapy爬取item的数据结构
        * 熟悉scrapy的开发人员都知道，scrapy有item类，用于数据库的入库
        通常item类直接用于存储数据库表的一行数据。但是人们有时会需要
        预处理数据行的数据，并且每种item入库的逻辑都有所不同。
        所以为了满足通用化，在此，item存储三种信息
        * 1.数据行：item['row']
        * 2.数据行入库规则：item['settings']
        * 3.数据行预处理器：item.row_builder
        * 对于1，用户完全自定义
        * 对于2，我们有配置信息：
            ```python
            # encoding=utf-8
            zhilian_task_item_rule = {
                'item_format':{
                    'Fcategory':{'type':'str','req':True,'dup':False},
                    'Ftask_url':{'type':'str','req':True,'dup':True}
                },
                'item_db':'db_job',
                'item_table':'t_zhilian_task',
                'write_table_method':'update', # 方法为更新（另外还有条件insert和无条件insert）
            }
            ```
        * item_format为数据库行格式，Fcategory为字段名，str为字段类型，req:True表示此字段必须有值（非默认值），
        * dup:False表示Fcategory为非unique index
        * item_db与item_table分别代表了该条目所属的库名和表名
        * write_table_method:update表示入库方式为有条件插入，即插入前用Ftask_url查一下，如果有重复条目，则不插入
        * 对于3，我们可以重写row_builder.build_row_from_custom方法来自定义预处理逻辑，该方法的重写在zhilian_task_spider.py中可以找到样例
            
新词提取算法
========
* 新词提取采用了SNS数据挖掘法，通过计算所有可能词的自由度与凝固度，选取自由度与凝固度高的词作为新词
    * 算法示例：原文章为“至少3年工作经验，熟悉spark大数据，了解数据挖掘，精通数据分析”
    * Ffree('数据')= min(-1/3*log(1/3) -1/3*log(1/3) -1/3*log(1/3),-1/2*log(1/2)-1/2*log(1/2)) （左词列表['大','解','通']，右词列表['挖','析']）
    * Fsld('数据')=P('数据')/P('数')P('据')
    * 算法原理详细解释：http://www.matrix67.com/blog/archives/5044
    * 新词提取的结果示例：（左边为词，右边为词频）
    * "Web移动端": 30,
      "信号处理": 1599,
      "OpenStack云平台": 9,
      "设备控制": 145,
      "用户增长": 9,
      "开源代码": 288,
      "输入法": 78,
      "毕业证": 117,
      "设备监控": 15,
      "小程序": 1451,
      "信息安全": 1819,
      "企业网站": 116,
      "网站搭建": 59,
      "Windows内核": 39,
      "PB开发": 11,
      "规划设计": 1374,
      "动态效果": 315,
      "主导项目": 124,
      "路径规划": 222,
      "高德": 122,
      "多通道": 15,
      "实时通信": 7,
      "承担责任": 44,
      "运营部门": 185,
      "入职": 29481,
      "独立思考": 1715,
      "直属上级": 9,
      "页面美工": 40,
      "时代广场": 408,
      "无基础": 2705,
      "基础理论": 297,
      "测试计划": 2478,
      "PHP工程师": 116,
      "社会保险": 1320,
      "数据访问": 124,
      "升职加薪": 13,
      "美国总部": 7,
      "制作流程": 971,
      "产品介绍": 92,
      "推广效果": 16,
      "数据加工": 20,
      "地铁站": 3421,
      "同时在线": 18,
      "回国": 50,
      "主流报表": 7,
      "代码优化": 201,
      "配置优化": 386,
      "负责移动": 361,
      "插画": 235,
      "团队意识": 6920,
      "汇编": 1241,
      "独立部署": 30,
      "提供完善": 1089,
      "市场拓展": 32,
      "绘图软件": 346,
        
--------未完待续--------
