from os import replace
import random
from re import split
import pytz
from datetime import datetime
from urllib import parse
from hoshino import R, Service, util, SubService, aiorequests
from hoshino.Gm import Gm
from hoshino.typing import CQEvent

sv = Service('wackiness', help_='''整活小功能们''', visible=False, bundle='fun')
Answer = SubService('answerbook', sv, help_='''为什么不问问神奇海螺呢！
[#答案之书] 后跟你的烦恼，问题解决率高达81.0%!(口胡''')
Choseone = SubService('choseone', sv, help_='''拯救选择恐惧症！
[#选择A还是B] 帮你做出选择''')
Cl = SubService('checkcolock', sv, help_='''看看你的表走得准不准！
[#对表] 获取对表网站链接''')
Cp = SubService('CPwords', sv, help_='''CP文生成
[#对表] 获取对表网站链接''')
Howtobaidu = SubService('howtobaidu', sv, help_='''拯救懒人群友！
[#百度xxx] 让可可萝教你百度xxx''')
Mz = SubService('mozheng', sv, help_='''魔怔文生成器！
[#我好想做A的B啊/C/D] 原文为《嘉然小姐的狗》
    A替换嘉然小姐
    B替换狗
    C替换老鼠
    D替换猫
    CD可以没有
    eg:#我好想做萝莉的狗啊''')
Lw = SubService('longwang', sv, help_='''迫害龙王！
[#迫害龙王] 字面意思''')
Nbnhhsh = SubService('nbnhhsh', sv, help_='''能不能好好说话！
[#??] 后跟翻译缩写
eg:#??pcr''')
Speak = SubService('speakthis', sv, help_='''[#说xxx] 调用tx朗读接口读xxx''')
Tail = SubService('gentail', sv, help_='''群名片小尾巴！
[#我要小尾巴] 后跟想要的小尾巴''')
Tql = SubService('tal', sv, help_='''tql！
[#tqlxxx] 讲讲xxx的故事''')
Wyy = SubService('wyysentence', sv, help_='''到点了，上号！
[上号/到点了] 每天0-1点限定功能''')
Yinglish = SubService('yinglish', sv, help_='''淫语翻译机
[#提涩] 后跟想要提升涩度的文字
[#提提涩] 转化率max，效果好不好不好说''')
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


@Nbnhhsh.on_suffix('是啥', '是啥啊', '是啥？', '是啥啊？', only_to_me=True)
@Nbnhhsh.on_prefix('??', '？？', '啥是', only_to_me=True)
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


@Wyy.on_keyword('上号', '网抑云', '到点了')
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
    else:
        await bot.finish(ev, '上号失败，我很抱歉。查询出错，请稍后重试。')
    if random.random() < 0.5:
        wyypic = R.img(
            'groupfun/wyy/wyy', f'{random.randint(1, 42)}.jpg').cqcode
        sentences = f'{wyypic}\n' + sentences
    await bot.send(ev, sentences)


@Answer.on_prefix('人生解答', '答案之书', only_to_me=True)
async def chat_answer(bot, ev: CQEvent):
    try:
        answers = R.data('groupfun/wackygroup/answer.json', 'json')
        answers = answers.read["Theanswer"]
        await bot.send(ev, random.choice(answers), at_sender=True)
    except Exception:
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


@Speak.on_prefix('说', only_to_me=True)
async def speakthis(bot, ev: CQEvent):
    kw = ev.message.extract_plain_text().strip()
    if kw:
        await bot.send(ev, f'[CQ:tts,text={kw}]')


@Tail.on_prefix('我要小尾巴', only_to_me=True)
async def weiba(bot, ev: CQEvent):
    fcode = u'\u202e'
    ecode = u'\u202d'
    kw = ev.message.extract_plain_text().strip()
    weiba = fcode+kw[::-1]+ecode
    oldcard = ev.sender['card'] or ev.sender['nickname']
    newcard = oldcard+weiba
    try:
        if await Gm(ev).card_set(ev.user_id, newcard) == Gm.PRIV_NOT_ENOUGH:
            await bot.send(ev, '好像不能亲手给你戴上呢> <，请自己全选复制换上去吧~', at_sender=True)
            await bot.send(ev, newcard)
    except Exception as e:
        sv.logger.error(e)
        await bot.send(ev, '好像不能亲手给你戴上呢> <，请自己全选复制换上去吧~', at_sender=True)
        await bot.send(ev, newcard)


@Lw.on_fullmatch('迫害龙王', '谁是龙王', only_to_me=True)
async def longwang(bot, ev: CQEvent):
    longwang = await Gm(ev).honor_info(
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


@Cl.on_fullmatch('对表', only_to_me=True)
async def checkclock(bot, ev: CQEvent):
    msg = '[CQ:share,url=https://time.is/zh/,title=时间校准]'
    await bot.send(ev, msg)


@Yinglish.on_prefix('提色', '提涩', '提瑟', only_to_me=True)
async def seqiup(bot, ev: CQEvent):
    kw = ev.message.extract_plain_text().strip()
    kw = util.filt_message(kw)
    kw = util.chs2yin(kw)
    await bot.send(ev, kw)


@Yinglish.on_prefix('提提色', '提提涩', '提提瑟', only_to_me=True)
async def seqiupup(bot, ev: CQEvent):
    kw = ev.message.extract_plain_text().strip()
    kw = util.filt_message(kw)
    kw = util.chs2yin(kw, 1)
    await bot.send(ev, kw)


@Mz.on_rex(r'^我?好想做([^/]+)的([^/]+)啊', only_to_me=True)
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


@Tql.on_prefix('tql', only_to_me=True)
async def tql(bot, ev: CQEvent):
    try:
        for i in ev.message:
            if i['type'] == 'at' and i['data']['qq'] != 'all':
                info = await Gm(ev).member_info(i['data']['qq'])
                kw = info['card'] or info['nickname']
                break
        else:
            kw = ev.message.extract_plain_text().strip()
        if not kw:
            return
        stories = R.data('groupfun/wackygroup/tql.json', 'json').read
        stories = random.choice(stories)
        await bot.send(ev, stories.replace('%name%', kw))
    except Exception:
        sv.logger.error('chat_tql读json出错')


@Cp.on_prefix('cp', 'CP', only_to_me=True)
async def cp(bot, ev: CQEvent):
    kw = []
    for i in ev.message:
        if i['type'] == 'at' and i['data']['qq'] != 'all':
            info = await Gm(ev).member_info(i['data']['qq'])
            kw.append(info['card'] or info['nickname'])
            if len(kw) > 1:
                break
    else:
        if kws := ev.message.extract_plain_text().strip().split():
            kw.extend(kws)
        if len(kw) == 1:
            kw.append(ev.sender['card'] or ev.sender['nickname'])
    if len(kw) < 2:
        return
    try:
        random.shuffle(kw)
        stories = R.data('groupfun/wackygroup/cp.json', 'json').read
        stories = random.choice(stories)
        await bot.send(ev, stories.format(A=kw[0], B=kw[1]))
    except Exception:
        sv.logger.error('chat_cp读json出错')
