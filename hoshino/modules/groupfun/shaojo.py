import random
from hoshino import Service, R
from hoshino.typing import CQEvent
import time

date = True
sv = Service('2d_girl', enable_on_default=True, help_='''今天也是少女!
[今天我是什么少女] 看看今天你是什么少女
[@xxx今天是什么少女] 看看xxx今天是什么少女''', bundle='fun')


def format_msg(qq: int, name):
    data = R.data('groupfun', 'shaojo.json').read
    face_style = data['face_style']
    height = data['height']
    breast_size = data['breast_size']
    hair_style = data['hair_style']
    daimao = data['daimao']
    color = data['color']
    color_hair = color+data['color_haironly']
    likelycolor = data['likelycolor']
    job = data['job']
    property = data['property']
    random.seed(qq * (int(time.time()/3600/24) if date else 1))
    msg = [f'二次元少女的{name}']
    msg.append(f'长着{random.choice(face_style)}')
    msg.append(f'身高{random.choice(height)}')
    haircolor = random.sample(color_hair, 3)
    for i, c in enumerate(haircolor):
        if c in likelycolor and random.random() < 0.5:
            haircolor[i] = likelycolor[c]
    msg.append(f'{haircolor[0]}{random.choice(hair_style)}')
    if '长' in msg[-1] and random.random() < 0.01:
        msg.append(f'发梢向{haircolor[1]}渐变')
    if random.random() < 0.01:
        msg.append(f'有一缕头发是{haircolor[2]}的')
    if random.random() < 0.3:
        msg.append(f'有{random.choice(daimao)}呆毛')
    msg.append(f'{random.choice(breast_size)}')
    eyecolor = random.sample(color, 2)
    for i, c in enumerate(eyecolor):
        if c in likelycolor and random.random() < 0.5:
            eyecolor[i] = likelycolor[c]
    if random.random() < 0.1:
        msg.append(f'异色瞳，左眼{"右眼".join(eyecolor)}')
    else:
        msg.append(f'瞳色{eyecolor[0]}')
    msg.append(f'{"和".join(random.sample(property, 2))}属性')
    if random.random() < 0.01:
        i = 2
        msg.append(f'多重人格，第2个人格是{"和".join(random.sample(property, 2))}属性')
        while random.random() < 0.4:
            i += 1
            msg.append(f'第{i}个人格是{"和".join(random.sample(property, 2))}属性')
    race = '猫耳' if random.random() < 0.1 else ''
    msg.append(f'是{race}{random.choice(job)}')
    return '，'.join(msg)


@sv.on_fullmatch('今天我是什么少女')
async def my_shoujo(bot, ev: CQEvent):
    uid = ev.user_id
    name = ev.sender['card'] or ev.sender['nickname']
    msg = format_msg(uid, name)
    await bot.send(ev, msg)


@sv.on_prefix('今天是什么少女')
@sv.on_suffix('今天是什么少女')
async def other_shoujo(bot, ev: CQEvent):
    arr = []
    for i in ev.message:
        if i['type'] == 'at' and i['data']['qq'] != 'all':
            arr.append(int(i['data']['qq']))
    gid = ev.group_id
    for uid in arr:
        info = await bot.get_group_member_info(
                group_id=gid,
                user_id=uid,
                no_cache=True
        )
        name = info['card'] or info['nickname']
        msg = format_msg(uid, name)
        await bot.send(ev, msg)
