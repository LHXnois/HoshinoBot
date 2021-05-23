import hoshino
from hoshino.util import botdebuginfo
bot = hoshino.get_bot()


@bot.on_meta_event('lifecycle.connect')
async def gocq_connect(ev):
    await botdebuginfo('go-cq 已连接！')
