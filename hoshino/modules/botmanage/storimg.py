from hoshino.service import sucmd
from hoshino import R
from hoshino.typing import CommandSession


@sucmd('storimg', aliases=('上传图片', '保存图片'), force_private=False)
async def storimg(session: CommandSession):
    folder = session.event.message.extract_plain_text().strip().split(' ')[-1]
    con = 0
    for i in session.event.message:
        if i['type'] == 'image':
            img = i['data']['file']
            imgurl = i['data']['url']
            await R.tem_img(f'storimg/{folder}', img).download(imgurl)
            con += 1
    if con:
        await session.send('get')
