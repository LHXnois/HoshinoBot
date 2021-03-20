import random
import hoshino
from hoshino import Service, R
from hoshino.typing import NoticeSession
from hoshino.Groupmaster import Groupmaster as Gm

sv1 = Service('group-leave-notice', help_='退群通知')

howleave = ['退群了', '被rm -rf了', '失去了梦想', '离开了我们',
            '各自精彩去了', '褪裙了', '回了老家', '回老家娶老婆了',
            '回老家种田去了', '去德国骨科了', '起飞了', '跑路了',
            '**了', '消失了', '离开了我们', '转生了', '尝试用岩浆泡脚',
            ]

@sv1.on_notice('group_decrease.leave')
async def leave_notice(session: NoticeSession):
    uid = session.ctx['user_id']
    avatar = await R.avatar(uid)
    avatar = avatar.cqcode
    info = await hoshino.get_bot().get_stranger_info(user_id=uid)
    name = info['nickname']
    await session.send(
        f"{str(avatar)}\n{name}({uid}){random.choice(howleave)}。")


sv2 = Service('group-welcome', help_='入群欢迎')

@sv2.on_notice('group_increase')
async def increace_welcome(session: NoticeSession):
    uid = session.event.user_id
    if uid == session.event.self_id:
        return  # ignore myself
    level = await Gm(session.event).vip_info(uid, 'level')
    if level is not None and level < 9:
        await session.send(f'⚠新成员qq等级较低(lv.{level})，请群友提高安全意识，谨慎交流')
    welcomes = hoshino.config.groupmaster.increase_welcome
    gid = session.event.group_id
    if gid in welcomes:
        await session.send(welcomes[gid], at_sender=True)
    # elif 'default' in welcomes:
    #     await session.send(welcomes['default'], at_sender=True)
