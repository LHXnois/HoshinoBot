from .generate import generate_day_schedule
import hoshino
import nonebot
import re
from hoshino import util, R

HELP_STR = '''
公主连结活动日历
[#日历] : 查看本群订阅服务器日历
[#国/台/日服日历] : 查看指定服务器日程
[#国/台/日服日历] on/off : 订阅/取消订阅指定服务器的日历推送
[#日历 time 时:分] : 设置日历推送时间
[#日历 status] : 查看本群日历推送设置
'''.strip()

sv = hoshino.Service('pcr_calendar', help_=HELP_STR, bundle='pcr查询')

group_data = {}


calendardata = R.data('priconne', 'calendar.json')
icon = 'https://lolibest.ltd/kokkoro_stamp.ico'


def load_data():
    if not calendardata.exist:
        return
    data = calendardata.read
    for k, v in data.items():
        group_data[k] = v


def save_data():
    calendardata.write(group_data)


async def send_calendar(group_id):
    bot = hoshino.get_bot()
    available_group = await sv.get_enable_groups()
    if str(group_id) not in group_data or int(group_id) not in available_group:
        return
    for server in group_data[str(group_id)]['server_list']:
        if 'clanb' in group_data[str(group_id)]:
            clanb = group_data[str(group_id)]['clanb']
            im = await generate_day_schedule(server, clanb)
        else:
            im = await generate_day_schedule(server)
        base64_str = util.pic2b64(im)
        if 'cardimage' not in group_data[group_id] or not group_data[group_id]['cardimage']:
            msg = f'[CQ:image,file={base64_str}]'
        else:
            msg = util.gencardimage(base64_str, f'{server}服日历', icon)
        for _ in range(5):  # 失败重试5次
            try:
                await bot.send_group_msg(group_id=int(group_id), message=msg)
                sv.logger.info(f'群{group_id}推送{server}日历成功')
                break
            except:
                sv.logger.info(f'群{group_id}推送{server}日历失败')
            await asyncio.sleep(60)


def update_group_schedule(group_id):
    group_id = str(group_id)
    if group_id not in group_data:
        return
    nonebot.scheduler.add_job(
        send_calendar,
        'cron',
        args=(group_id,),
        id=f'calendar_{group_id}',
        replace_existing=True,
        hour=group_data[group_id]['hour'],
        minute=group_data[group_id]['minute']
    )


@sv.on_rex(r'^([国台日])?服?日[历程](.*)', only_to_me=True)
async def start_scheduled(bot, ev):
    group_id = str(ev['group_id'])
    server_name = ev['match'].group(1)
    if server_name == '台':
        server = 'tw'
    elif server_name == '日':
        server = 'jp'
    elif server_name == '国':
        server = 'cn'
    elif group_id in group_data and len(group_data[group_id]['server_list']) > 0:
        server = group_data[group_id]['server_list'][0]
    else:
        server = 'cn'
    cmd = ev['match'].group(2)
    if not cmd:
        if 'clanb' in group_data[str(group_id)]:
            clanb = group_data[str(group_id)]['clanb']
            im = await generate_day_schedule(server, clanb)
        else:
            im = await generate_day_schedule(server)
        base64_str = util.pic2b64(im)
        if 'cardimage' not in group_data[group_id] or not group_data[group_id]['cardimage']:
            msg = f'[CQ:image,file={base64_str}]'
        else:
            msg = util.gencardimage(base64_str, f'{server}服日历', icon)
    else:
        if group_id not in group_data:
            group_data[group_id] = {
                'server_list': [],
                'hour': 8,
                'minute': 0,
                'cardimage': False,
            }
        if not hoshino.priv.check_priv(ev, hoshino.priv.ADMIN):
            msg = '权限不足'
        elif 'on' in cmd:
            if server not in group_data[group_id]['server_list']:
                group_data[group_id]['server_list'].append(server)
            save_data()
            msg = f'{server}日程推送已开启'
        elif 'off' in cmd:
            if server in group_data[group_id]['server_list']:
                group_data[group_id]['server_list'].remove(server)
            save_data()
            msg = f'{server}日程推送已关闭'
        elif 'time' in cmd:
            match = re.search(r'(\d*):(\d*)', cmd)
            if not match or len(match.groups()) < 2:
                msg = '请指定推送时间'
            else:
                group_data[group_id]['hour'] = int(match.group(1))
                group_data[group_id]['minute'] = int(match.group(2))
                msg = f"推送时间已设置为: {group_data[group_id]['hour']}:{group_data[group_id]['minute']:02d}"
        elif 'status' in cmd:
            msg = f"订阅日历: {group_data[group_id]['server_list']}"
            msg += f"\n推送时间: {group_data[group_id]['hour']}:{group_data[group_id]['minute']:02d}"
        elif 'cardimage' in cmd:
            if 'cardimage' not in group_data[group_id] or not group_data[group_id]['cardimage']:
                group_data[group_id]['cardimage'] = True
                msg = '已切换为cardimage模式'
            else:
                group_data[group_id]['cardimage'] = False
                msg = '已切换为标准image模式'
            save_data()
        elif '会战' in cmd or 'clanb' in cmd:
            if 'clanb' not in group_data[group_id] or group_data[group_id]['clanb']:
                group_data[group_id]['clanb'] = False
                msg = '已隐藏会战相关内容'
            else:
                group_data[group_id]['clanb'] = True
                msg = '已取消隐藏会战相关内容'
            save_data()
        else:
            msg = '指令错误'
        update_group_schedule(group_id)
        save_data()
    await bot.send(ev, msg)

'''
@sv.on_fullmatch('test')
async def test(bot, ev):
    update_group_schedule(ev.group_id)
'''


@nonebot.on_startup
async def startup():
    load_data()
    for group_id in group_data:
        update_group_schedule(group_id)
