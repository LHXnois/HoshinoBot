import os
import random

from nonebot.exceptions import CQHttpError

from hoshino import R, Service, priv
from hoshino.util import FreqLimiter, DailyNumberLimiter

_max = 5
EXCEED_NOTICE = f'您今天已经冲过{_max}次了，请明早5点后再来！'
_nlmt = DailyNumberLimiter(_max)
_flmt = FreqLimiter(5)

sv = Service('findold', manage_priv=priv.SUPERUSER,
             enable_on_default=True, help_='''考 古 发 现
取自一位一般互联网用户的qq图片文件夹）
涩图:沙雕图:表情包=8:1:1
[#考古] 从历史中扒拉一张图
ps：加数字可一次取多张，最多5 如#考古5''', bundle='setu')
setu_folder = R.img('setu/').path


def setu_gener(folder=''):
    while True:
        filelist = os.listdir(os.path.join(setu_folder, folder))
        random.shuffle(filelist)
        for filename in filelist:
            if os.path.isfile(os.path.join(setu_folder, folder, filename)):
                yield R.img(f'setu/{folder}', filename)


# defaultsetu_gener = setu_gener()
old_gener = setu_gener('oldimgs')


''' def get_setu():
    return defaultsetu_gener.__next__() '''


def find_old():
    return old_gener.__next__()


''' #@sv.on_rex(r'不够[涩瑟色]|[涩瑟色]图|来一?[点份张].*[涩瑟色]|再来[点份张]|看过了|铜')
async def setu(bot, ev):
    """随机叫一份涩图，对每个用户有冷却时间"""
    uid = ev['user_id']
    if not _nlmt.check(uid):
        await bot.send(ev, EXCEED_NOTICE, at_sender=True)
        return
    if not _flmt.check(uid):
        await bot.send(ev, '您冲得太快了，请稍候再冲', at_sender=True)
        return
    _flmt.start_cd(uid)
    _nlmt.increase(uid)

    # conditions all ok, send a setu.
    pic = get_setu()
    try:
        await bot.send(ev, pic.cqcode)
    except CQHttpError:
        sv.logger.error(f"发送图片{pic.path}失败")
        try:
            await bot.send(ev, '涩图太涩，发不出去勒...')
        except Exception:
            pass '''

@sv.on_prefix('考古')
async def find_olds(bot, ev):
    """随机叫一份涩图，对每个用户有冷却时间"""
    uid = ev['user_id']
    if not _flmt.check(uid):
        await bot.send(ev, '您冲得太快了，请稍候再冲', at_sender=True)
        return
    _flmt.start_cd(uid)
    kw = ev.message.extract_plain_text().strip()
    try:
        count = min(int(kw), 5)
        if count <= 0:
            count = 1
    except Exception:
        count = 1
    # conditions all ok, send a setu.
    pic = [find_old() for _ in range(count)]
    pic = [i.cqcode for i in pic]
    pic = sum(pic)
    try:
        await bot.send(ev, pic)
    except CQHttpError:
        sv.logger.error(f"发送图片{pic}失败")
        try:
            await bot.send(ev, '涩图太涩，发不出去勒...')
        except Exception:
            pass
