import random
import requests
import pytz
import json
import os
from datetime import datetime
from nonebot import on_command, CommandSession
from urllib import parse
from hoshino import R, Service, priv, util, SubService
from hoshino.typing import NoticeSession

sv = Service('wackiness', help_='''整活小功能们''', visible=False, bundle='整活')
Choseone = SubService('choseone', sv, help_='''拯救选择恐惧症！
[@选择A还是B]帮你做出选择''')
Howtobaidu = SubService('howtobaidu', sv, help_='''拯救懒人群友！
[@百度xxx]让可可萝教你百度xxx''')
Nbnhhsh = SubService('nbnhhsh', sv, help_='''能不能好好说话！
[@??]翻译缩写
eg:#??pcr''')

@Choseone.on_prefix('选择', only_to_me=True)
async def choseone(bot, ev):
    kw = ev.message.extract_plain_text().strip()
    arr = kw.split('还是')
    arr = [i for i in arr if i != '']
    if len(arr) > 1:
        msg = []
        msg.append('')
        count = 1
        for i in arr:
            if len(i) > 0:
                msg.append(f'{count}，{i}')
                count += 1
        msg.append(f'建议选择：{random.choice(arr)}')
        await bot.send(ev, '\n'.join(msg), at_sender=True)


@Howtobaidu.on_prefix('百度', only_to_me=True)
async def howtobaidu(bot, ev):
    msg = []
    kw = ev.message.extract_plain_text().strip()
    if kw == '':
        return
    baiduurl = 'http://api.goubibei.com/baidu/?'
    shorturl = 'http://api.wx.urlfh.com/dwz.php?type=qq&longurl='
    msg.append(f'\n可可罗教你怎么百度{kw}哦')
    data = {
        "kw": kw
    }
    kw = parse.urlencode(data)
    url = baiduurl + kw[3:]
    surl = shorturl + url
    resp = requests.get(surl, timeout=5)
    if resp.status_code == requests.codes.ok:
        res = resp.json()
        if res['code'] == 1:
            if res['ae_url'] is None:
                url = res['longurl']
            else:
                url = res['ae_url']
    msg.append(url)
    await bot.send(ev, '\n'.join(msg), at_sender=True)


@Nbnhhsh.on_suffix(('是啥', '是啥啊', '是啥？', '是啥啊？'), only_to_me=True)
@Nbnhhsh.on_prefix(('??', '？？', '啥是'), only_to_me=True)
async def nbnhhsh(bot, ev):
    kw = ev.message.extract_plain_text().strip()
    if len(kw) > 1 and kw.isalnum():
        body = {"text": kw}
        resp = requests.post(
            'https://lab.magiconch.com/api/nbnhhsh/guess/',
            data=body,
            timeout=5
            )
        if resp.status_code == requests.codes.ok:
            res = resp.json()
            if 'trans' in res[0]:
                msg = f'"{kw}"可能是：\n'+' '.join(res[0]['trans'])
                await bot.send(ev, msg)
            else:
                await bot.send(ev, 'emm...在下也猜不透它的意思')
        else:
            Nbnhhsh.logger.error('查询失败')


@sv.on_prefix(('人生解答', '答案之书'), only_to_me=True)
async def chat_answer(bot, ev):
    try:
        with open(os.path.join(os.path.dirname(__file__), 'data/chat.json'), 'r', encoding='utf8') as f:
            answers = json.load(f)["Theanswer"]
            await bot.send(ev, random.choice(answers), at_sender=True)
    except:
        sv.logger.error('chat_answer读json出错')
        return

@sv.on_fullmatch('今年剩余', only_to_me=True)
async def chat_jinnianshengyu(bot, ev):
    now = datetime.now(tz)
    start = datetime(now.year, 1, 1)
    nowtime = datetime(now.year, now.month, now.day)
    xiaohao = (nowtime - start).days
    shengyu = int(xiaohao*10/365)
    msg = f'今年已过去{xiaohao}天\n'
    for i in range(shengyu):
        msg += '◼'
    for i in range(10-shengyu):
        msg += '◻'
    await bot.send(ev, msg)

@sv.on_keyword(('上号', '网抑云', '到点了'))
async def music163_sentences(bot, ctx):
    now = datetime.now(tz)
    if not (0 <= now.hour <= 1):
        # await bot.send(ev, '还没到点呢')
        return
    if random.random() < 0.1:
        await bot.finish(ctx, R.img('groupfun', f'wyy/notwyy{random.randint(1, 7)}.jpg').cqcode)
    if random.random() < 0.5+1:
        resp = requests.get('http://api.heerdev.top/nemusic/random', timeout=5)
        if resp.status_code == requests.codes.ok:
            res = resp.json()
            sentences = res['text']
            # await bot.send(ctx, sentences)
        else:
            await bot.finish(ctx, '上号失败，我很抱歉。查询出错，请稍后重试。')
    else:
        resp = requests.get('https://api.lo-li.icu/wyy/', timeout=5)
        if resp.status_code == requests.codes.ok:
            sentences = resp.text
            # await bot.finish(ctx, sentences)
        else:
            await bot.finish(ctx, '上号失败，我很抱歉。查询出错，请稍后重试。')
    if random.random() < 0.5:
        wyypic = R.img('groupfun', f'wyy/wyy{random.randint(1, 42)}.jpg').cqcode
        sentences = f'{wyypic}\n' + sentences
    await bot.send(ctx, sentences)

