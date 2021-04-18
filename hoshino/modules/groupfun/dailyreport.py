from hoshino import Service, R, util
from hoshino.typing import CQEvent, MessageSegment
from wordcloud import WordCloud
import jieba

sv = Service('dayreport', enable_on_default=False, bundle='fun')
Gening = False
stopwords = R.data(
    'groupfun/dayreport/stopwords/baidu_stopwords.txt', 'txt').read
@sv.on_message()
async def msgstore(bot, ev: CQEvent):
    if Gening:
        return
    gid = ev.group_id
    msg = ev.message.extract_plain_text().strip()
    if not msg:
        return
    msg = jieba.cut(msg)
    msg = " ".join(msg)
    data = R.data(f'groupfun/dayreport/{gid}.json', 'json')
    if not data.exist:
        cont = []
    else:
        cont = data.read
    cont.append(msg)
    data.write(cont)

def genimg(gid):
    data = R.data(f'groupfun/dayreport/{gid}.json', 'json')
    cont = data.read
    cont = ' '.join(cont)
    Ws = WordCloud(
        width=800,
        height=600,
        font_path=R.font('simhei.ttf').path,
        background_color='white',
        stopwords=stopwords
    ).generate(cont)
    img = Ws.to_image()
    return MessageSegment.image(util.pic2b64(img))

@sv.scheduled_job('cron', hour='23', minute='59')
async def genreport():
    global Gening
    Gening = True
    glist = await sv.get_enable_groups()
    for gid in glist:
        await sv.bot.send_group_msg(
                group_id=gid,
                message=f'本日词云\n{genimg(gid)}'
            )
        R.data(f'groupfun/dayreport/{gid}.json', 'json').delete()
    Gening = False

@sv.on_fullmatch('本日词云', only_to_me=True)
async def reporttest(bot, ev: CQEvent):
    gid = ev.group_id
    await bot.send(ev, f'本日词云\n{genimg(gid)}')