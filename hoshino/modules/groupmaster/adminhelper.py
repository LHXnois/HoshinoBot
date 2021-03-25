from hoshino import Service, R, priv, util
from hoshino.Gm import Gm
from hoshino.typing import CQEvent
from hoshino.msghandler import anonymous_list
from string import ascii_letters
from aiocqhttp.exceptions import ActionFailed
import re
import random
sv = Service('adminhelper',
             use_priv=priv.ADMIN, manage_priv=priv.OWNER,
             bundle='master', help_='''群管助手：机器人治国！
-----以下需bot为群主
[#设置管理员@xxx] 将xxx设为管理
[#撤销管理员@xxx] 撤销xxx的管理
[#设置头衔@xxxtest] 给xxx设置头衔test
-----以下需比对方职位高
[#飞机票@xxx] 欢送xxx
[#塞口球@xxx 1分] 口xxx一分钟
-----以下需要管理
[#摘口球@xxx] 给xxx解禁
[#匿名塞口球xxx 1分] 口匿名用户xxx一分钟，xxx为匿名昵称，匿名塞口球无法解除
[#全员口球 1分] 1分钟全体禁言
[#设置名片@xxxtest] 给xxx设置名片test
[#设置群名xxx] 设置群名为xxx
[#发公告xxx] 发公告xxx''')

@sv.on_prefix(('设置管理员', '戴帽子'), only_to_me=True)
async def set_admin(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.PYUSER):
        await bot.finish(ev, '权限不够哦', at_sender=True)
    for i in ev.message:
        if i.type == 'at' and (uid := i.data['qq']) != 'all':
            if await Gm(ev).admin_set(uid) == Gm.PRIV_NOT_ENOUGH:
                await bot.finish(ev, '在下好像不是群主呢...', at_sender=True)
    await bot.send(ev, '帽子戴好啦~')


@sv.on_prefix(('撤销管理员', '摘帽子'), only_to_me=True)
async def drop_admin(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.PYUSER):
        await bot.finish(ev, '权限不够哦', at_sender=True)
    for i in ev.message:
        if i.type == 'at' and (uid := i.data['qq']) != 'all':
            if await Gm(ev).admin_set(uid, False) == Gm.PRIV_NOT_ENOUGH:
                await bot.finish(ev, '在下好像不是群主呢...', at_sender=True)
    await bot.send(ev, '帽子摘好啦~')


@sv.on_prefix(('设置头衔',), only_to_me=True)
async def set_title(bot, ev):
    if not priv.check_priv(ev, priv.PYUSER):
        await bot.finish(ev, '权限不够哦', at_sender=True)
    firm = ev.message[0]
    if firm['type'] == 'at' and firm['data']['qq'] != 'all':
        uid = firm['data']['qq']
        s = ev.message.extract_plain_text().strip()
        if await Gm(ev).title_set(
                user_id=uid, title=s) == Gm.PRIV_NOT_ENOUGH:
            await bot.finish(ev, '在下好像不是群主呢...', at_sender=True)

ready_kick_group = {1111: {'test': []}}
@sv.on_prefix(('飞机票', '飞了他', '踢了他'))
async def kick_member(bot, ev:CQEvent):
    kicklist = []
    gid = ev.group_id
    Gmaster = Gm(ev)
    for i in ev.message:
        if i.type == 'at' and (uid := i.data['qq']) != 'all':
            kicklist.append(uid)
    if kicklist:
        str_list = [random.choice(ascii_letters) for i in range(5)]
        randstr = ''.join(str_list)
        ready_kick_group[gid] = {randstr: kicklist}
        msg = ['即将送走以下群友：']
        for i in kicklist:
            name = await Gmaster.member_info(i, 'card')
            if not name:
                name = await Gmaster.member_info(i, 'nickname')
            msg.append(f'{name}({i})')
        msg.append(f'请发送“#飞机票{randstr}”确认踢出')
        await bot.finish(ev, util.escape('\n'.join(msg)), at_sender=True)
    if gid in ready_kick_group:
        if (kw := str(ev.message)) in ready_kick_group[gid]:
            kicklist = ready_kick_group[gid][kw]
            for i in kicklist:
                if await Gmaster.member_kick(i) == Gm.PRIV_NOT_ENOUGH:
                    await bot.finish(ev, '在下好像没有权限呢')
            await bot.send(ev, '已经全部送走啦')


def timeget(time: int, unit: str) -> int:
    if unit in '秒sS':
        time = time * 1
    elif unit in '分mM':
        time = time * 60
    elif unit in '时hH':
        time = time * 3600
    elif unit in '天dD':
        time = time * 3600 * 24
    elif unit in '星周zZ':
        time = time * 3600 * 24 * 7
    elif unit == '月':
        time = time * 3600 * 24 * 30
    else:
        pass
    return time


@sv.on_prefix(('塞口球', '口他'), only_to_me=True)
async def must_sleep(bot, ev):
    msg = str(ev.message)
    matchObj = re.match(r'^\[CQ:at,qq=([0-9]+)\] +([0-9]+)?个?小?([月星周zZ时分秒HMSDhmsd天]?)钟?期?$', msg)
    if matchObj is not None:
        uid = int(matchObj.group(1))
        if uid in bot.config.SUPERUSERS:
            return
        if matchObj.group(2):
            time = int(matchObj.group(2))
            unit = matchObj.group(3) if matchObj.group(3) is not None else 'm'
        else:
            time = 1
            unit = 'm'
        time = timeget(time, unit)
        try:
            await Gm(ev).member_silence(time=time, user_id=uid)
        except ActionFailed as e:
            sv.logger.error(f'禁言失败 retcode={e.retcode}')
        except Exception as e:
            sv.logger.exception(e)


@sv.on_prefix(('摘口球', '解禁'), only_to_me=True)
async def dont_sleep(bot, ev):
    try:
        for i in ev.message:
            if i.type == 'at' and (uid := i.data['qq']) != 'all':
                if await Gm(ev).member_silence(
                        time=0, user_id=uid) == Gm.PRIV_NOT_ENOUGH:
                    await bot.finish(ev, '在下好像不是群主呢...', at_sender=True)
    except ActionFailed as e:
        sv.logger.error(f'禁言失败 retcode={e.retcode}')
    except Exception as e:
        sv.logger.exception(e)


def get_anonymous(ev: CQEvent):
    msg = []
    for i in anonymous_list[ev.group_id]['anonymous']:
        msg.append(f'{i}')
    if not msg:
        msg.append('...\n在本机运行期间还没有观测到过匿名用户~')
    msg = ['本机运行期间观测到过以下匿名用户:'] + msg
    return msg


@sv.on_prefix(('塞口球匿名', '匿名塞口球'), only_to_me=True)
async def anonymous_sleep(bot, ev: CQEvent):
    msg = str(ev.message)
    matchObj = re.match(r'^ ?([^ ]+)( [0-9]+)?个?小?([月星周zZ时分秒HMSDhmsd天]?)钟?期?$', msg)
    if matchObj is not None:
        gid = ev.group_id
        name = matchObj.group(1)
        if name not in anonymous_list[gid]['anonymous']:
            msg = ['没有观测到过该匿名用户,只能口球观测到过的匿名用户']
            msg = msg + get_anonymous(ev)
            await bot.finish(ev, '\n'.join(msg), at_sender=True)
        flag = anonymous_list[gid]['anonymous'][name]['flag']
        if matchObj.group(2):
            time = int(matchObj.group(2)[1:])
            unit = matchObj.group(3) if matchObj.group(3) is not None else '天'
        else:
            time = 1
            unit = '天'
        time = timeget(time, unit)
        try:
            await Gm(ev).member_silence(time=time, anonymous_flag=flag)
        except ActionFailed as e:
            sv.logger.error(f'禁言失败 retcode={e.retcode}')
        except Exception as e:
            sv.logger.exception(e)
    else:
        msg = ['格式不太对哦，请按照“#匿名塞口球xxx 1天”格式发送，xxx为匿名用户名字，后面时间要用空格隔开，不加时间默认一天']
        msg = msg + get_anonymous(ev)
        await bot.finish(ev, '\n'.join(msg), at_sender=True)


@sv.on_suffix('本群匿名消息', only_to_me=True)
async def about_anonymous(bot, ev: CQEvent):
    kw = ev.message.extract_plain_text()
    if kw == '处理':
        anonymous_list[ev.group_id]['no_anonymous'] = False
    elif kw == '不处理':
        anonymous_list[ev.group_id]['no_anonymous'] = True


@sv.on_prefix(('全域沉默', '关闭群聊', '全员口球'), only_to_me=True)
async def all_silence(bot, ev: CQEvent):
    msg = ev.message.extract_plain_text()
    matchObj = re.match(r'^ *([0-9]+)个?小?([月星周zZ时分秒HMSDhmsd天]?)钟?期?$', msg)
    if matchObj is not None:
        time = int(matchObj.group(1))
        unit = matchObj.group(2) if matchObj.group(2) is not None else 'm'
    else:
        time = 1
        unit = 'm'
    time = timeget(time, unit)
    try:
        if await Gm(ev).group_silence() == Gm.PRIV_NOT_ENOUGH:
            await bot.finish(ev, '在下好像不是群主呢...', at_sender=True)
    except ActionFailed as e:
        sv.logger.error(f'禁言失败 retcode={e.retcode}')

    async def task(ev: CQEvent):
        await Gm(ev).group_silence(False)
    util.add_delay_job(task=task, id=str(ev.group_id), delay_time=time, args=[ev])


@sv.on_prefix(('设置名片',), only_to_me=True)
async def set_card(bot, ev:CQEvent):
    if not priv.check_priv(ev, priv.PYUSER):
        await bot.finish(ev, '权限不够哦', at_sender=True)
    firm = ev.message[0]
    if firm['type'] == 'at' and firm['data']['qq'] != 'all':
        uid = firm['data']['qq']
        s = ev.message.extract_plain_text().strip()
        if await Gm(ev).card_set(
                user_id=uid, card_text=s) == Gm.PRIV_NOT_ENOUGH:
            await bot.finish(ev, '在下好像不是管理呢...', at_sender=True)


@sv.on_prefix('设置群名', only_to_me=True)
async def grouprename(bot, ev: CQEvent):
    kw = ev.message.extract_plain_text().strip()
    if await Gm(ev).groupname_set(kw) == Gm.PRIV_NOT_ENOUGH:
        bot.finish(ev, '在下好像不是管理呢...', at_sender=True)


@sv.on_prefix('发公告', only_to_me=True)
async def notice(bot, ev: CQEvent):
    kw = ev.message.extract_plain_text()
    if await Gm(ev).group_notice(kw) == Gm.PRIV_NOT_ENOUGH:
        bot.finish(ev, '在下好像不是管理呢...', at_sender=True)
