import os
from urllib.parse import urljoin
from urllib.request import pathname2url

from PIL import Image, ImageFont, ImageDraw
from aiocqhttp.message import Message

import hoshino
from hoshino import util, aiorequests
from hoshino.config import Proxies
from hoshino.typing import Union, MessageSegment, CaseInsensitiveDict

import re
import random
import filetype
import moviepy.editor as mpe


class ResObj:
    def __init__(self, res_path, must_file=False):
        res_dir = os.path.expanduser(hoshino.config.RES_DIR)
        fullpath = os.path.abspath(os.path.join(res_dir, res_path))
        if not fullpath.startswith(os.path.abspath(res_dir)):
            raise ValueError('Cannot access outside RESOUCE_DIR')
        self.__path = os.path.normpath(res_path)
        self.dir, self.file = os.path.split(self.__path)
        if self.file:
            self.file, self.suffix = os.path.splitext(self.file)
        elif must_file:
            raise ValueError('must be a file')

    @property
    def url(self):
        """资源文件的url，供酷Q（或其他远程服务）使用"""
        return urljoin(hoshino.config.RES_URL, pathname2url(self.__path))

    @property
    def path(self):
        """资源文件的路径，供bot内部使用"""
        return os.path.join(hoshino.config.RES_DIR, self.__path)

    @property
    def exist(self):
        return os.path.exists(self.path)

    def delete(self):
        if self.exist:
            try:
                os.remove(self.path)
            except Exception as e:
                hoshino.logger.exception(e)

    async def download(self, url: str, use_proxie=False, proxies=Proxies):
        hoshino.logger.info(f'download_res from {url}')
        if use_proxie:
            resp = await aiorequests.get(url, stream=True, proxies=proxies)
        else:
            resp = await aiorequests.get(url, stream=True)
        hoshino.logger.debug(f'status_code={resp.status_code}')
        if 200 == resp.status_code:
            try:
                content = await resp.content
                hoshino.logger.debug(f'saving to {self.path}')
                with open(self.path, 'wb') as f:
                    f.write(content)
                    hoshino.logger.debug('saved!')
                    return self
            except Exception as e:
                hoshino.logger.exception(e)


class ResImg(ResObj):
    @property
    def cqcode(self) -> MessageSegment:
        if hoshino.config.RES_PROTOCOL == 'http':
            return MessageSegment.image(self.url)
        elif hoshino.config.RES_PROTOCOL == 'file':
            return MessageSegment.image(
                f'file:///{os.path.abspath(self.path)}')
        else:
            try:
                return MessageSegment.image(util.pic2b64(self.open()))
            except Exception as e:
                hoshino.logger.exception(e)
                return MessageSegment.text('[图片出错]')

    def open(self) -> Image:
        try:
            return Image.open(self.path)
        except FileNotFoundError:
            hoshino.logger.error(f'缺少图片资源：{self.path}')
            raise


class ResData(ResObj):
    def __init__(self, res_path, default=None):
        super().__init__(res_path, must_file=True)
        if not self.exist:
            dirpath = os.path.dirname(self.path)
            if not os.path.exists(dirpath):
                os.makedirs(dirpath, exist_ok=True)
            if default is not None:
                self.write(default)

    @property
    def read(self) -> dict:
        if self.suffix == '.json':
            return util.load_jsons(self.path)
        if self.suffix == '.txt':
            return [line.strip() for line in open(
                self.path, encoding='UTF-8').readlines()]
        else:
            hoshino.logger.error(f'未定义该类型数据处理方式：{self.suffix}')

    def write(self, content):
        if self.suffix == '.json':
            util.save_jsons(content, self.path)
        else:
            hoshino.logger.error(f'未定义该类型数据处理方式：{self.suffix}')


class ResFont(ResObj):
    def open(self, size: int) -> ImageFont:
        return ImageFont.truetype(self.path, size)


class TemImg(ResImg):

    def __init__(self, res_path,
                 for_gocq: bool = False,
                 must_file=True):
        self.for_gocq = for_gocq
        if for_gocq:
            self.gocqpath = res_path
        else:
            super().__init__(res_path, must_file=must_file)
            if not self.exist:
                dirpath = os.path.dirname(self.path)
                if not os.path.exists(dirpath):
                    os.makedirs(dirpath, exist_ok=True)

    @property
    def path(self):
        """资源文件的路径，供bot内部使用"""
        if self.for_gocq:
            return self.gocqpath
        else:
            return super().path

    @property
    def url(self):
        """资源文件的url，供酷Q（或其他远程服务）使用"""
        if self.for_gocq:
            return urljoin(pathname2url(self.path))
        else:
            return urljoin(hoshino.config.RES_URL, pathname2url(self.__path))

    @property
    def cqcode(self) -> MessageSegment:
        if self.for_gocq:
            return MessageSegment.image(
                f'file:///{os.path.abspath(self.path)}')
        elif hoshino.config.RES_PROTOCOL == 'http':
            return MessageSegment.image(self.url)
        elif hoshino.config.RES_PROTOCOL == 'file':
            return MessageSegment.image(
                f'file:///{os.path.abspath(self.path)}')
        else:
            try:
                return MessageSegment.image(util.pic2b64(self.open()))
            except Exception as e:
                hoshino.logger.exception(e)
                return MessageSegment.text('[图片出错]')

    @property
    def hexie(self):
        if self.suffix not in ('.gif', '.GIF'):
            im = self.open()
            width, height = im.size
            draw = ImageDraw.Draw(im)
            draw.point(
                (random.randint(1, width), random.randint(1, height)),
                fill=(
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255)
                    ))
            im.save(self.path)
        return self


class TemVideo(ResObj):

    def __init__(self, res_path):
        super().__init__(res_path)
        if not self.exist:
            dirpath = os.path.split(self.path)[0]
            if not os.path.exists(dirpath):
                os.makedirs(dirpath, exist_ok=True)


    @property
    def gif(self):
        giftem = tem_img('vedio2gif', self.file+'.gif')
        cache = mpe.VideoFileClip(self.path)
        # todo toobiggif
        cache.write_gif(giftem.path)
        return giftem

    @property
    def cqcode(self):
        return self.gif.cqcode


def get(path, *paths):
    return ResObj(os.path.join(path, *paths))


def img(path, *paths):
    return ResImg(os.path.join('img', path, *paths))


def rand_img(path, *paths):
    files = os.listdir(get(path, *paths).path)
    rfile = random.choice(files)
    return ResImg(rfile)


def data(path, *paths, default=None):
    return ResData(os.path.join('data', path, *paths), default)


def font(path, *paths):
    return ResFont(os.path.join('font', path, *paths))


def tem_img(path, *paths, **args):
    return TemImg(os.path.join('tem/img', path, *paths), **args)


def tem_video(path, *paths):
    return TemVideo(os.path.join('tem/video', path, *paths))


def tem(ttype, path,  *paths, **args):
    if ttype == 'img':
        return tem_img(path, *paths, **args)
    elif ttype == 'video':
        return tem_video(path, *paths)


async def tem_gocqimg(url_path, headers=None, thread_count=1):
    if not headers:
        headers = [
            "User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                AppleWebKit/537.36 (KHTML, like Gecko) \
                Chrome/78.0.3904.87 Safari/537.36",
            "Referer=https://www.baidu.com"
        ]
    if 'qpic' in url_path:
        headers[1] = "Referer=https://user.qzone.qq.com"
    res_path = await hoshino.get_bot().download_file(
        url=url_path,
        thread_count=thread_count,
        headers=headers
    )
    return TemImg(res_path['file'], for_gocq=True)


async def download_img(url: str, *paths,
                       cache: bool = True,
                       check_suffix: bool = True,
                       proxies: dict = None,
                       headers: dict = None,
                       **args) -> TemImg:
    if paths:
        if (tem := tem_img(*paths)).exist and cache:
            return tem
        filename = tem.file
        suffix = tem.suffix
        dirname = tem.dir
        if suffix in ('.image', '.mirai', '.null') and check_suffix:
            suffix = ''

    hoshino.logger.info(f'downloading img from {url}')

    # ================================ #
    # 网络请求参数
    pama = {}
    if proxies is True:
        pama['proxies'] = Proxies
    elif proxies is not None:
        pama['proxies'] = proxies
    if headers is not None:
        pama['headers'] = CaseInsensitiveDict(headers)

    # ================================= #
    # 下载，确定后缀
    resp = await aiorequests.get(url, **pama)

    hoshino.logger.debug(f'status_code={resp.status_code}')

    if 200 != resp.status_code:
        pass
    if check_suffix and not suffix:
        if match := re.search(
                'image/(?P<type>[^;]+)',
                resp.headers.get('content-type'),
                flags=re.I):
            suffix = '.'+match.groupdict().get('type')

    content = await resp.content

    if check_suffix and not suffix:
        try:
            suffix = filetype.guess_extension(content) or 'jpg'
            suffix = '.'+suffix
        except Exception:
            suffix = '.jpg'
    # ================================== #
    # 这里必须确定img对象
    if paths:
        img = TemImg(os.path.join(dirname, filename+suffix))

    # ================================== #
    hoshino.logger.debug(f'is image, saving to {img.path}')
    with open(img.path, 'wb') as f:
        f.write(content)
        hoshino.logger.debug('saved!')
    return img


async def download_img_form_msg(msg: MessageSegment, *dirpath) -> TemImg:
    return await download_img(
        msg['data']['url'], *dirpath, msg['data']['file'])


async def download_img_form_msgs(msg: Message, *dirpath, num=0) -> list:
    imglist = []
    for i in msg:
        if i['type'] == 'image':
            imglist.append(await download_img_form_msg(i, *dirpath))
        if len(imglist) >= num > 0:
            break
    return imglist


def crop_square(img: Image) -> Image:
    width, height = img.size
    if width != height:
        length = min(width, height)
        return img.crop(((width - length) / 2, (height - length) / 2,
                        (width + length) / 2, (height + length) / 2))
    return img


def get_circle_pic(pic: Image, size: int = None, scale: int = 5) -> Image:
    pic = crop_square(pic)
    if not size:
        size = pic.size[0]
    else:
        pic = pic.resize((size, size))
    mask = Image.new('L', (size*scale, size*scale), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size * scale, size * scale), fill=255)
    mask = mask.resize((size, size), Image.ANTIALIAS)
    pic.putalpha(mask)
    return pic


async def avatar(user_id: int, s: int = 100) -> TemImg:
    apiPath = f'http://q1.qlogo.cn/g?b=qq&nk={user_id}&s={s}'
    return await download_img(
        apiPath, 'groupmaster/avatar', f'{user_id}_{s}.png',
        check_suffix=False,
        )


def add_text(img: Image, text: str, textsize: int,
             _f='msyh.ttf',
             textfill='black',
             position: tuple = (0, 0)) -> Image:
    '''textsize 文字大小\n
    font 字体，默认微软雅黑\n
    textfill 文字颜色，默认黑色，black 黑色，blue蓝色，white白色，yellow黄色，red红色\n
    position 文字偏移（0,0）位置，图片左上角为起点，第一个数是宽方向，第二个数是高方向'''
    _font = font(_f).open(textsize)
    draw = ImageDraw.Draw(img)
    draw.text(xy=position, text=text, font=_font, fill=textfill)
    return img


def textline2pic(text: str, textsize: int, textfill='black', t=255) -> Image:
    length = util.tlen(text, textsize)
    dsc = Image.new('RGBA', (length, textsize), (255, 255, 255, t))
    img = add_text(dsc, text, textsize, 'hkww.ttf', textfill)
    return img


def text2pic(text: Union[list, str],
             textsize: int = 20,
             textfill='black',
             t=255) -> Image:
    pics = []
    if type(text) is list:
        for i in text:
            pics.append(text2pic(i, textsize, textfill, t))
    elif type(text) is Image:
        pics.append(text)
    else:
        text = text.split('\n')
        for i in text:
            pics.append(textline2pic(i, textsize, textfill, t))
    return util.concat_pic(pics, 0, t)
