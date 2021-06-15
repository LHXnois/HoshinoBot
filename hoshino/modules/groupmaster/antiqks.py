import aiohttp
from hoshino import R, Service, util
import re
sv = Service('antiqks', help_='识破骑空士的阴谋')

qksimg1 = R.img('groupmaster/antiqks1.jpg').cqcode
qksimg2 = R.img('groupmaster/antiqks2.jpg').cqcode

@sv.on_keyword("granbluefantasy.jp")
async def qks_keyword(bot, ev):
    msg = f'骑空士爪巴\n{qksimg1}'
    await bot.send(ev, msg, at_sender=True)
    await util.silence(ev, 60)

# 有潜在的安全问题
@sv.on_rex(r'[a-zA-Z0-9\.]{4,12}\/[a-zA-Z0-9]+')
async def qks_rex(bot, ev):
    msg = str(ev.raw_message)
    matchObj = re.search(r'[a-zA-Z0-9\.]{4,12}\/[a-zA-Z0-9]+', msg)
    msg = f'骑空士爪巴远点\n{qksimg2}'
    res = 'http://'+matchObj.group(0)
    async with aiohttp.TCPConnector(verify_ssl=False) as connector:
        async with aiohttp.request(
            'GET',
            url=res,
            allow_redirects=False,
            connector=connector,
        ) as resp:
            h = resp.headers
            s = resp.status
    if s == 301 or s == 302:
        if 'granbluefantasy.jp' in h['Location']:
            await bot.send(ev, msg, at_sender=True)
            await util.silence(ev, 60, skip_su=False)
