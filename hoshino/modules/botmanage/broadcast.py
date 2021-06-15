import asyncio

import hoshino
from hoshino.service import sucmd, _loaded_services
from hoshino.typing import CommandSession, CQHttpError
from nonebot.argparse import ArgumentParser


@sucmd('broadcast', aliases=('bc', '广播'), force_private=False, shell_like=True)
async def broadcast(session: CommandSession):
    parser = ArgumentParser(session=session)
    parser.add_argument('-a', '--all', action='store_true')
    parser.add_argument('-s', '--service', type=str, default='')
    parser.add_argument('-g', '--group', type=int, default=0)
    args = parser.parse_args(session.argv)

    _all = args.all
    gid = args.group
    ser = args.service
    msg = session.current_arg
    bot = session.bot
    ev = session.event
    su = session.event.user_id
    for sid in hoshino.get_self_ids():
        if _all:
            gl = await bot.get_group_list(self_id=sid)
            gl = [g['group_id'] for g in gl]
        elif gid:
            gl = [gid]
        elif ser in _loaded_services:
            gl = _loaded_services[ser].get_enable_groups()
            for i in gl:
                gl[i] = sid if sid in gl[i] else gl[i][0]
        else:
            await session.finish('-a/-g/-s')
        await bot.send_private_msg(self_id=sid, user_id=su, message=f"开始向{len(gl)}个群广播：\n{msg}")
        for g in gl:
            await asyncio.sleep(0.5)
            try:
                await bot.send_group_msg(self_id=sid, group_id=g, message=msg)
                hoshino.logger.info(f'群{g} 投递广播成功')
            except CQHttpError as e:
                hoshino.logger.error(f'群{g} 投递广播失败：{type(e)}')
                try:
                    await bot.send_private_msg(self_id=sid, user_id=su, message=f'群{g} 投递广播失败：{type(e)}')
                except Exception as e:
                    hoshino.logger.critical(f'向广播发起者进行错误回报时发生错误：{type(e)}')
    await bot.send_private_msg(self_id=ev.self_id, user_id=su, message='广播完成！')
