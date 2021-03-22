from hoshino import SubService
from hoshino import priv, util, R
from hoshino import aiorequests
from .query import sv as msv
from hoshino.service import sucmd
from hoshino.typing import CommandSession

sv_help = '''
xxx要卡rank吗？
[#日/台/陆rank] rank推荐表
'''.strip()

sv = SubService("pcr-rank", msv, help_=sv_help)

server_addr = "https://pcresource.coldthunder11.com/rank/"


class Rank:
    areas = {'cn': '国服', 'tw': '台服', 'jp': '日服'}
    rankdata = R.data('priconne/query/rank.json', 'json')
    ranks = rankdata.read['source']
    rankc = rankdata.read['cache']

    def __init__(self, area: str) -> None:
        self.area = area
        self.source = Rank.ranks[area]
        self.sourceurl = server_addr + \
            f"{self.source['channel']}/{self.source['route']}/"
        self.cache = Rank.rankc[area]
        self.rankp = R.img('priconne/quick', f'{area}rank.jpg')

    @property
    def pic(self):
        if self.rankp.exist:
            return self.rankp.cqcode
        else:
            pass

    async def genrenkpic(self, no_cache=False):
        pics = []
        for picname in self.cache['files']:
            pic = R.tem_img('priconne/quick', picname)
            if not pic.exist or no_cache:
                await pic.download(f'{self.sourceurl}{picname}')
            pics.append(pic.open().convert('RGBA'))
        rpic = util.concat_pic(pics, 0, 0)
        rpic.convert('RGB').save(self.rankp.path)

    async def update_cache(self, no_cache=False):
        resp = await aiorequests.get(f"{self.sourceurl}config.json")
        res = await resp.json()
        new = False
        if self.cache['notice'] != res['notice']:
            new = True
            self.cache['notice'] = res['notice']
        if self.cache['files'] != res['files']:
            new = True
            self.cache['files'] = res['files']
        if new:
            data = Rank.rankdata.read
            data['cache'][self.area] = self.cache
            Rank.rankdata.write(data)
            await self.genrenkpic()
        elif no_cache:
            await self.genrenkpic(no_cache)
        return new

    def set_source(self, name=None, channel=None, route=None):
        if name:
            self.source['name'] = name
        if channel:
            self.source['channel'] = channel
        if route:
            self.source['route'] = route
        data = Rank.rankdata.read
        data['source'][self.area] = self.source
        Rank.rankdata.write(data)


async def update_cache(no_cache=False):
    sv.logger.info("正在更新Rank表缓存")
    for area in Rank.areas:
        await Rank(area).update_cache(no_cache)
    sv.logger.info("Rank表缓存更新完毕")

WHICH_SERVER = """
请问您要查询哪个服务器的rank表？
*日rank表
*台rank表
*陆rank表"""


@sv.on_rex(r"^(\*?([日台国陆b])服?([前中后]*)卫?)?rank(表|推荐|指南)?$", only_to_me=True)
async def rank_sheet(bot, ev):
    match = ev["match"]
    is_jp = match.group(2) == "日"
    is_tw = match.group(2) == "台"
    is_cn = match.group(2) and match.group(2) in "国陆b"
    if not is_jp and not is_tw and not is_cn:
        await bot.send(ev, WHICH_SERVER, at_sender=True)
        return
    msg = []
    msg.append("\n")
    area = 'jp' if is_jp else 'tw' if is_tw else 'cn'
    qrank = Rank(area)
    msg.append(qrank.cache['notice'])
    msg.append(str(qrank.pic))
    await bot.send(ev, "".join(msg), at_sender=True)
    await util.silence(ev, 60, False)


@sucmd("查看当前rank更新源", False)
async def show_current_rank_source(session: CommandSession):
    msg = []
    for area in Rank.areas:
        msg.append(f"\n{Rank.areas[area]}: \n")
        qrank = Rank(area)
        msg.append(qrank.source["name"])
        msg.append("   ")
        if qrank.source["channel"] == "stable":
            msg.append("稳定源")
        elif qrank.source["channel"] == "auto_update":
            msg.append("自动更新源")
        else:
            msg.append(qrank.source["channel"])
    await session.send("".join(msg), at_sender=True)


@sucmd("查看全部rank更新源", False)
async def show_all_rank_source(session: CommandSession):
    resp = await aiorequests.get(server_addr+"route.json")
    res = await resp.json()
    msg = []
    msg.append("\n")
    msg.append("稳定源：\n国服:\n")
    for uo in res["ranks"]["channels"]["stable"]["cn"]:
        msg.append(uo["name"])
        msg.append("   ")
    msg.append("\n台服:\n")
    for uo in res["ranks"]["channels"]["stable"]["tw"]:
        msg.append(uo["name"])
        msg.append("   ")
    msg.append("\n日服:\n")
    for uo in res["ranks"]["channels"]["stable"]["jp"]:
        msg.append(uo["name"])
        msg.append("   ")
    msg.append("\n自动更新源：\n国服:\n")
    for uo in res["ranks"]["channels"]["auto_update"]["cn"]:
        msg.append(uo["name"])
        msg.append("   ")
    msg.append("\n台服:\n")
    for uo in res["ranks"]["channels"]["auto_update"]["tw"]:
        msg.append(uo["name"])
        msg.append("   ")
    msg.append("\n日服:\n")
    for uo in res["ranks"]["channels"]["auto_update"]["jp"]:
        msg.append(uo["name"])
        msg.append("   ")
    msg.append("\n如需修改更新源，请使用命令[设置rank更新源 国/台/日 稳定/自动更新 源名称]")
    await session.send("".join(msg), at_sender=True)


@sv.on_rex(r'^设置rank更新源 (.{0,5}) (.{0,10}) (.{0,20})$')
async def change_rank_source(bot, ev):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.send(ev, "仅有SUPERUSER可以使用本功能")
    robj = ev['match']
    server = robj.group(1)
    channel = robj.group(2)
    name = robj.group(3)
    if server == "国":
        server = "cn"
    elif server == "台":
        server = "tw"
    elif server == "日":
        server = "jp"
    else:
        await bot.send(ev, "请选择正确的服务器（国/台/日）", at_sender=True)
        return
    if channel == "稳定":
        channel = "stable"
    elif channel == "自动更新":
        channel = "auto_update"
    else:
        await bot.send(ev, "请选择正确的频道（稳定/自动更新）", at_sender=True)
        return
    resp = await aiorequests.get(server_addr+"route.json")
    res = await resp.json()
    has_name = False
    source_jo = None
    for uo in res["ranks"]["channels"][channel][server]:
        if uo["name"].upper() == name.upper():
            has_name = True
            source_jo = uo
            break
    if not has_name:
        await bot.send(ev, "请输入正确的源名称", at_sender=True)
        return
    Rank(server).set_source(source_jo["name"], channel, source_jo["route"])
    await bot.send(ev, "更新源设置成功,开始更新缓存...", at_sender=True)
    await update_cache(True)
    await bot.send(ev, "更新成功")


@sucmd("更新rank源缓存", False)
async def update_rank_cache(session: CommandSession):
    await session.send("开始更新，这可能会花很久很久...")
    try:
        await update_cache(True)
        await session.send("更新成功")
    except Exception as e:
        await session.send(f'更新失败 {e}')


@sv.scheduled_job('cron', hour='17', minute='06')
async def schedule_update_rank_cache():
    await update_cache()


@sucmd("手动更新rank", False)
async def update_rankpic(session: CommandSession):
    area = session.event.message.extract_plain_text().strip().split(' ')[-1]
    if area not in Rank.areas:
        await session.finish('请选择正确的服务器（cn/tw/jp）')
    pics = []
    for i in session.event.message:
        if i['type'] == 'image':
            img = i['data']['file']
            imgurl = i['data']['url']
            pic = R.tem_img('storimg/rank', img)
            await pic.download(imgurl)
            pics.append(pic.open().convert('RGBA'))
    rpic = util.concat_pic(pics, 0, 0)
    rpic.convert('RGB').save(Rank(area).rankp.path)
    await session.send(Rank(area).pic)
