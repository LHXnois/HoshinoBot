from hoshino.service import sucmd
from hoshino import R
from hoshino.typing import CommandSession
from nonebot.argparse import ArgumentParser


@sucmd('保存图片')
async def broadcast(session: CommandSession):
    folder = session.event.message.extract_plain_text().strip().split(' ')[-1]
    for i in session.event.message:
        if i['type'] == 'image':
            img = i['data']['file']
            imgurl = i['data']['url']
            await R.tem_img(f'storimg/{folder}', img).download(imgurl)
