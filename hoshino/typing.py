import random
from typing import (Any, Callable, Dict, Iterable, List, NamedTuple, Optional,
                    Set, Tuple, Union)
from io import BytesIO
from pathlib import Path
from base64 import b64encode
from aiocqhttp import Event as CQEvent
from nonebot import (CommandSession, CQHttpError, Message, MessageSegment as ms,
                     NLPSession, NoticeSession, RequestSession)
from requests.structures import CaseInsensitiveDict

from . import HoshinoBot


class MessageSegment(ms):
    @staticmethod
    def image(file: Union[str, bytes, BytesIO, Path],
              type_: Optional[str] = None,
              cache: bool = True,
              id: Optional[int] = None,
              c: Optional[int] = None) -> 'MessageSegment':
        """图片。"""
        # if isinstance(file, BytesIO):
        #    file = file.read()
        # if isinstance(file, bytes):
        #    file = f"base64://{b64encode(file).decode()}"
        # elif isinstance(file, Path):
        #    file = f'file:///{file.resolve()}'
        args = {'cache': 1 if cache else 0}
        if type_ in ('flash', 'show'):
            args['type'] = type_
            if type_ == 'show' and id:
                args['id'] = id
        if c:
            args['c'] = c
        return MessageSegment(type_='image', data={'file': file, **args})

    @staticmethod
    def cardimage(file: str, **args) -> 'MessageSegment':
        """card图片。"""
        return MessageSegment(type_='cardimage', data={'file': file, **args})

    @staticmethod
    def poke(qq: int) -> 'MessageSegment':
        return MessageSegment(type_='poke', data={'qq': str(qq)})

    @staticmethod
    def gift(qq: int, id: int = None) -> 'MessageSegment':
        if id is None:
            id = random.randint(0, 13)
        return MessageSegment(type_='gift', data={'qq': str(qq), 'id': str(id)})

    @staticmethod
    def tts(text: str) -> 'MessageSegment':
        """文字转语音。"""
        return MessageSegment(type_='tts', data={'text': text})

    @staticmethod
    def reply(id: int, **args) -> 'MessageSegment':
        """回复"""
        return MessageSegment(type_='reply', data={'id': id, **args})
