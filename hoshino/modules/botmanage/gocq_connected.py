import hoshino

bot = hoshino.get_bot()


@bot.on_meta_event('lifecycle.connect')
async def gocq_connect(ev):
    try:
        debuggroup = bot.config.DEBUGGROUP[0]
        assert debuggroup
        await bot.send_group_msg(group_id=debuggroup, message='go-cq 已连接！')
    except Exception:
        master = bot.config.SUPERUSERS[0]
        await bot.send_private_msg(user_id=master, message='go-cq 已连接！')
