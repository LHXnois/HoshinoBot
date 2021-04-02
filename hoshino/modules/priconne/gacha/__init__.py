import os
import random
from collections import defaultdict
from PIL import Image

from hoshino import Service, priv, util, R
from hoshino.typing import CQEvent, MessageSegment
from hoshino.util import DailyNumberLimiter, concat_pic, pic2b64, silence

from .. import chara
from .gacha import Gacha, cardinfo
from ..pcrColleciton import pcrCoins, pcrCharas
try:
    import ujson as json
except Exception:
    import json


sv_help = '''
在群里玩pcr（的抽卡）！
宝石来源：签到，小游戏
[#单抽/十连/来一井] 抽卡！
ps: 每天第一发十连免费
[#抽干家底] 更真实的抽一井（指抽到就停手
[#pcr仓库] 看看box
[#查看卡池] 卡池&出率
[#切换卡池] 更换卡池（jp以外卡池不会及时更新（懒
'''.strip()
sv = Service('gacha', help_=sv_help, bundle='pcr娱乐')
free_limit = DailyNumberLimiter(1)

FAIL_LIST = [
    f'抽卡被宫子拦住了！\n{R.img("priconne/gacha/buding.jpg").cqcode}',
    f'主さま,花凛小姐有事不在\n{R.img("priconne/gacha/kkl.gif").cqcode}',
    f'奇怪的东西混进了卡池！\n{R.img(f"priconne/gacha/jojo{random.randint(1, 2)}.gif").cqcode}',
    f'触发了奇怪的动画！\n{R.img("priconne/gacha/naoyixue.gif").cqcode}',
    '为什么会失败呢？原因征集中！有好玩的脑洞请告诉蓝红心！',
]
bg_gacha10 = R.img('priconne/gacha/backgrounds.jpg').open().convert('RGBA')
bg_up = R.img('priconne/gacha/bg-up.png').open().convert('RGBA')
bg_mid = R.img('priconne/gacha/bg-mid.png').open().convert('RGBA')
bg_down = R.img('priconne/gacha/bg-down.png').open().convert('RGBA')
GACHA_FAIL_NOTICE = f'\n抽卡失败了！\n{random.choice(FAIL_LIST)}\n本次抽卡无消耗'
POOL = ('MIX', 'JP', 'TW', 'BL')
DEFAULT_POOL = POOL[0]

_pool_config_file = os.path.expanduser('~/.hoshino/group_pool_config.json')
_group_pool = {}
try:
    with open(_pool_config_file, encoding='utf8') as f:
        _group_pool = json.load(f)
except FileNotFoundError as e:
    sv.logger.warning(
        'group_pool_config.json not found, will create when needed.')
_group_pool = defaultdict(lambda: DEFAULT_POOL, _group_pool)


def dump_pool_config():
    with open(_pool_config_file, 'w', encoding='utf8') as f:
        json.dump(_group_pool, f, ensure_ascii=False)


gacha_10_aliases = ('抽十连', '十连', '十连！', '十连抽', '来个十连', '来发十连', '来次十连', '抽个十连', '抽发十连', '抽次十连', '十连扭蛋', '扭蛋十连',
                    '10连', '10连！', '10连抽', '来个10连', '来发10连', '来次10连', '抽个10连', '抽发10连', '抽次10连', '10连扭蛋', '扭蛋10连')
gacha_1_aliases = ('单抽', '单抽！', '来发单抽', '来个单抽', '来次单抽', '扭蛋单抽', '单抽扭蛋')
gacha_200_aliases = ('抽一井', '来一井', '来发井', '抽发井', '天井扭蛋', '扭蛋天井')


@sv.on_fullmatch(('卡池资讯', '查看卡池', '看看卡池', '康康卡池', '看看up', '看看UP'))
async def gacha_info(bot, ev: CQEvent):
    gid = str(ev.group_id)
    gacha = Gacha(ev.user_id, _group_pool[gid])
    up_chara = gacha.up
    up_chara = map(lambda x: str(chara.fromname(
        x, star=3).icon.cqcode) + x, up_chara)
    up_chara = '\n'.join(up_chara)
    await bot.send(ev, f"本期卡池主打的角色：\n{up_chara}\nUP角色合计={(gacha.up_prob/10):.1f}% 3★出率={(gacha.s3_prob)/10:.1f}%")


POOL_NAME_TIP = '请选择以下卡池\n> 切换卡池jp\n> 切换卡池tw\n> 切换卡池b\n> 切换卡池mix'


@sv.on_prefix(('切换卡池', '选择卡池'))
async def set_pool(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '只有群管理才能切换卡池', at_sender=True)
    name = util.normalize_str(ev.message.extract_plain_text())
    if not name:
        await bot.finish(ev, POOL_NAME_TIP, at_sender=True)
    elif name in ('国', '国服', 'cn'):
        await bot.finish(ev, '请选择以下卡池\n> 选择卡池 b服\n> 选择卡池 台服')
    elif name in ('b', 'b服', 'bl', 'bilibili'):
        name = 'BL'
    elif name in ('台', '台服', 'tw', 'sonet'):
        name = 'TW'
    elif name in ('日', '日服', 'jp', 'cy', 'cygames'):
        name = 'JP'
    elif name in ('混', '混合', 'mix'):
        name = 'MIX'
    else:
        await bot.finish(ev, f'未知服务器地区 {POOL_NAME_TIP}', at_sender=True)
    gid = str(ev.group_id)
    _group_pool[gid] = name
    dump_pool_config()
    await bot.send(ev, f'卡池已切换为{name}池', at_sender=True)
    await gacha_info(bot, ev)


async def check_jewel_num(bot, ev: CQEvent, num):
    pC = pcrCoins(ev.user_id, '宝石')
    if not pC.check_C(num):
        have = pC.cnum
        await bot.finish(ev, f'主さま，我们的宝石只剩{have}了，已经付不起{num}了><', at_sender=True)


def get_coin_info(uid, all=False):
    msg = ['========']
    msg.append(f'剩余宝石{pcrCoins(uid, "宝石").cnum}颗')
    msg.append(f"女神的秘石{pcrCoins(uid, '秘石').cnum}颗")
    if all:
        msg.append(f'心碎{pcrCoins(uid, "心碎").cnum}颗')
        msg.append(f'mana{pcrCoins(uid, "mana").cnum}颗')
        msg.append(f'卢币{pcrCoins(uid, "卢币").cnum}颗')
        msg.append(f'扫荡券{pcrCoins(uid, "扫荡券").cnum}张')
    return '\n'.join(msg)


def get_gachares_info(uid: int, result: dict, gtype: int, res: Image,
                      free: bool = False, chara=None,
                      onlyforup: bool = False) -> MessageSegment:
    msg = []
    nh = result['hiishi']
    ne = len(result['new'])
    up = result['up']
    s3 = result['s3']
    s2 = result['s2']
    s1 = result['s1']
    silenunit = 30 if result['fes'] else 60
    if gtype == 1:
        msg = [f'{chara.name} {"★"*chara.star}']
    else:
        msg = [f'>{ne}new {up}up\n{s3}虹{s2}金{s1}银']
    if gtype == 10:
        if free:
            msg = ['今天份的免费十连！><'] + msg
        resultlist = [f'{c.name}{"★"*c.star}' for c in result['chara']]
        msg.append(' '.join(resultlist[0:5]))
        msg.append(' '.join(resultlist[5:]))
    if result['new'] and gtype != 1:
        newinfo = []
        for i, n in enumerate(result['new']):
            if i % 3 == 0 and i > 0:
                newinfo.append('\n   ')
            newinfo.append(n)
        msg.append(('NEW: '+' '.join(newinfo)))
    if gtype == 200:
        fup = result['first_up_pos']
        if up and not onlyforup:
            msg.append(f"第{fup}抽首次获得up角色")
        if onlyforup:
            if up:
                msg.append(f'抽到了！好耶！\n第{fup}抽到up角色！，花费{fup*150}宝石')
            else:
                msg.append(f"沉船了...呜呜呜...\n抽了{fup}发，花费{fup*150}宝石")
    if result['prize']:
        msg.append('--------')
        if gtype == 1:
            msg.append(f'Prize Gacha! : {result["card"][0]}')
        elif gtype == 10:
            msg.append('Prize Gacha!')
            cardlist = result["card"]
            msg.append(f'{" ".join(cardlist[:5])}\n{" ".join(cardlist[5:])}')
        elif gtype == 200:
            msg.append('Prize Gacha!')
            for i in range(1, 7):
                if pget := result[f'p{i}']:
                    msg.append(f'{cardinfo[i]["name"]}×{pget}')
        msg.append('--------')
        if nc := result['chips']:
            msg.append(f'获得记忆碎片×{nc}个')
        if nh:
            pcrCoins(uid, '秘石').add_C(nh)
            msg.append(f'获得秘石×{nh}')
        if nhc := result['heartchip']:
            pcrCoins(uid, '心碎').add_C(nhc)
            msg.append(f'获得公主之心(碎片)×{nhc}个')
        if nrc := result['rushcoupon']:
            pcrCoins(uid, '扫荡券').add_C(nrc)
            msg.append(f'获得扫荡券×{nrc}张')
    else:
        if nc := result['chips']:
            msg.append(f'获得记忆碎片×{nc}个')
        if nh:
            pcrCoins(uid, '秘石').add_C(nh)
            msg.append(f'获得秘石×{nh}')

    if gtype == 200:
        if up == 0 and s3 == 0:
            msg.append("太惨了，主さま咱们还是退款删游吧...")
        elif up == 0 and s3 > 7:
            msg.append("up呢？我的up呢？")
        elif up == 0 and s3 <= 3:
            msg.append("主さま，梦幻包考虑一下？\n在下会更加努力的打工的！")
        elif up == 0:
            msg.append("据说天井的概率只有12.16%")
        elif up <= 2:
            if result['first_up_pos'] < 40:
                msg.append("你的喜悦我收到了，滚去喂鲨鱼吧！")
            elif result['first_up_pos'] < 80:
                msg.append("已经可以了，主さま已经很欧了")
            elif result['first_up_pos'] > 190:
                msg.append("标 准 结 局")
            elif result['first_up_pos'] > 150:
                msg.append("补井还是不补井，这是一个问题...")
            else:
                msg.append("期望之内，亚洲水平")
        elif up == 3:
            msg.append("抽井母五一气呵成！多出30等专武～")
        elif up >= 4:
            msg.append("记忆碎片一大堆！您是托吧？")
    msg.append(get_coin_info(uid))
    msg = R.text2pic(msg)
    img = concat_pic([res, msg], t=0 if gtype != 10 else 255)
    img = pic2b64(img)
    img = MessageSegment.image(img)
    if gtype == 200:
        silence_time = (2*up + s3*(1+0.5*int(bool(ne))))*silenunit
    elif gtype == 10:
        SUPER_LUCKY_LINE = 4
        silence_time = (2*(up)+s3*(1+int(bool(ne))))*silenunit
        SUPER_LUCKY = (2*(up)+s3) >= SUPER_LUCKY_LINE and free
        return img, silence_time, SUPER_LUCKY
    elif gtype == 1:
        silence_time = (4*up+s3*(1+ne))*silenunit
    return img, silence_time


def check_free_num(bot, ev: CQEvent):
    return free_limit.check(ev.user_id)


async def check_if_fail(bot, ev: CQEvent, p):
    if random.random() < p:
        await bot.finish(ev, GACHA_FAIL_NOTICE, at_sender=True)


async def check_all(bot, ev: CQEvent, num, p, free=False):
    uid = ev.user_id
    if free_limit.check(uid) and free:
        await check_if_fail(bot, ev, p)
        free_limit.increase(uid)
        return True
    else:
        await check_jewel_num(bot, ev, num)
        await check_if_fail(bot, ev, p)
        pcrCoins(uid, '宝石').red_C(num)


@sv.on_prefix(gacha_1_aliases, only_to_me=True)
async def gacha_1(bot, ev: CQEvent):

    await check_all(bot, ev, 150, 0.01)

    gid = str(ev.group_id)
    uid = ev.user_id
    gacha = Gacha(uid, _group_pool[gid])
    result = gacha.gacha_one(gacha.up_prob, gacha.s3_prob,
                             gacha.s2_prob, recordcard=True)

    chara = result['chara'][0]

    img, silence_time = get_gachares_info(
        uid, result, 1, chara.gachaicon, chara=chara)
    await bot.send(ev, f'素敵な仲間が増えますよ！\n{img}', at_sender=True)
    if silence_time:
        await silence(ev, silence_time, skip_su=False)


@sv.on_prefix(gacha_10_aliases, only_to_me=True)
async def gacha_10(bot, ev: CQEvent):

    free = await check_all(bot, ev, 1500, 0.02, True)

    await bot.send(ev, '少女祈祷中...')
    gid = str(ev.group_id)
    uid = ev.user_id
    gacha = Gacha(uid, _group_pool[gid])
    resultdic = gacha.gacha_ten()
    result = resultdic['chara']

    base = bg_gacha10.copy()
    res1 = chara.gen_team_pic(result[:5], size=84, gacha=True, t=0)
    res2 = chara.gen_team_pic(result[5:], size=84, gacha=True, t=0)
    res = concat_pic([res1, res2], border=0, t=0)
    base.paste(res, (156, 65), res.split()[3])
    # 纯文字版
    # result = [f'{c.name}{"★"*c.star}' for c in result]
    # res1 = ' '.join(result[0:5])
    # res2 = ' '.join(result[5:])
    # res = f'{res1}\n{res2}'
    img, silence_time, SUPER_LUCKY = get_gachares_info(
        uid, resultdic, 10, base, free=free)
    if SUPER_LUCKY:
        silence_time *= 2
        await bot.send(ev, '恭喜海豹！おめでとうございます！')

    await bot.send(ev, f'素敵な仲間が増えますよ！\n{img}', at_sender=True)
    if silence_time:
        await silence(ev, silence_time, skip_su=False)


@sv.on_prefix(gacha_200_aliases, only_to_me=True)
async def gacha_200(bot, ev: CQEvent):

    await check_all(bot, ev, 30000, 0.03)

    gid = str(ev.group_id)
    uid = ev.user_id
    gacha = Gacha(uid, _group_pool[gid])
    await bot.send(ev, '少女祈祷中...')
    result = gacha.gacha_tenjou()
    res = result['chara']
    lenth = len(res)
    if lenth <= 0:
        res = "\n竟...竟然没有3★？！\n"
        res = R.text2pic(res)
    else:
        step = 4
        pics = []
        for i in range(0, lenth, step):
            j = min(lenth, i + step)
            pics.append(chara.gen_team_pic(
                res[i:j], offsetx=8, sizey=72,
                star_slot_verbose=False, gacha=True, t=0))
        res = concat_pic(pics, border=-8, t=0)

    img, silence_time = get_gachares_info(uid, result, 200, res)
    await bot.send(ev, f'\n素敵な仲間が増えますよ！\n{img}', at_sender=True)
    if silence_time:
        await silence(ev, silence_time, skip_su=False)


@sv.on_prefix('抽干家底', only_to_me=True)
async def allin(bot, ev: CQEvent):
    gid = str(ev.group_id)
    uid = ev.user_id

    await check_jewel_num(bot, ev, 150)
    await check_if_fail(bot, ev, 0.03)

    gacha = Gacha(uid, _group_pool[gid])

    kw = ev.message.extract_plain_text().strip()
    if len(gacha.up) > 1 and kw != '':
        mappp = {'1': 0, '2': 1}
        if kw in mappp and (mappp[kw]+1) <= len(gacha.up):
            aimup = mappp[kw]
        else:
            wantid = chara.name2id(kw)
            mappp[wantid] = None
            t = 0
            for i in gacha.up:
                mappp[chara.name2id(i)] = t
                t += 1
            if mappp[wantid] is not None:
                aimup = mappp[wantid]
            else:
                comlist = ['#抽干家底' + i for i in gacha.up]
                await bot.finish(ev, '不加参数默认追一号位up，若要指定请在指令后加参数:\n'+'\n'.join(comlist))
    else:
        aimup = 0

    await bot.send(ev, '正在抽干家底...')
    num = min(pcrCoins(uid, '宝石').cnum // 150, 200)
    result = gacha.gacha_tenjou(num, True, aimup)
    gachatimes = min(num, result["first_up_pos"])
    pcrCoins(uid, '宝石').red_C(gachatimes*150)
    res = result['chara']
    lenth = len(res)
    if lenth <= 0:
        res = "\n竟...竟然没有3★？！\n"
        res = R.text2pic(res)
    else:
        step = 4
        pics = []
        for i in range(0, lenth, step):
            j = min(lenth, i + step)
            pics.append(chara.gen_team_pic(
                res[i:j], offsetx=8, sizey=72,
                star_slot_verbose=False, gacha=True, t=0))
        res = concat_pic(pics, border=-8, t=0)

    img, silence_time = get_gachares_info(
        uid, result, 200, res, onlyforup=True)

    await bot.send(ev, f'\n素敵な仲間が増えますよ！\n{img}', at_sender=True)
    if silence_time:
        await silence(ev, silence_time, skip_su=False)


@sv.on_prefix('发十连')
async def kakin(bot, ev: CQEvent):
    if ev.user_id not in bot.config.SUPERUSERS:
        return
    count = 0
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            if uid in bot.config.SUPERUSERS:
                pcrCoins(uid, '宝石').add_C(45000)
            free_limit.reset(uid)
            count += 1
    if count:
        await bot.send(ev, f"已为{count}位用户充值完毕！谢谢惠顾～")


@sv.on_fullmatch(('pcr仓库', 'pcrbox'))
async def lookbox(bot, ev: CQEvent):
    uid = ev.user_id
    eclist = pcrCharas(uid).get_exist_C()
    Starinfo = (util.load_config(__file__))['Starinfo']
    fes = Starinfo['fes']
    star3_f = Starinfo['star3_f']
    star1_f = Starinfo['star1_f']
    nfes = len(fes)
    nstar3_f = len(star3_f)
    nstar1_f = len(star1_f)
    star3 = len(Starinfo['star3']) + nfes + nstar3_f
    star2 = len(Starinfo['star2'])
    star1 = len(Starinfo['star1']) + nstar1_f
    allc = star3+star2+star1
    star = [3]
    count = {
        's1': 0,
        's2': 0,
        's3': 0,
        'fes': 0,
        's1_f': 0,
        's3_f': 0,
    }
    res = []
    if len(eclist) < 30:
        star = star+[1, 2]
    for (cid, cstar) in eclist:
        count[f's{cstar}'] += 1
        name = chara.fromid(cid).name
        if name in fes:
            count['fes'] += 1
        elif name in star3_f:
            count['s3_f'] += 1
        elif name in star1_f:
            count['s1_f'] += 1
        if cstar not in star:
            continue
        res.append(chara.fromid(cid))
    count = f'''总计：{count["s3"]+count["s2"]+count["s1"]}/{allc}
★★★: {count["s3"]}/{star3}
★★: {count["s2"]}/{star2}
★: {count["s1"]}/{star1}
FES: {count["fes"]}/{nfes}
限定三星: {count["s3_f"]}/{nstar3_f}
限定一星: {count["s1_f"]}/{nstar1_f}
{get_coin_info(uid, True)}'''
    count = R.text2pic(count, 20)
    lenth = len(res)
    if lenth <= 0:
        res = "\n空空如也\n"
        res = R.text2pic(res, 20)
    else:
        step = 4
        pics = []
        for i in range(0, lenth, step):
            j = min(lenth, i + step)
            pics.append(chara.gen_team_pic(
                res[i:j], star_slot_verbose=False))
        res = concat_pic(pics)

    img = concat_pic([count, res])
    img = pic2b64(img)
    img = MessageSegment.image(img)
    await bot.send(ev, f'的仓库：\n{img}', at_sender=True)
