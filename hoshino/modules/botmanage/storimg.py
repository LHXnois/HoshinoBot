from hoshino.service import sucmd
from hoshino import R
from hoshino.typing import CommandSession


@sucmd('storimg', aliases=('上传图片', '保存图片'), force_private=False)
async def storimg(session: CommandSession):
    folder = session.event.message.extract_plain_text().strip().split(' ')[-1]
    if await R.download_img_form_msgs(
            session.event.message, f'storimg/{folder}'):
        await session.send('get')
