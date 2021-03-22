from .textfilter.filter import DFAFilter
import base64
import os
import time
import unicodedata
from collections import defaultdict
from datetime import datetime, timedelta
from io import BytesIO

import re
import pytz
import zhconv
from aiocqhttp.exceptions import ActionFailed
from aiocqhttp.message import escape
from matplotlib import pyplot as plt
from PIL import Image

import hoshino
from hoshino.typing import CQEvent, Message, Union, MessageSegment
from .yinglish import chs2yin


try:
    import ujson as json
except:
    import json

from nonebot import scheduler


def load_config(inbuilt_file_var):
    """
    Just use `config = load_config(__file__)`,
    you can get the config.json as a dict.
    """
    filename = os.path.join(os.path.dirname(inbuilt_file_var), 'config.json')
    try:
        with open(filename, encoding='utf8') as f:
            config = json.load(f)
            return config
    except Exception as e:
        hoshino.logger.exception(e)
        return {}


def save_jsons(config: dict, path: str) -> bool:
    try:
        with open(path, 'w', encoding='utf8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as ex:
        hoshino.logger.error(ex)
        return False


def load_jsons(path: str) -> dict:
    try:
        with open(path, mode='r', encoding='utf8') as f:
            data = json.load(f)
            return data
    except Exception as ex:
        hoshino.logger.error(
            f'exception occured when loading config in {path}  {ex}')
        hoshino.logger.exception(ex)
        return {}


async def delete_msg(ev: CQEvent):
    try:
        await hoshino.get_bot().delete_msg(self_id=ev.self_id, message_id=ev.message_id)
    except ActionFailed as e:
        hoshino.logger.error(f'撤回失败 retcode={e.retcode}')
    except Exception as e:
        hoshino.logger.exception(e)


async def silence(ev: CQEvent, ban_time, skip_su=True):
    try:
        if skip_su and ev.user_id in hoshino.config.SUPERUSERS:
            return
        await hoshino.get_bot().set_group_ban(self_id=ev.self_id, group_id=ev.group_id, user_id=ev.user_id, duration=ban_time)
    except ActionFailed as e:
        hoshino.logger.error(f'禁言失败 retcode={e.retcode}')
    except Exception as e:
        hoshino.logger.exception(e)


def pic2b64(pic: Image) -> str:
    buf = BytesIO()
    pic.save(buf, format='PNG')
    base64_str = base64.b64encode(buf.getvalue()).decode()
    return 'base64://' + base64_str


def fig2b64(plt: plt) -> str:
    buf = BytesIO()
    plt.savefig(buf, format='PNG', dpi=100)
    base64_str = base64.b64encode(buf.getvalue()).decode()
    return 'base64://' + base64_str


def concat_pic(pics, border=5, t=255):
    num = len(pics)
    w = 0
    h = [0]*len(pics)
    for i, p in enumerate(pics):
        _w, h[i] = p.size
        w = max(w, _w)
    des = Image.new('RGBA', (w, sum(h) + (num-1) * border),
                    (255, 255, 255, t))
    for i, pic in enumerate(pics):
        des.paste(pic, (0,  (sum(h[:i]) + i * border)), pic)
    return des


def tlen(text: str, font_size: int):
    length = 0
    for i in text:
        if i == '\n':
            continue
        if i in '-':
            length += font_size / 3
        elif re.search(r'[a-z]', i) or i in '=][ ':
            length += font_size / 2
        elif re.search(r'[0-9]', i):
            length += font_size*7 / 10
        elif re.search(r'[A-Z]', i):
            length += font_size*2 / 3
        else:
            length += font_size
    return round(length+0.5)

def normalize_str(string) -> str:
    """
    规范化unicode字符串 并 转为小写 并 转为简体
    """
    string = unicodedata.normalize('NFKC', string)
    string = string.lower()
    string = zhconv.convert(string, 'zh-hans')
    return string


MONTH_NAME = ('睦月', '如月', '弥生', '卯月', '皐月', '水無月',
              '文月', '葉月', '長月', '神無月', '霜月', '師走')


def month_name(x: int) -> str:
    return MONTH_NAME[x - 1]


DATE_NAME = (
    '初一', '初二', '初三', '初四', '初五', '初六', '初七', '初八', '初九', '初十',
    '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十',
    '廿一', '廿二', '廿三', '廿四', '廿五', '廿六', '廿七', '廿八', '廿九', '三十',
    '卅一'
)


def date_name(x: int) -> str:
    return DATE_NAME[x - 1]


NUM_NAME = (
    '〇〇', '〇一', '〇二', '〇三', '〇四', '〇五', '〇六', '〇七', '〇八', '〇九',
    '一〇', '一一', '一二', '一三', '一四', '一五', '一六', '一七', '一八', '一九',
    '二〇', '二一', '二二', '二三', '二四', '二五', '二六', '二七', '二八', '二九',
    '三〇', '三一', '三二', '三三', '三四', '三五', '三六', '三七', '三八', '三九',
    '四〇', '四一', '四二', '四三', '四四', '四五', '四六', '四七', '四八', '四九',
    '五〇', '五一', '五二', '五三', '五四', '五五', '五六', '五七', '五八', '五九',
    '六〇', '六一', '六二', '六三', '六四', '六五', '六六', '六七', '六八', '六九',
    '七〇', '七一', '七二', '七三', '七四', '七五', '七六', '七七', '七八', '七九',
    '八〇', '八一', '八二', '八三', '八四', '八五', '八六', '八七', '八八', '八九',
    '九〇', '九一', '九二', '九三', '九四', '九五', '九六', '九七', '九八', '九九',
)


def time_name(hh: int, mm: int) -> str:
    return NUM_NAME[hh] + NUM_NAME[mm]


class FreqLimiter:
    def __init__(self, default_cd_seconds):
        self.next_time = defaultdict(float)
        self.default_cd = default_cd_seconds

    def check(self, key) -> bool:
        return bool(time.time() >= self.next_time[key])

    def start_cd(self, key, cd_time=0):
        self.next_time[key] = time.time() + (cd_time if cd_time >
                                             0 else self.default_cd)

    def left_time(self, key) -> float:
        return self.next_time[key] - time.time()


class DailyNumberLimiter:
    tz = pytz.timezone('Asia/Shanghai')

    def __init__(self, max_num):
        self.today = -1
        self.count = defaultdict(int)
        self.max = max_num

    def check(self, key) -> bool:
        now = datetime.now(self.tz)
        day = (now - timedelta(hours=5)).day
        if day != self.today:
            self.today = day
            self.count.clear()
        return bool(self.count[key] < self.max)

    def get_num(self, key):
        return self.count[key]

    def increase(self, key, num=1):
        self.count[key] += num

    def reset(self, key):
        self.count[key] = 0


gfw = DFAFilter()
gfw.parse(os.path.join(os.path.dirname(__file__),
                       'textfilter/sensitive_words.txt'))


def filt_message(message: Union[Message, str]):
    if isinstance(message, str):
        return gfw.filter(message)
    elif isinstance(message, Message):
        for seg in message:
            if seg.type == 'text':
                seg.data['text'] = gfw.filter(seg.data.get('text', ''))
        return message
    else:
        raise TypeError


def add_delay_job(task, id=None, delay_time: int = 30, args=[]):
    now = datetime.now()
    job = scheduler.add_job(task,
                            'date',
                            id=id,
                            run_date=now +
                            timedelta(seconds=delay_time),
                            misfire_grace_time=5,
                            args=args)
    return job


def add_date_job(task, id=None, run_date=None, args=[]):
    job = scheduler.add_job(task, 'date', id=id, run_date=run_date, args=args)
    return job


def add_cron_job(task, id=None, hour='*', minute='0', second='0', args=[]):
    job = scheduler.add_job(task,
                            'cron',
                            id=id,
                            hour=hour,
                            minute=minute,
                            second=second,
                            misfire_grace_time=5,
                            args=args)
    return job


def poke(uid):
    return MessageSegment(type_='poke', data={'qq': str(uid), })


async def poke_in_session(session, uid=None):
    if uid is None:
        uid = session['user_id']
    await session.send(poke(uid))


async def poke_in_event(bot, ev, uid=None):
    if uid is None:
        uid = ev.user_id
    await bot.send(ev, poke(uid))


def gencardimage(file, source=None, icon=None):
    source = f',source={source}' if source else ''
    icon = f',icon={icon}' if icon else ''
    return f'[CQ:cardimage,file={file}{source}{icon}]'
