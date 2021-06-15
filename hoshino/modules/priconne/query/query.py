import itertools
from hoshino import util, R
from hoshino.typing import CQEvent
from . import sv


@sv.on_rex(r'^jjc((作业(网)?)|数据库)?$')
async def say_arina_database(bot, ev):
    await bot.send(ev, '''公主连接Re:Dive 竞技场编成数据库
日文：https://nomae.net/arenadb
中文：https://pcrdfans.com/battle''')


OTHER_KEYWORDS = '''【日rank】【台rank】【b服rank】【jjc作业网】
【黄骑充电表】【一个顶俩】【多目标boss机制】【pcr公式】'''
PCR_SITES = f'''
【繁中wiki/兰德索尔图书馆】pcredivewiki.tw
【体力规划工具/可可萝笔记】https://kokkoro-notes.lolita.id/#
【刷图规划工具/quest-helper】https://expugn.github.io/priconne-quest-helper/
【日文wiki/GameWith】gamewith.jp/pricone-re
【日文wiki/AppMedia】appmedia.jp/priconne-redive
【竞技场作业库(中文)】pcrdfans.com/battle
【竞技场作业库(日文)】nomae.net/arenadb
【论坛/NGA社区】bbs.nga.cn/thread.php?fid=-10308342
【iOS实用工具/初音笔记】bbs.nga.cn/read.php?tid=14878762
【安卓实用工具/静流笔记】bbs.nga.cn/read.php?tid=20499613
【台服卡池千里眼】bbs.nga.cn/read.php?tid=16986067
【日官网】priconne-redive.jp
【台官网】www.princessconnect.so-net.tw
【pcr美术资源】https://redive.estertion.win/
【pc美术资源】priconestory.nekonikoban.org

===其他查询关键词===
{OTHER_KEYWORDS}
※B服速查请输入【bcr速查】'''

BCR_SITES = f'''
【妈宝骑士攻略(懒人攻略合集)】bbs.nga.cn/read.php?tid=20980776
【机制详解】bbs.nga.cn/read.php?tid=19104807
【初始推荐】bbs.nga.cn/read.php?tid=20789582
【术语黑话】bbs.nga.cn/read.php?tid=18422680
【角色点评】bbs.nga.cn/read.php?tid=20804052
【秘石规划】bbs.nga.cn/read.php?tid=20101864
【卡池亿里眼】bbs.nga.cn/read.php?tid=20816796
【为何卡R卡星】bbs.nga.cn/read.php?tid=20732035
【推图阵容推荐】bbs.nga.cn/read.php?tid=21010038

===其他查询关键词===
{OTHER_KEYWORDS}
※日台服速查请输入【pcr速查】'''


@sv.on_fullmatch('pcr速查', 'pcr图书馆', '图书馆')
async def pcr_sites(bot, ev: CQEvent):
    await bot.send(ev, PCR_SITES, at_sender=True)
    await util.silence(ev, 60)


@sv.on_fullmatch('bcr速查', 'bcr攻略')
async def bcr_sites(bot, ev: CQEvent):
    await bot.send(ev, BCR_SITES, at_sender=True)
    await util.silence(ev, 60)


@sv.on_rex(r'^(兰德索尔|pcr)?(年龄|胸围|学业|胸部|岁数|欧派|大小)(统计|分布|表)表?$', only_to_me=True)
async def pcrfenbubiao(bot, ev):
    match = ev['match']
    is_n = match.group(2) in '年龄岁数'
    is_x = match.group(2) in '胸围胸部欧派大小'
    is_s = match.group(2) == '学业'
    if is_n:
        await bot.send(ev, R.img('priconne/tips/pcrnianlingbiao.jpg').cqcode)
    elif is_x:
        await bot.send(ev, R.img('priconne/tips/xiongwei.png').cqcode)
    elif is_s:
        await bot.send(ev, R.img('priconne/tips/xueniantuice.jpg').cqcode)


@sv.on_fullmatch(('furry', 'furry分级', '喜欢羊驼很怪吗', '喜欢羊驼有多怪'), only_to_me=True)
async def furryrank(bot, ev):
    await bot.send(ev, R.img('priconne/tips/furry.jpg').cqcode)


YUKARI_SHEET_ALIAS = map(lambda x: ''.join(x), itertools.product(
    ('黄骑', '酒鬼'), ('充电', '充电表', '充能', '充能表')))
YUKARI_SHEET = f'''
{R.img('priconne/quick/黄骑充电.jpg').cqcode}
※大圈是1动充电对象 PvP测试
※黄骑四号位例外较多
※对面羊驼或中后卫坦 有可能歪
※我方羊驼算一号位
※图片搬运自漪夢奈特'''


@sv.on_fullmatch(YUKARI_SHEET_ALIAS)
async def yukari_sheet(bot, ev):
    await bot.send(ev, YUKARI_SHEET, at_sender=True)
    await util.silence(ev, 60)


DRAGON_TOOL = f'''
拼音对照表：{R.img('priconne/KyaruMiniGame/注音文字.jpg').cqcode}{R.img('priconne/KyaruMiniGame/接龙.jpg').cqcode}
龍的探索者們小遊戲單字表 https://hanshino.nctu.me/online/KyaruMiniGame
镜像 https://hoshino.monster/KyaruMiniGame
网站内有全词条和搜索，或需科学上网'''


@sv.on_fullmatch('一个顶俩', '拼音接龙', '韵母接龙')
async def dragon(bot, ev):
    await bot.send(ev, DRAGON_TOOL, at_sender=True)
    await util.silence(ev, 60)


Duomubiao = R.data('priconne/query/duomubiao.json', 'json')
Duomubiaopic = R.img('priconne/tips/duomubiao.jpg').cqcode


@sv.on_fullmatch(('多目标boss机制文字'), only_to_me=True)
async def duomubiao(bot, ev):
    msg = Duomubiao.read
    await bot.send(ev, '\n'.join(msg), at_sender=True)
    await util.silence(ev, 60*5)


Duomubiaourl = f'''
{Duomubiaopic}
原文来自https://ngabbs.com/read.php?tid=18623761
不想看图不想开浏览器不怕刷屏也可以发送#多目标boss机制文字
===其他查询关键词===
{OTHER_KEYWORDS}
※日台服速查请输入【pcr速查】'''


@sv.on_fullmatch(('多目标boss机制', '多目标boss'), only_to_me=True)
async def duomubiaourl(bot, ev):
    await bot.send(ev, Duomubiaourl, at_sender=True)


otherk = [
    "===其他查询关键词===",
    f"{OTHER_KEYWORDS}",
    "※日台服速查请输入【pcr速查】"]

pcrFORMULA = R.data('priconne/query/FORMULA.json', 'json')


@sv.on_prefix(('pcr公式'), only_to_me=True)
async def pcrgongshi(bot, ev):
    keyword = ev.message.extract_plain_text()
    if not keyword:
        msg = pcrFORMULA.read["pcrFORMULA"]['pcrgshelp'] + otherk
        await bot.send(ev, '\n'.join(msg), at_sender=True)
    else:
        msg = pcrFORMULA.read["pcrFORMULA"].get(keyword)
        if msg is not None:
            msg = '\n'.join(msg)
            await bot.send(ev, msg)
        else:
            pass
