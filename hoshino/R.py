import os
from urllib.parse import urljoin
from urllib.request import pathname2url

from nonebot import MessageSegment, get_bot
from PIL import Image, ImageFont
import aiohttp

import hoshino
from hoshino import logger, util, aiorequests

import re
import random
import filetype


class ResObj:
    def __init__(self, res_path):
        res_dir = os.path.expanduser(hoshino.config.RES_DIR)
        fullpath = os.path.abspath(os.path.join(res_dir, res_path))
        if not fullpath.startswith(os.path.abspath(res_dir)):
            raise ValueError('Cannot access outside RESOUCE_DIR')
        self.__path = os.path.normpath(res_path)

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


class ResImg(ResObj):
    @property
    def cqcode(self) -> MessageSegment:
        if hoshino.config.RES_PROTOCOL == 'http':
            return MessageSegment.image(self.url)
        elif hoshino.config.RES_PROTOCOL == 'file':
            return MessageSegment.image(f'file:///{os.path.abspath(self.path)}')
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
    def __init__(self, res_path, Type: str = None):
        ResObj.__init__(self, res_path)
        self.Type = Type

    @property
    def read(self) -> dict:
        if not self.Type:  # 没有指定后缀，自动识别后缀名
            try:
                self.Type = filetype.guess_mime(self.path).split('/')[1]
            except:
                raise ValueError('不是有效文件类型')
        if self.Type == 'json':
            return util.load_jsons(self.path)
        else:
            hoshino.logger.error(f'未定义该类型数据处理方式：{self.Type}')


class ResFont(ResObj):
    def open(self, size: int) -> ImageFont:
        return ImageFont.truetype(self.path, size)


class TemImg(ResImg):

    def __init__(self, res_path, Type: str = None, for_gocq: bool = False):
        self.for_gocq = for_gocq
        self.Type = Type
        if for_gocq:
            self.gocqpath = res_path
        else:
            suffix = os.path.splitext(res_path)
            if suffix[1] in ('.image', '.mirai', '.null'):
                res_path = suffix[0]
            ResObj.__init__(self, res_path)
            self.__path = self._ResObj__path
            if not self.exist:
                dirpath = os.path.split(self.path)[0]
                if not os.path.exists(dirpath):
                    os.makedirs(dirpath, exist_ok=True)

    @property
    def path(self):
        """资源文件的路径，供bot内部使用"""
        if self.for_gocq:
            return self.gocqpath
        else:
            return os.path.join(hoshino.config.RES_DIR, self.__path)

    def delete(self):
        if self.exist:
            try:
                os.remove(self.path)
            except Exception as e:
                hoshino.logger.exception(e)

    async def download(self, url: str) -> None:
        hoshino.logger.info(f'download_tem_img from {url}')
        resp = await aiorequests.get(url, stream=True)
        hoshino.logger.debug(f'status_code={resp.status_code}')
        if 200 == resp.status_code:
            try:
                if re.search(r'image', resp.headers['content-type'], re.I):
                    content = await resp.content
                    self.addsuffix(content=content)
                    hoshino.logger.debug(f'is image, saving to {self.path}')
                    with open(self.path, 'wb') as f:
                        f.write(content)
                        hoshino.logger.debug('saved!')
                        return self
            except Exception as e:
                hoshino.logger.exception(e)

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
            return MessageSegment.image(self.path)
        elif hoshino.config.RES_PROTOCOL == 'http':
            return MessageSegment.image(self.url)
        elif hoshino.config.RES_PROTOCOL == 'file':
            return MessageSegment.image(f'file:///{os.path.abspath(self.path)}')
        else:
            try:
                return MessageSegment.image(util.pic2b64(self.open()))
            except Exception as e:
                hoshino.logger.exception(e)
                return MessageSegment.text('[图片出错]')

    def addsuffix(self, suffix: str = None, content=None):
        if os.path.splitext(self.path)[1]:
            return
        if not suffix:  # 没有指定后缀，自动识别后缀名
            try:
                suffix = filetype.guess_mime(
                    content).split('/')[1]
                self.Type = suffix
            except:
                raise ValueError('不是有效文件类型')
                suffix = 'png'
        self.__path = self.__path+'.'+suffix


def get(path, *paths):
    return ResObj(os.path.join(path, *paths))


def img(path, *paths):
    return ResImg(os.path.join('img', path, *paths))


def rand_img(path, *paths):
    files = os.listdir(os.path.join('img', path, *paths))
    rfile = random.choice(files)
    return ResImg(rfile)


def data(path, Type=None):
    return ResData(os.path.join('data', path), Type)


def font(path, *paths):
    return ResFont(os.path.join('font', path, *paths))


def tem_img(path, *paths):
    return TemImg(os.path.join('tem/img', path, *paths))


async def tem_gocqimg(url_path, headers=None, thread_count=1):
    if not headers:
        headers = [
            "User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36",
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
