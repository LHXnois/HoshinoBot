import os
import random
from aiocqhttp import CQHttp

from nonebot.exceptions import CQHttpError

from hoshino import R, Service, priv
from hoshino.util import FreqLimiter, DailyNumberLimiter, chain_replay, genchain
from hoshino.typing import CQEvent
_max = 5
EXCEED_NOTICE = f'您今天已经冲过{_max}次了，请明早5点后再来！'
_nlmt = DailyNumberLimiter(_max)
_flmt = FreqLimiter(5)
oldsetu_folder = 'setu/oldimgs/'
maxdeep = len(os.listdir(R.get('tem/img/', oldsetu_folder).path))
sv = Service('findold', manage_priv=priv.SUPERUSER,
             enable_on_default=True, help_=f'''考 古 发 现
取自一位一般互联网用户的qq图片文件夹）
涩图:沙雕图:表情包=8:1:1
[#考古] 从历史中扒拉一张图
ps：加数字可一次取多张，最多5 如#考古5
pps：斜杠加数字可指定深度，越大越久远，默认0 如#考古/1
ppps: 目前最大深度 {maxdeep-1}''', bundle='setu')

DEEPTH_NOT_EXIT = 404
DEEPTH_CLEAR = 200


def oldsetu_gener(deepth=0, num=1):
    locate = maxdeep - deepth
    if not (picdir := R.get('tem/img/', oldsetu_folder, str(locate))).exist:
        return DEEPTH_NOT_EXIT
    data = R.data('setu/oldimgs', f'{locate}.json', default={
            'left': 0,
    })
    if (filedata := data.read)['left'] == 0:
        filelist = os.listdir(picdir.path)
        if not (maxnum := len(filelist)):
            return DEEPTH_NOT_EXIT
        random.shuffle(filelist)
        filedata = {
            'left': maxnum,
            'maxnum': maxnum,
            'data': filelist
        }
    num = min(num, filedata['left'])
    pic = [R.tem_img(
        oldsetu_folder,
        str(locate),
        filedata['data'].pop()
        ).hexie for _ in range(num)]
    filedata['left'] -= num
    data.write(filedata)
    return (pic, filedata['left'], filedata['maxnum'])


infodata = {
    1: '? ~ 19.3',
    2: '19.3 ~ 19.5',
    3: '19.5 ~ 19.6',
    4: '19.6 ~ 19.8',
    5: '19.8 ~ 19.10',
    6: '19.10 ~ 19.10',
    7: '19.10 ~ 20.5',
    8: '20.5 ~ 20.8',
    9: '20.8 ~ 20.10',
    10: '20.10 ~ 21.1',
    11: '21.1 ~ 21.3',
    12: '21.3 ~ 21.4',
    13: '21.4 ~ 21.6'
}

# defaultsetu_gener = setu_gener()


''' def get_setu():
    return defaultsetu_gener.__next__() '''


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

@sv.on_prefix('考古', only_to_me=True)
async def find_olds(bot, ev: CQEvent):
    """随机叫一份涩图，对每个用户有冷却时间"""
    uid = ev['user_id']
    if not _flmt.check(uid):
        await bot.send(ev, '您冲得太快了，请稍候再冲', at_sender=True)
        return
    _flmt.start_cd(uid)
    kw = ev.message.extract_plain_text().strip().split('/')
    count = 1
    deepth = 0
    if len(kw) > 0 and kw[0]:
        try:
            count = min(int(kw[0].strip()), 5)
            if count <= 0:
                count = 1
        except Exception:
            count = 1
    if len(kw) > 1 and kw[1]:
        try:
            deepth = min(int(kw[1].strip()), maxdeep-1)
            if deepth <= 0:
                deepth = 0
        except Exception:
            deepth = 0
    # conditions all ok, send a setu.
    pic = oldsetu_gener(deepth, count)
    if pic is DEEPTH_NOT_EXIT:
        await bot.finish(ev, '该深度下没有图片！')
    left = pic[1]
    pic = [i.cqcode for i in pic[0]]
    picm = sum(pic)
    try:
        info = f'深度{deepth}\n时期: {infodata[maxdeep-deepth]}\n剩余图片{left}'
        await bot.send(ev, f'{info}\n{picm}')
    except CQHttpError:
        sv.logger.error(f"发送图片{picm}失败")
        try:
            msg = [genchain(info)]
            username = ev.sender['card'] or ev.sender['nickname']
            for i in pic:
                name = random.choice([username, '色批'])
                msg.append(genchain(i, name, ev.user_id))
            await chain_replay(bot, ev, msg)
        except CQHttpError:
            await bot.send(ev, info)
            for i, p in enumerate(pic):
                try:
                    await bot.send(ev, p)
                except CQHttpError:
                    await bot.send(ev, f'{i+1}号涩图太涩，发不出去勒...')
                    await bot.send_private_msg(
                        user_id=uid,
                        group_id=ev.group_id,
                        message=p)
