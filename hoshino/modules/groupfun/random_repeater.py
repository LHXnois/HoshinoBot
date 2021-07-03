import random
import hoshino
from hoshino import Service, util, R
from hoshino.typing import CQEvent, CQHttpError
from hoshino.Gm import Gm
from PIL import ImageSequence
from pygtrie import CharTrie
sv = Service('random-repeater', help_='随机复读机pro', bundle='fun')

PROB_A = 1.4
group_stat = {}     # group_id: (last_msg, is_repeated, p)

'''
不复读率 随 复读次数 指数级衰减
从第2条复读，即第3条重复消息开始有几率触发复读

a 设为一个略大于1的小数，最好不要超过2，建议1.6
复读概率计算式：p_n = 1 - 1/a^n
递推式：p_n+1 = 1 - (1 - p_n) / a
'''


@sv.on_message()
async def random_repeater(bot, ev: CQEvent):
    group_id = ev.group_id
    msg = ev.message

    if group_id not in group_stat:
        group_stat[group_id] = (msg, False, 0)
        return

    last_msg, is_repeated, p = group_stat[group_id]
    if check_repeater(last_msg, msg):     # 群友正在复读
        if not is_repeated:     # 机器人尚未复读过，开始测试复读
            sv.logger.debug(f"[群{group_id}] 群友正在复读，当前参与概率：{p}")
            if random.random() < p:    # 概率测试通过，复读并设flag
                try:
                    group_stat[group_id] = (msg, True, 0)
                    if not Gm.check_command(ev):
                        await _repeater(bot, ev, 0.3*(1-p))
                except CQHttpError as e:
                    hoshino.logger.error(f'复读失败: {type(e)}')
                    hoshino.logger.exception(e)
            else:                      # 概率测试失败，蓄力
                p = 1 - (1 - p) / PROB_A
                group_stat[group_id] = (msg, False, p)
        else:
            sv.logger.debug(f"[群{group_id}] 群友还在复读")
    else:   # 不是复读，重置
        group_stat[group_id] = (msg, False, 0)


def _test_a(a):
    '''
    该函数打印prob_n用于选取调节a
    注意：由于依指数变化，a的轻微变化会对概率有很大影响
    '''
    p0 = 0
    for _ in range(10):
        p0 = (p0 - 1) / a + 1
        print(p0)


def check_repeater(lastmsg, msg):
    if str(lastmsg) == str(msg):
        return True
    else:
        lenth = len(lastmsg)
        if lenth == len(msg):
            for i in range(lenth):
                if lastmsg[i]['type'] != msg[i]['type']:
                    return False
                elif lastmsg[i]['type'] == 'image':
                    if lastmsg[i]['data']['file'] != msg[i]['data']['file']:
                        return False
                else:
                    if lastmsg[i]['data'] != msg[i]['data']:
                        return False
            return True
    return False


async def _repeater(bot, ev, if_daduan=0):
    if random.random() < if_daduan:
        await bot.send(ev, '不许复读！')
        sv.logger.debug(f"[群{ev.group_id}] 打断了一次复读")
        return
    first_msg = ev.message[0]
    if first_msg['type'] == 'image':
        img = await R.download_img_form_msg(
            first_msg, 'groupfun/random_repeater')
        image = img.open()
        turnAround = random.randint(0, 6)
        if image.format == 'GIF':
            if image.is_animated:
                frames = [f.transpose(turnAround).copy()
                          for f in ImageSequence.Iterator(image)]
                if random.random() < 0.5:
                    frames.reverse()  # 内置列表倒序方法
                frames[0].save(img.path, save_all=True,
                               append_images=frames[1:],
                               loop=0, transparency=0)
        else:
            image.transpose(turnAround).save(img.path)
        await bot.send(ev, img.cqcode)
        sv.logger.debug(f"[群{ev.group_id}] 对单图片进行了特殊复读")
    else:
        textcount = 0
        for i in ev.message:
            if i['type'] == 'text' or 'emoji':
                textcount += 1
            else:
                textcount = 0
                break
        msg = str(util.filt_message(ev.message))
        if textcount >= 1:
            if random.random() < 0.05:
                msg = msg[::-1]
            elif random.random() < 0.05:
                lmsg = list(msg)
                random.shuffle(lmsg)
                msg = ''.join(lmsg)
        await bot.send(ev, msg)
        sv.logger.debug(f"[群{ev.group_id}] 进行了一次复读")


NOTAOWA_WORD = (
    'bili', 'Bili', 'BILI', '哔哩', '啤梨', 'mu', 'pili', 'dili',
    '是不', '批里', 'nico', '滴哩', 'BiLi', '不会吧', '20', '哼，', '哼,',
    ',000', '多娜', '霹雳'
)

lasttaowa = {}


def check_ltaowa(msg: str) -> list:
    t = CharTrie()
    for i in range(len(msg)//2-1):
        mmsg = msg[:i+2]
        if mmsg.strip(mmsg[0]):
            if mmsg.endswith((':', '：', '"', '“', "'", '‘')):
                t[(mmsg*2)[:-1]] = mmsg
            t[mmsg*2] = mmsg
    result = t.shortest_prefix(msg)
    if result:
        result = result.value
        smsg = msg.split(result)
        return [result, len(smsg)-1, smsg[-1]]
    else:
        return ['', 0, msg]


def check_rtaowa(msg: str) -> list:
    result = check_ltaowa(msg[::-1])
    return [result[0][::-1], result[1], result[2][::-1]]


def check_taowa(msg: str) -> list:
    ltaowa = check_ltaowa(msg)
    rtaowa = check_rtaowa(msg)
    if ltaowa[0] and rtaowa[0]:
        if len(ltaowa[2])+len(rtaowa[2]) < len(msg):
            case = ltaowa[1] - rtaowa[1]
            if (case == 0 and len(ltaowa[0]) < len(rtaowa[0])) or case < 0:
                ltaowa = check_ltaowa(rtaowa[2])
            else:
                rtaowa = check_rtaowa(ltaowa[2])
    if ltaowa[0] or rtaowa[0]:
        dic = {'ltor': {
            '<': '>', '《': '》',
            "'": "'", '"': '"',
            '‘': '’', '“': '”',
            '(': ')', '（': '）',
            '[': ']', '【': '】',
            '{': '}'}}
        dic['rtol'] = {dic['ltor'][i]: i for i in dic['ltor']}
        if not ltaowa[0]:
            for i in [rtaowa[0][-1], rtaowa[0][0]]:
                if i in dic['rtol']:
                    ltaowa[0] += dic['rtol'][i]
            smsg = ltaowa[2][::-1].split(rtaowa[0][::-1])[-1][::-1]
            if ltaowa[0] and len(smsg.split(ltaowa[0])) > 1:
                smsg = smsg.split(ltaowa[0], rtaowa[1])[-1]
        elif not rtaowa[0]:
            for i in [ltaowa[0][-1], ltaowa[0][0]]:
                if i in dic['ltor']:
                    rtaowa[0] = dic['ltor'][i]
            smsg = rtaowa[2].split(ltaowa[0])[-1]
            if rtaowa[0] and len(smsg[::-1].split(rtaowa[0][::-1])) > 1:
                smsg = smsg[::-1].split(rtaowa[0][::-1], ltaowa[1])[-1][::-1]
        else:
            smsg = rtaowa[2].split(ltaowa[0])[-1]
    else:
        return []
    return [ltaowa[0], rtaowa[0], smsg]


@sv.on_message()
async def taowabot(bot, ev: CQEvent):
    group_id = ev.group_id
    if group_id not in lasttaowa:
        lasttaowa[group_id] = (None, 0)
    for m in ev.message:
        if m.type in 'atimagefacejsonnode':
            lasttaowa[group_id] = ('', 0)
            return
    msg = str(ev.message)
    if (taowa := check_taowa(msg)) and not Gm.check_command(ev):
        if taowa[0] in NOTAOWA_WORD or taowa[1] in NOTAOWA_WORD:
            return
        lastt, taowacount = lasttaowa[group_id]
        if taowa != lastt:
            lasttaowa[group_id] = (taowa, 0)
            msg = taowa[0] + msg + taowa[1]
            await bot.send(ev, util.filt_message(msg))
        else:
            if taowacount == 0:
                if taowa[2] != '':
                    await bot.send(ev, '禁止套娃!')
            taowacount += 1
            lasttaowa[group_id] = (taowa, taowacount)
    else:
        lasttaowa[group_id] = (None, 0)
