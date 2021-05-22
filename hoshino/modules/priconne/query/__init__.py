from hoshino import Service

sv_help = '''
[pcr速查] 常用网址/图书馆
[bcr速查] B服萌新攻略
[挖矿15001] 矿场余钻
[#pcr公式] pcr的各种计算公式
[#年龄/胸部/学业分布表] 各种数据的分布表
[#furry分级] 喜欢羊驼到底有多怪
[黄骑充电表] 黄骑1动规律
[一个顶俩] 台服接龙小游戏
[谁是霸瞳] 角色别称查询
[#多目标boss机制] 看看多目标boss的机制
'''.strip()

sv = Service('pcr-query', help_=sv_help, bundle='pcr查询')

from .query import *
from .whois import *
from .miner import *
from .rank import *
