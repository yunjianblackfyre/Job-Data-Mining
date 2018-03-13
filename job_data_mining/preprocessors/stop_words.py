'# coding=utf-8'
'''
在不同领域，停止词信息量有轻有重
比如 能 这个词可以当做停止词去掉，然而在
求职信息中，由于智能的词频逐年增多，所以对能字的处理
不仅仅局限于去掉，而增加了替换的需求。

所以处理停止词时，要先通过统计观察得出本领域内
哪些停止词可以直接去掉，哪些需要保留，哪些需要
特殊处理。这是个体力活，残念

提取停止词的标准
停止词通常出现概率高，并且独立性强（很少歧义）
停止词的反词频通常较高，也就是说信息量低

停止正则
停止正则应当放在停止词之前，以实现精准定位

特殊逻辑：
将 智能 替换为 智慧
'''

STOP_PATTERNS = [
    # 正则的或：从左到右（先找'以上'，若木有，找'左右'，还是找不到就匹配）
    '(\d+\W\d+)(年)',
    '(\d+)(年)',
    '([一两二三四五六七八九十多半]+)(年)'
    
]

STOP_WORDS_ENG = [
"a",
"about",
"above",
"after",
"again",
"against",
"all",
"am",
"an",
"and",
"any",
"are",
"arent",
"as",
"at",
"be",
"because",
"been",
"before",
"being",
"below",
"between",
"both",
"but",
"by",
"cant",
"cannot",
"could",
"couldnt",
"did",
"didnt",
"do",
"does",
"doesnt",
"doing",
"dont",
"down",
"during",
"each",
"few",
"for",
"from",
"further",
"had",
"hadnt",
"has",
"hasnt",
"have",
"havent",
"having",
"he",
"hed",
"hell",
"hes",
"her",
"here",
"heres",
"hers",
"herself",
"him",
"himself",
"his",
"how",
"hows",
"i",
"id",
"ill",
"im",
"ive",
"if",
"in",
"into",
"is",
"isnt",
"it",
"its",
"its",
"itself",
"lets",
"me",
"more",
"most",
"mustnt",
"my",
"myself",
"no",
"nor",
"not",
"of",
"off",
"on",
"once",
"only",
"or",
"other",
"ought",
"our",
"ours",
"ourselves",
"out",
"over",
"own",
"same",
"shant",
"she",
"shed",
"shell",
"shes",
"should",
"shouldnt",
"so",
"some",
"such",
"than",
"that",
"thats",
"the",
"their",
"theirs",
"them",
"themselves",
"then",
"there",
"theres",
"these",
"they",
"theyd",
"theyll",
"theyre",
"theyve",
"this",
"those",
"through",
"to",
"too",
"under",
"until",
"up",
"very",
"was",
"wasnt",
"we",
"wed",
"well",
"were",
"weve",
"were",
"werent",
"what",
"whats",
"when",
"whens",
"where",
"wheres",
"which",
"while",
"who",
"whos",
"whom",
"why",
"whys",
"with",
"wont",
"would",
"wouldnt",
"you",
"youd",
"youll",
"youre",
"youve",
"your",
"yours",
"yourself",
"yourselves",
]

STOP_WORDS = [
'各类型',
'能够',
'能力',
'才能',
'不能',
'性能',
'功能',
'技能',
'拥有',
'具有',
'现有',
'已有',
'以及',
'并且',
'或者',
'针对',
'对接',
'对于',
'为人',
'较为',
'作为',
'各类',
'各种',
'各项',
'各组',
'各个',
'以上',
'以下',
'以前',
'以后',
'可以',
'以往',
'如上',
'如下',
'例如',
'诸如',
'整个',
'这个',
'多个',
'有个',
'一个',
'二个',
'两个',
'三个',
'五个',
'六个',
'七个',
'八个',
'九个',
'个大',
'个人',
'我们',
'他们',
'你们',
'一定',
'一种',
'一项',
'一起',
'一门',
'两种',
'两项',
'两起',
'两门',
'基于',
'善于',
'从业',
'从事',
'其他',
'使用',
'日常',
'常用',
'快速',
'基本',
'至少',
'最少',
'的',
'能',
'有',
'和',
'及',
'与',
'且',
'或',
'对',
'等',
'为',
'各',
'以',
'可',
'者',
'如',
'并',
]

if __name__ == '__main__':
    import re
    pattern = STOP_PATTERNS[0]
    test_list = [
        '1-2年以上工作经验',
    ]
    for test_str in test_list:
        for pattern in STOP_PATTERNS:
            test_str = re.sub(pattern, '', test_str)
        print(test_str)
        