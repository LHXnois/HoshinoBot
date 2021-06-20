from hoshino import Service, util
from hoshino.typing import MessageSegment, CQHttpError, CQEvent
from hoshino import aiorequests
sv = Service('dailynews', enable_on_default=False, help_='每日早报')


@sv.scheduled_job('cron', hour='8', minute='30')
async def autonews():
    try:
        info = await aiorequests.get('http://dwz.2xb.cn/zaob')
        info = await info.json()
        if info['msg'] == 'Success':
            await sv.broadcast(
                MessageSegment.image(info['imageUrl']), 'dailynews')
    except CQHttpError as e:
        sv.logger.error(f'daily news error {e}')
    except Exception as e:
        await util.botdebuginfo(f'daily news error {e}')


@sv.on_fullmatch('今日早报', only_to_me=True)
async def handnews(bot, ev: CQEvent):
    info = await aiorequests.get('http://dwz.2xb.cn/zaob')
    info = await info.json()
    if info['msg'] == 'Success':
        await bot.send(ev, MessageSegment.image(info['imageUrl']))
