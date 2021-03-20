import random
import pytz
from datetime import datetime
from urllib import parse
from hoshino import R, Service, util, SubService, aiorequests
from hoshino.Groupmaster import Groupmaster
from hoshino.typing import CQEvent

sv = Service('wackiness', help_='''整活小功能们''', visible=False, bundle='整活')
Choseone = SubService('choseone', sv, help_='''拯救选择恐惧症！
[@选择A还是B]帮你做出选择''')
Howtobaidu = SubService('howtobaidu', sv, help_='''拯救懒人群友！
[@百度xxx]让可可萝教你百度xxx''')
Nbnhhsh = SubService('nbnhhsh', sv, help_='''能不能好好说话！
[@??]翻译缩写
eg:#??pcr''')
Wyy = SubService('wyysentence', sv, help_='''到点了，上号！
[上号/到点了] 每天0-1点限定功能''')
tz = pytz.timezone('Asia/Shanghai')


@Choseone.on_prefix('选择', only_to_me=True)
async def choseone(bot, ev: CQEvent):
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
        await bot.send(ev, util.escape('\n'.join(msg)), at_sender=True)


@Howtobaidu.on_prefix('百度', only_to_me=True)
async def howtobaidu(bot, ev: CQEvent):
    kw = ev.message.extract_plain_text().strip()
    if kw == '':
        return
    baiduurl = 'https://tool.pcrlink.cn/nbhbdm/?'
    msg = f'可可罗教你怎么百度{kw}哦'
    url = baiduurl + f's={kw}'
    msg = f'[CQ:share,url={url},title={msg}]'
    await bot.send(ev, msg, at_sender=True)


@Nbnhhsh.on_suffix(('是啥', '是啥啊', '是啥？', '是啥啊？'), only_to_me=True)
@Nbnhhsh.on_prefix(('??', '？？', '啥是'), only_to_me=True)
async def nbnhhsh(bot, ev: CQEvent):
    kw = ev.message.extract_plain_text().strip()
    if len(kw) > 1 and kw.isalnum():
        body = {"text": kw}
        url = 'https://lab.magiconch.com/api/nbnhhsh/guess/'
        resp = await aiorequests.post(url, data=body, timeout=5)
        if resp.ok:
            res = await resp.json()
            if 'trans' in res[0]:
                msg = f'"{kw}"可能是：\n'+' '.join(res[0]['trans'])
                await bot.send(ev, util.escape(msg))
            else:
                await bot.send(ev, 'emm...在下也猜不透它的意思')
        else:
            Nbnhhsh.logger.error('查询失败')


@Wyy.on_keyword(('上号', '网抑云', '到点了'))
async def music163_sentences(bot, ev: CQEvent):
    now = datetime.now(tz)
    if not (0 <= now.hour <= 1):
        # await bot.send(ev, '还没到点呢')
        return
    if random.random() < 0.1:
        await bot.finish(ev, R.img(
            'groupfun/wyy/notwyy', f'{random.randint(1, 7)}.jpg').cqcode)
    resp = await aiorequests.get('https://api.lo-li.icu/wyy/', timeout=5)
    if resp.ok:
        sentences = await resp.text
        # await bot.finish(ev, sentences)
    else:
        await bot.finish(ev, '上号失败，我很抱歉。查询出错，请稍后重试。')
    if random.random() < 0.5:
        wyypic = R.img(
            'groupfun/wyy/wyy', f'{random.randint(1, 42)}.jpg').cqcode
        sentences = f'{wyypic}\n' + sentences
    await bot.send(ev, sentences)


@sv.on_prefix(('人生解答', '答案之书'), only_to_me=True)
async def chat_answer(bot, ev: CQEvent):
    try:
        answers = R.data('groupfun/wackygroup/answer.json', 'json')
        answers = answers.read["Theanswer"]
        await bot.send(ev, random.choice(answers), at_sender=True)
    except:
        sv.logger.error('chat_answer读json出错')
        await bot.send(ev, '答案之书找不到惹T T', at_sender=True)


@sv.on_fullmatch('今年剩余', only_to_me=True)
async def chat_jinnianshengyu(bot, ev: CQEvent):
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


@sv.on_prefix('我要小尾巴', only_to_me=True)
async def weiba(bot, ev: CQEvent):
    fcode = u'\u202e'
    ecode = u'\u202d'
    kw = ev.message.extract_plain_text().strip()
    weiba = fcode+kw[::-1]+ecode
    Gm = Groupmaster(ev)
    oldcard = await Gm.member_info(ev.user_id, 'card')
    if not oldcard:
        oldcard = await Gm.member_info(ev.user_id, 'nickname')
    newcard = oldcard+weiba
    try:
        await Gm.card_set(ev.user_id, newcard)
    except Exception as e:
        sv.logger.error(e)
        await bot.send(ev, '好像没办亲手给你戴上呢> <，请自己全选复制换上去吧~', at_sender=True)
        await bot.send(ev, newcard)


@sv.on_fullmatch(('迫害龙王', '谁是龙王'), only_to_me=True)
async def longwang(bot, ev: CQEvent):
    longwang = await Groupmaster(ev).honor_info(
        honor_type='talkative', key='current_talkative')
    if not longwang:
        await bot.finish(ev, '没有龙王')
    lwid = longwang['user_id']
    if lwid == ev.self_id:
        msg = R.img(f'groupfun/longwang/isme{random.randint(1, 4)}.jpg').cqcode
    else:
        pohaiimg = R.img(
            f'groupfun/longwang/pohai{random.randint(1, 13)}.jpg').cqcode
        msg = f'[CQ:at, qq={lwid}]\n{str(pohaiimg)}'
    await bot.send(ev, msg)


@sv.on_fullmatch(('对表'), only_to_me=True)
async def checkclock(bot, ev: CQEvent):
    msg = '[CQ:share,url=https://time.is/zh/,title=时间校准]'
    await bot.send(ev, msg)


@sv.on_prefix(('提色', '提涩', '提瑟'), only_to_me=True)
async def seqiup(bot, ev: CQEvent):
    kw = ev.message.extract_plain_text().strip()
    kw = util.filt_message(kw)
    kw = util.chs2yin(kw)
    await bot.send(ev, kw)


@sv.on_prefix(('提提色', '提提涩', '提提瑟'), only_to_me=True)
async def seqiupup(bot, ev: CQEvent):
    kw = ev.message.extract_plain_text().strip()
    kw = util.filt_message(kw)
    kw = util.chs2yin(kw, 1)
    await bot.send(ev, kw)


@sv.on_rex(r'^我?好想做([^/]+)的([^/]+)啊', only_to_me=True)
async def jiarannogog(bot, ev: CQEvent):
    cont = R.data('groupfun/wackygroup/jiarannodog.json', 'json').read
    cont = '\n'.join(cont)
    jiaran = ev['match'].group(1)
    dog = ev['match'].group(2)
    cont = cont.replace('嘉然小姐', jiaran).replace('狗', dog)
    kw = ev.message.extract_plain_text().strip().split('/')
    rlist = ['老鼠', '猫']
    i = 0
    for ki in kw[1:]:
        if i > 1:
            break
        if not ki:
            ki = rlist[i]
        cont = cont.replace(rlist[i], ki)
        i += 1
    await bot.send(ev, cont)
