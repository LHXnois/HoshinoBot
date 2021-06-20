import random
from typing import (Any, Callable, Dict, Iterable, List, NamedTuple, Optional,
                    Set, Tuple, Union)

from aiocqhttp import Event as CQEvent
from nonebot import (CommandSession, CQHttpError, Message, MessageSegment as ms,
                     NLPSession, NoticeSession, RequestSession)

from . import HoshinoBot


class MessageSegment(ms):
    @staticmethod
    def image(file: str, **args) -> 'MessageSegment':
        """图片。"""
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
