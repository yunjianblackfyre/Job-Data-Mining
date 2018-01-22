Job-Data-Mining
========
招聘信息数据挖掘，致力于从各大求职网站挖掘出有用信息
这些招聘信息来自中国各大互联网：智联、拉勾、51jobs等等

Job-Data-Mining, this project is dedicated to find useful information from jobs posted on varies websites
such as zhilian, lagou, 51jobs and so on.

- _Scroll down for English documentation._

效果说明
========
 * 爬取元数据：职位1：数据工程师   职位2：AI工程师   职位3：后台开发工程师   职位4：产品经理   职位5：产品销售 
 * 职位聚类：互联网后台类（职位1，职位2，职位3）业务类（职位4，职位5）
 * 关键词聚类：互联网后台类（服务器、机器学习、大数据、推荐系统）业务类（产品设计、视觉设计、交流能力、市场分析） 
 * 本项目预期效果：任何求职者能够通过聚类找到自己理想工作所属类别，并利用技能关键词了解技能要求，最优化分配自己的学习资源


基础环境搭建流程
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

* 建立数据库
    * 用$password指代mysql密码
    * shell指令执行：
      mysql -uroot -ppassword < /home/$username/JOB-DATA-MINING/sql_files/zhilian_tables.sql

过程方法
========
* 采用Scrapy框架爬取数据，解析与入库逻辑可配置，用户不需要深度参与爬虫开发
* 关键词提取采用SNS挖掘方法提取新词，随后采用结巴分词器进行分词
* 主题提取采用LDA或者Word2Vect方法

自定义爬虫
========
如果用户希望用爬虫爬取其他网站，只需要调整少量程序即可实现。
（假定用户熟悉scrapy框架）
需要调整的地方如下：
    * /job_data_mining/crawlers/config.py文件夹下，可以调整入库规则和网站解析规则
        * 调整说明：
            智联招聘：页面信息解析规则
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
            fields标记了在本页面需要爬取的单一元素
            children_path标记了本页面需要爬取的列表
            parse_html方法接受zhilian_task_parse_rule作为爬取规则，输出一个dict列表作为元数据
            用户可以在请求的回调解析方法内自定义处理元数据的方法
            
    * 用户可以自定义scrapy爬取item的数据结构
        * 调整说明：
            熟悉scrapy的开发人员都知道，scrapy有item类，用于数据库的入库
            通常item类直接用于存储数据库表的一行数据。但是人们有时会需要
            预处理数据行的数据，并且每种item入库的逻辑都有所不同。
            所以为了满足通用化，在此，item存储三种信息
            1.数据行：item['row']
            2.数据行入库规则：item['settings']
            3.数据行预处理器：item.row_builder
            对于1，用户完全自定义
            对于2，我们有配置信息：
                zhilian_task_item_rule = {
                    'item_format':{
                        'Fcategory':{'type':'str','req':True,'dup':False},
                        'Ftask_url':{'type':'str','req':True,'dup':True}
                    },
                    'item_db':'db_job',
                    'item_table':'t_zhilian_task',
                    'write_table_method':'update', # 方法为更新（另外还有条件insert和无条件insert）
                }
                item_format为数据库行格式，Fcategory为字段名，str为字段类型，req:True表示此字段必须有值（非默认值），
                dup:False表示Fcategory为非unique index
                item_db与item_table分别代表了该条目所属的库名和表名
                write_table_method:update表示入库方式为有条件插入，即插入前用Ftask_url查一下，如果有重复条目，则不插入
            对于3，我们可以重写row_builder.build_row_from_custom方法来自定义预处理逻辑，该方法的重写在zhilian_task_spider.py中可以找到样例
            
新词提取算法
========
新词提取采用了SNS数据挖掘法，通过计算所有可能词的自由度与凝固度，选取自由度与凝固度高的词作为新词
算法示例：原文章为“至少3年工作经验，熟悉spark大数据，了解数据挖掘，精通数据分析”
    * Ffree('数据')= min(-1/3*log(1/3) -1/3*log(1/3) -1/3*log(1/3),-1/2*log(1/2)-1/2*log(1/2)) （左词列表['大','解','通']，右词列表['挖','析']）
    * Fsld('数据')=P('数据')/P('数')P('据')
    算法原理详细解释：http://www.matrix67.com/blog/archives/5044
    新词提取的结果示例：（左边为词，右边为词频）
        "Web移动端": 30,
        "老板": 370,
        "信号处理": 1599,
        "OpenStack云平台": 9,
        "设备控制": 145,
        "用户增长": 9,
        "开源代码": 288,
        "输入法": 78,
        "毕业证": 117,
        "实际问题": 103,
        "设备监控": 15,
        "家园": 152,
        "小程序": 1451,
        "信息安全": 1819,
        "企业网站": 116,
        "网站搭建": 59,
        "量身定做": 6,
        "Windows内核": 39,
        "岛内": 21,
        "大道南号": 16,
        "熟悉网络": 693,
        "PB开发": 11,
        "规划设计": 1374,
        "动态效果": 315,
        "主导项目": 124,
        "路径规划": 222,
        "组内人员": 9,
        "高德": 122,
        "多通道": 15,
        "实时通信": 7,
        "承担责任": 44,
        "企业中心": 39,
        "行性方案": 14,
        "运营部门": 185,
        "入职": 29481,
        "提供作品": 228,
        "独立思考": 1715,
        "直属上级": 9,
        "免费员工": 65,
        "页面美工": 40,
        "时代广场": 408,
        "全部部分": 8,
        "修改": 7717,
        "过程中": 15405,
        "同类": 992,
        "无基础": 2705,
        "基础理论": 297,
        "号楼二层": 56,
        "测试计划": 2478,
        "集团旗下": 131,
        "指引": 180,
        "PHP工程师": 116,
        "社会保险": 1320,
        "数据访问": 124,
        "升职加薪": 13,
        "美国总部": 7,
        "端后台": 176,
        "本公司是": 70,
        "类院校": 71,
        "制作流程": 971,
        "电话": 15704,
        "产品介绍": 92,
        "推广效果": 16,
        "读性": 154,
        "你将": 771,
        "代表": 457,
        "数据加工": 20,
        "地铁站": 3421,
        "控制": 16544,
        "型企业": 160,
        "同时在线": 18,
        "回国": 50,
        "主流报表": 7,
        "代码优化": 201,
        "额外": 3142,
        "配置优化": 386,
        "区海泰": 216,
        "赛事": 89,
        "负责移动": 361,
        "插画": 235,
        "前台技术": 28,
        "四川": 1074,
        "享受": 25461,
        "团队意识": 6920,
        "汇编": 1241,
        "独立部署": 30,
        "提供完善": 1089,
        "市场拓展": 32,
        "绘图软件": 346,
        
--------未完待续--------
