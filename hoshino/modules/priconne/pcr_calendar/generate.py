import math
import asyncio
import datetime
import base64
from io import BytesIO
from .event import *
from .draw import *
from hoshino import util
server_name = {
    'cn': '国服',
    'tw': '台服',
    'jp': '日服',
}


async def generate_day_schedule(server='cn', clanb=True):
    events = await get_events(server, 0, 7)
    if not clanb:
        for event in events:
            if event['type'] == 3:
                events.remove(event)
    has_prediction = False
    for event in events:
        if event['start_days'] > 0:
            has_prediction = True
    if has_prediction:
        im = create_image(len(events) + 2)
    else:
        im = create_image(len(events) + 1)

    title = f'公主连结{server_name[server]}活动'
    pcr_now = get_pcr_now(0)
    draw_title(im, 0, title, pcr_now.strftime('%Y/%m/%d'), '正在进行')

    if len(events) == 0:
        draw_item(im, 1, 1, '无数据', 0)
    i = 1
    for event in events:
        if event['start_days'] <= 0:
            draw_item(im, i, event['type'], event['title'], event['left_days'])
            i += 1
    if has_prediction:
        draw_title(im, i, right='即将开始')
        for event in events:
            if event['start_days'] > 0:
                i += 1
                draw_item(im, i, event['type'],
                          event['title'], -event['start_days'])
    return im
