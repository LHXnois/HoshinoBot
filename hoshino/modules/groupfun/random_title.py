import random
import re
from hoshino import Service, R, priv
from hoshino.Groupmaster import Groupmaster as Gm
from hoshino.util import FreqLimiter, DailyNumberLimiter
import hoshino


sv = Service('random-title', help_='''随机头衔
[@bot随机头衔]获得一个随机头衔
[@bot申请头衔]后跟自己想要的头衔
'''.strip())

Timecd = 86400  # 这是一天
_flmt = FreqLimiter(86400)
_nlmt = DailyNumberLimiter(1)
last_req = {}

titlegroup = ('中二', 'pcr', '碧蓝', '基础', 'all', 'blhx')


@sv.on_rex(r'^.*随机(pcr|中二|基础|碧蓝(航线)?|blhx)?头衔$', only_to_me=True)
# @sv.on_keyword('随机头衔', only_to_me=True)
async def random_title(bot, ev):
    user_id = ev.user_id
    if pohaicheck(ev.group_id, user_id):  # 判断是否被迫害，是的话忽略
        return
    await check_cd(bot, ev, Timecd/12)  # 判断是否cd
    match = ev['match'].group(1)
    if match not in titlegroup:
        choice = 'all'
    else:
        choice = match
    await Gm(ev).title_set(
        user_id=user_id,
        title=rand_title(choice),
    )


@sv.on_prefix(('申请头衔', '我想要头衔', '想要头衔'), only_to_me=True)
async def set_title(bot, ev):
    user_id = ev.user_id
    if pohaicheck(ev.group_id, user_id):
        return
    s = ev.message.extract_plain_text()
    if not _nlmt.check(user_id) and ev.user_id not in hoshino.config.SUPERUSERS or hoshino.config.PYUSERS:
        await bot.finish(ev, '新头衔要好好佩戴哦(自主申请头衔限每天一次，明天5点再来吧~)', at_sender=True)
    _nlmt.increase(user_id, 1)
    # await check_cd(bot, ev, Timecd)
    await Gm(ev).title_set(
        user_id=user_id,
        title=s,
    )


@sv.on_prefix(('设置迫害头衔', '迫害头衔'), only_to_me=True)  # 设置头衔并加入迫害列表
async def suset_title(bot, ev):
    if not priv.check_priv(ev, priv.PYUSER):  # master限定
        return
    firm = ev.message[0]
    if firm['type'] == 'at' and firm['data']['qq'] != 'all':
        uid = firm['data']['qq']
        s = ev.message.extract_plain_text()
        await Gm(ev).title_set(
            user_id=uid,
            title=s,
        )
        pohaiadd(ev.group_id, uid)


@sv.on_prefix(('不迫害', '不再迫害'), only_to_me=True)
async def no_pohai(bot, ev):
    if not priv.check_priv(ev, priv.PYUSER):  # master限定
        return
    count = 0
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            if nopohai(ev.group_id, uid):
                count += 1
    if count:
        await bot.send(ev, f"已解除{count}位用户的迫害～")


def rand_name(length=2):
    if random.random() < 0.4:
        word = '随机头衔'
        if random.random() < 0.4:
            lmsg = list(word)
            random.shuffle(lmsg)
            word = ''.join(lmsg)
        return word
    word = ''
    for _ in range(length):
        a = random.randint(0xb0, 0xd7)
        if a == 0xd7:
            b = random.randint(0xa1, 0xf9)
        else:
            b = random.randint(0xa1, 0xfe)
        val = f'{a:x}{b:x}'
        word += bytes.fromhex(val).decode('gb2312')
    return word


def rand_azurname():
    return random.choice(titledata["partA"]) + random.choice(
        titledata["partB"]) + random.choice(
            titledata["partC"]) + random.choice(titledata["partD"])


def rand_zhongername():
    if random.random() < 0.8:
        title = random.choice(titledata["partF"]) + \
            random.choice(titledata["partG"])
        if random.random() < 0.1:
            if title[2] in "の的之":
                title = title[3:] + title[2] + title[0:2]
            else:
                title = title[2:]+title[0:2]
        if len(title) < 5:
            if random.random() < 0.25:
                title = random.choice(["Re:", "The:", "此乃"]) + title
            elif random.random() < 0.4:
                title = title + random.choice(titledata["partH"])
    else:
        title = random.choice(titledata["partF"])
        if random.random() < 0.6:
            title = random.choice(["代号:", "Re:", "The:", "此乃"]) + title
            if random.random() < 0.5 and len(title) < 5:
                title = title + random.choice(titledata["partH"])
        else:
            title = title + random.choice(titledata["partH"])
    return title


def rand_title(choice='all'):
    r = random.random()
    if choice in '碧蓝航线blhx' or (choice == 'all' and r < 0.3):
        return rand_azurname()
    elif choice == '中二' or (choice == 'all' and r < 0.5):
        return rand_zhongername()
    elif choice == 'pcr' or (choice == 'all' and r < 0.8):
        return random.choice(titledata["partE"])
    elif r < 0.9:
        length = 2
    elif r < 0.99:
        length = 3
    else:
        length = 4
    return rand_name(length)


async def check_cd(bot, ev, addcd):
    if ev.user_id in hoshino.config.SUPERUSERS or hoshino.config.PYUSERS:
        return
    if not _flmt.check(ev.user_id):
        cd = int(_flmt.left_time(ev.user_id))
        scd = f'{str(int(cd/3600))}h{str(int((cd%3600)/60))}min{str(int((cd%3600)%60))}s'
        await bot.finish(ev, f'新头衔要好好佩戴哦(cd:{scd})', at_sender=True)
    _flmt.start_cd(ev.user_id, addcd)


pohailistdata = R.data('groupfun/random_title/pohailist.json', 'json')  # 读列表
if not pohailistdata.exist:
    content = '''{
    1111111: []
}'''
    pohailistdata.write(content)
pohailist = pohailistdata.read
titledata = R.data('groupfun/random_title/data.json', 'json').read


def pohaiadd(group_id, user_id):  # 加入迫害列表
    if user_id in hoshino.config.SUPERUSERS or hoshino.config.PYUSERS:
        return
    if group_id not in pohailist:
        pohailist[group_id] = [user_id]
    elif user_id not in pohailist[group_id]:
        pohailist[group_id].append(user_id)
    else:
        return
    pohailistdata.write(pohailist)


def pohaicheck(group_id, user_id):  # 检查是否受迫害
    if user_id in hoshino.config.SUPERUSERS or hoshino.config.PYUSERS:
        return False
    if group_id not in pohailist:
        pohailist[group_id] = []
        pohailistdata.write(pohailist)
        return False
    elif user_id not in pohailist[group_id]:
        return False
    return True


def nopohai(group_id, user_id):
    if group_id not in pohailist:
        pohailist[group_id] = []
        pohailistdata.write(pohailist)
        return False
    elif user_id not in pohailist[group_id]:
        return False
    else:
        pohailist[group_id].remove(user_id)
        pohailistdata.write(pohailist)
        return True
