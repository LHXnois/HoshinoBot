import re
import random
import datetime
from random import choice
from PIL import Image, ImageDraw, ImageFilter

from hoshino import R, Service
from hoshino.util import pic2b64, FreqLimiter
from hoshino.typing import CQEvent, MessageSegment
from hoshino.Groupmaster import Groupmaster as Gm

sv = Service('generator', help_='''
生成器
[#营销号 主体/事件/另一种说法] 营销号生成器
[#狗屁不通 主题] 狗屁不通生成器
[#记仇 天气/主题] 记仇表情包生成器
[我朋友说他好了] 无中生友，无艾特时随机群员
[#报时] 现在几点了？
[#rua@目标] 群友搓一搓，生活乐趣多
'''.strip(), bundle='fun')

_flmt = FreqLimiter(300)


def measure(msg, font_size, img_width):
    i = 0
    length = 0
    measured_msg = []
    while i < len(msg):
        if re.search(r'[0-9a-zA-Z]', msg[i]):
            length += font_size // 2
        else:
            length += font_size
        if length >= img_width:
            measured_msg.append(msg[:i])
            msg = msg[i:]
            length = 0
            i = 1
        i += 1
    measured_msg.append(msg)
    return '\n'.join(measured_msg)


@sv.on_prefix(('营销号'))
async def yxh(bot, ev: CQEvent):
    kw = ev.message.extract_plain_text().strip()
    arr = kw.split('/')
    if not arr[2]:
        return
    msg = f'    {arr[0]}{arr[1]}是怎么回事呢？{arr[0]}相信大家都很熟悉，但是'\
        f'{arr[0]}{arr[1]}是怎么回事呢，下面就让可可萝带大家一起了解吧。\n    {arr[0]}{arr[1]}，其实'\
        f'就是{arr[2]}，大家可能会很惊讶{arr[0]}怎么会{arr[1]}呢？但事实就是这样，可可萝也感到非常惊讶。\n'\
        f'    这就是关于{arr[0]}{arr[1]}的事情了，大家有什么想法呢，欢迎在群里告诉可可萝一起讨论哦！'
    await bot.send(ev, msg)


@sv.on_prefix(('狗屁不通'))
async def gpbt(bot, ev: CQEvent):
    data = R.data('groupfun/generator/gpbt.json', 'json').read
    title = ev.message.extract_plain_text().strip()
    length = 500
    body = ""
    while len(body) < length:
        num = random.randint(0, 100)
        if num < 10:
            body += "\r\n"
        elif num < 20:
            body += random.choice(data["famous"]) \
                .replace('a', random.choice(data["before"])) \
                .replace('b', random.choice(data['after']))
        else:
            body += random.choice(data["bosh"])
        body = body.replace("x", title)
    await bot.send(ev, body)


@sv.on_prefix(('记仇'))
async def jc(bot, ev: CQEvent):
    kw = ev.message.extract_plain_text().strip()
    arr = kw.split('/')
    image = R.img('groupfun/generator', 'jichou.jpg').open()
    # 创建Font对象:
    font = R.font('simhei.ttf').open(size=80)

    time = datetime.datetime.now().strftime('%Y年%m月%d日')
    msg = f'{time}，{arr[0]}，{arr[1]}，这个仇我先记下了'
    place = 12
    line = len(msg.encode('utf-8')) // place + 1

    msg = measure(msg, 80, 974)

    # 创建Draw对象:
    image_text = Image.new('RGB', (974, 32 * line), (255, 255, 255))
    draw = ImageDraw.Draw(image_text)
    draw.text((0, 0), msg, fill=(0, 0, 0), font=font)
    # 模糊:
    image_text = image_text.filter(ImageFilter.BLUR)
    image_back = Image.new('RGB', (974, 32 * line + 764), (255, 255, 255))
    image_back.paste(image, (0, 0))
    image_back.paste(image_text, (0, 764))

    await bot.send(ev, str(MessageSegment.image(pic2b64(image_back))))


@sv.on_rex(('^我(有个|一个|有一个)*朋友(想问问|说|让我问问|想问|让我问|想知道|'
            '让我帮他问问|让我帮他问|让我帮忙问|让我帮忙问问|问)*(?P<kw>.{0,30}$)'), only_to_me=True)
async def friend(bot, ev: CQEvent):
    if ev.user_id not in bot.config.SUPERUSERS:
        # 定义非管理员的冷却时间
        if not _flmt.check(ev.user_id):
            return
        _flmt.start_cd(ev.user_id)
    data = R.data('groupfun/generator/config.json', 'json').read
    arr = []
    is_at = False
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            arr = [int(m.data['qq'])]
            is_at = True
    if not is_at:
        try:
            arr = data[f'{ev.group_id}']
        except Exception:
            arr = await Gm(ev).member_list()
    match = ev['match']
    msg = match.group('kw')
    msg = msg.replace('他', '我').replace('她', '我')
    image = await R.avatar(choice(arr))
    image = image.open()
    img_origin = Image.new('RGBA', (100, 100), (255, 255, 255))
    scale = 3
    # 使用新的半径构建alpha层
    r = 100 * scale
    alpha_layer = Image.new('L', (r, r), 0)
    draw = ImageDraw.Draw(alpha_layer)
    draw.ellipse((0, 0, r, r), fill=255)
    # 使用ANTIALIAS采样器缩小图像
    alpha_layer = alpha_layer.resize((100, 100), Image.ANTIALIAS)
    img_origin.paste(image, (0, 0), alpha_layer)

    # 创建Font对象:
    font = R.font('simhei.ttf').open(size=30)
    font2 = R.font('simhei.ttf').open(size=25)

    # 创建Draw对象:
    image_text = Image.new('RGB', (450, 150), (255, 255, 255))
    draw = ImageDraw.Draw(image_text)
    draw.text((0, 0), '朋友', fill=(0, 0, 0), font=font)
    draw.text((0, 40), msg, fill=(125, 125, 125), font=font2)

    image_back = Image.new('RGB', (700, 150), (255, 255, 255))
    image_back.paste(img_origin, (25, 25))
    image_back.paste(image_text, (150, 40))

    await bot.send(ev, str(MessageSegment.image(pic2b64(image_back))))


@sv.on_prefix(('rua', '搓'), only_to_me=True)
async def rua(bot, ev: CQEvent):
    is_at = False
    arr = []
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            arr = [int(m.data['qq'])]
            is_at = True
    if not is_at:
        arr.append(ev.self_id)
        arr.append(ev.user_id)
    avatar_origin = (await R.avatar(choice(arr), 160)).open()
    avatar_origin = R.get_circle_pic(avatar_origin, 350)
    avatar_size = [(350, 350), (372, 305), (395, 283), (380, 305), (350, 372)]
    avatar_pos = [(50, 100), (28, 145), (5, 167), (5, 145), (50, 78)]
    hand_pos = (0, -50)
    imgs = []
    for i in range(5):
        im = Image.new(mode='RGBA', size=(500, 500))
        hand = R.img('groupfun/generator', f'rua/hand-{i+1}.png').open()
        hand = hand.convert('RGBA')
        avatar = avatar_origin.copy()
        avatar = avatar.resize(avatar_size[i])
        im.paste(avatar, avatar_pos[i], mask=avatar.split()[3])
        im.paste(hand, hand_pos, mask=hand.split()[3])
        mask = im.split()[3]
        mask = Image.eval(mask, lambda a: 255 if a <= 50 else 0)
        # maskpath = R.img('groupfun/generator', f'rua/mask-{i+1}.jpg').path
        # mask.save(maskpath)
        # mask = R.img('groupfun/generator', f'rua/mask-{i+1}.jpg').open()
        im = im.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255)
        im.paste(255, mask)
        imgs.append(im)
    result = R.tem_img('groupfun/generator', 'rua/output.gif')
    imgs[0].save(fp=result.path, save_all=True, append_images=imgs,
                 loop=0, duration=10, quality=80, transparency=255, disposal=3)
    await bot.send(ev, result.cqcode)


@sv.on_keyword(('报时', '几点了', '现在几点', '几点钟啦', '几点啦'), only_to_me=True)
async def showtime(bot, ev):
    now = datetime.datetime.now()
    hour = now.hour
    minute = now.minute
    hour_str = f' {hour}' if hour < 10 else str(hour)
    minute_str = f' {minute}' if minute < 10 else str(minute)
    originpic = R.img('groupfun/generator/nowtime.jpg').open()
    outputpic = R.tem_img('groupfun/generator/nowtime.jpg')
    img = R.add_text(originpic, f'{hour_str}点{minute_str}分',
                     textsize=95, textfill='black', position=(305, 255))
    img.save(outputpic.path)
    await bot.send(ev, outputpic.cqcode, at_sender=False)
