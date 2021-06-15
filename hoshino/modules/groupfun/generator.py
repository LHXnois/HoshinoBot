import re
import random
import datetime
from random import choice
from PIL import Image, ImageDraw, ImageFilter
from urllib.parse import quote

from nonebot import message

from hoshino import R, Service
from hoshino.util import pic2b64, FreqLimiter
from hoshino.typing import CQEvent, MessageSegment, Callable
from hoshino.Gm import Gm

sv = Service('generator', help_='''
生成器
[#营销号 主体/事件/另一种说法] 营销号生成器
[#狗屁不通 主题] 狗屁不通生成器
[#记仇 天气/主题] 记仇表情包生成器
[我朋友说他好了] 无中生友，无艾特时随机群员
[#报时] 现在几点了？
[#rua@目标] 群友搓一搓，生活乐趣多
[#5k upper lower] 5k梗图生成
[#友情模式] 切换友情模式
[#炖@目标] 生活不易，炖群友出气
[#小心@目标] 绝对不可以和这种网友见面.jpg
[#狂粉@目标] 爱xx爱
[#丢@目标] 丢出去
[#精神支柱@目标] 精 神 支 柱 ！
[#撕@目标] 手撕xxx
[#狂蹭@目标] 蹭蹭蹭蹭蹭蹭
[#狂mua@目标] muamuamuamuamua
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


@sv.on_prefix('营销号', only_to_me=True)
async def yxh(bot, ev: CQEvent):
    kw = ev.message.extract_plain_text().strip()
    arr = kw.split('/')
    if not arr[2]:
        return
    msg = (f'    {arr[0]}{arr[1]}是怎么回事呢？{arr[0]}相信大家都很熟悉，但是'
           f'{arr[0]}{arr[1]}是怎么回事呢，下面就让可可萝带大家一起了解吧。\n    {arr[0]}{arr[1]}，其实'
           f'就是{arr[2]}，大家可能会很惊讶{arr[0]}怎么会{arr[1]}呢？但事实就是这样，可可萝也感到非常惊讶。\n'
           f'    这就是关于{arr[0]}{arr[1]}的事情了，大家有什么想法呢，欢迎在群里告诉可可萝一起讨论哦！')
    await bot.send(ev, msg)


@sv.on_prefix('狗屁不通', only_to_me=True)
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


@sv.on_prefix('记仇', only_to_me=True)
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


@sv.on_rex(('^我(有个|一个|有一个)*朋友(想问问|说|让我问问|想问|让我问|想知道|让我帮他问问|让我帮他问|让我帮忙问|让我帮忙问问|问)*(?P<kw>.{0,30}$)'))
async def friend(bot, ev: CQEvent):
    if ev.user_id not in bot.config.SUPERUSERS:
        # 定义非管理员的冷却时间
        if not _flmt.check(ev.user_id):
            return
        _flmt.start_cd(ev.user_id)
    arr = []
    is_at = False
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            arr = [int(m.data['qq'])]
            is_at = True
    if not is_at:
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


@sv.on_keyword('报时', '几点了', '现在几点', '几点钟啦', '几点啦', only_to_me=True)
async def showtime(bot, ev):
    now = datetime.datetime.now()
    hour = now.hour
    minute = now.minute
    hour_str = f' {hour}' if hour < 10 else str(hour)
    minute_str = f' {minute}' if minute < 10 else str(minute)
    originpic = R.img('groupfun/generator/nowtime.jpg').open()
    img = R.add_text(originpic, f'{hour_str}点{minute_str}分',
                     textsize=95, textfill='black', position=(305, 255))
    await bot.send(ev, MessageSegment.image(pic2b64(img)))


@sv.on_prefix('5k', '5K', only_to_me=True)
async def _5k(bot, ev: CQEvent):
    kw = ev.message.extract_plain_text().strip().split()
    if len(kw) == 2:
        url = f'https://gsapi.cyberrex.ml/image?top={quote(kw[0])}&bottom={quote(kw[1])}'
        #pic = await R.tem_img(
        #    'groupfun/generator', '5k.png').download(url)
        await bot.send(ev, MessageSegment.image(url))


@sv.on_prefix('低情商', only_to_me=True)
async def iq(bot, ev: CQEvent):
    kw = ev.message.extract_plain_text().strip().split('高情商')
    if len(kw) == 2:
        base = R.img('groupfun/generator', 'EQ.jpg').open()
        img = R.add_text(base, kw[0],
                         textsize=95, textfill='black', position=(10, 460))
        img = R.add_text(base, kw[1],
                         textsize=95, textfill='white', position=(480, 460))
        await bot.send(ev, MessageSegment.image(pic2b64(img)))


async def avatargen(bot, ev: CQEvent, type, gif=False, anum=1, **args):
    avatar = []
    for m in ev.message:
        if m.type == 'image':
            pic = await R.tem_img(
                'groupfun/generator/input', m.data['file']
                ).download(m.data['url'])
            avatar.append(R.crop_square(pic.open()))
        if m.type == 'at' and m.data['qq'] != 'all':
            avatar.append((await R.avatar(int(m.data['qq']), 160)).open())
        if len(avatar) >= anum:
            break
    else:
        if anum == 2:
            for uid in [ev.user_id, ev.self_id][:anum-len(avatar)]:
                avatar.append((await R.avatar(uid, 160)).open())
        elif anum == 1:
            avatar.append(
                (await R.avatar(choice([ev.user_id, ev.self_id]), 160)).open())
        else:
            await bot.finish(ev, '格式错误')
    if anum == 1:
        avatar = avatar[0]
    if gif:
        await bot.send(ev, typelist[type](avatar))
    else:
        await bot.send(ev, MessageSegment.image(pic2b64(typelist[type](avatar))))


typelist = {}


def avatargenadder(*cmd, **args) -> Callable:
    def deco(func) -> Callable:
        typelist[cmd[0]] = func

        @sv.on_prefix(*cmd, only_to_me=True)
        async def genfunc(bot, ev: CQEvent):
            await avatargen(bot, ev, cmd[0], **args)
        return func
    return deco


@avatargenadder('狂粉')
def kuangfen_gen(avatar: Image) -> Image:
    avatar = R.get_circle_pic(avatar, 101).convert('RGBA')
    base = R.img('groupfun/generator', 'kuangfen.jpg').open()
    base.paste(avatar, (90, 7), mask=avatar.split()[3])
    return base


@avatargenadder('炖')
def dun_gen(avatar: Image) -> Image:
    avatar_c = R.get_circle_pic(avatar, 110).convert('RGBA')
    base = R.img('groupfun/generator', 'dunu.png').open()
    base.paste(avatar_c, (51, 62), mask=avatar_c.split()[3])
    uppon = R.img('groupfun/generator', 'dunb.png').open()
    base.paste(uppon, mask=uppon.split()[3])
    base.paste(avatar.resize((25, 25)), (153, 219))
    return base


@avatargenadder('小心')
def xiaoxin_gen(avatar: Image) -> Image:
    base = R.img('groupfun/generator', 'xiaoxin.jpg').open()
    base.paste(avatar.resize((210, 210)), (0, 20))
    return base


@avatargenadder('友情模式')
def friend_gen(avatar: Image) -> Image:
    avatar = R.get_circle_pic(avatar, 160)
    mask = R.img('groupfun/generator', 'friend.png').open().resize((160, 160))
    im = Image.new(mode='RGBA', size=(160, 160))
    im.paste(avatar, mask=avatar)
    im.paste(mask, mask=mask.split()[3])
    return im


@avatargenadder('撕')
def tear_gen(avatar: Image) -> Image:
    tear = R.img('groupfun/generator', 'tear.png').open()
    frame = Image.new('RGBA', (1080, 804), (255, 255, 255, 0))
    left = avatar.resize((385, 385)).rotate(24, expand=True)
    right = avatar.resize((385, 385)).rotate(-11, expand=True)
    frame.paste(left, (-5, 355))
    frame.paste(right, (649, 310))
    frame.paste(tear, mask=tear)
    return frame


@avatargenadder('丢')
def throw_gen(avatar: Image) -> Image:
    avatar = R.get_circle_pic(avatar, 143)
    avatar = avatar.rotate(random.randint(1, 360), Image.BICUBIC)
    throw = R.img('groupfun/generator', 'throw.png').open()
    throw.paste(avatar, (15, 178), mask=avatar)
    return throw


@avatargenadder('心灵支柱', '精神支柱')
def support_gen(avatar: Image) -> Image:
    support = R.img('groupfun/generator', 'support.png').open()
    frame = Image.new('RGBA', (1293, 1164), (255, 255, 255, 0))
    avatar = avatar.resize((815, 815), Image.ANTIALIAS).rotate(23, expand=True)
    frame.paste(avatar, (-172, -17))
    frame.paste(support, mask=support)
    return frame


@avatargenadder('rua', '搓', gif=True)
def rua_gen(avatar_origin: Image) -> MessageSegment:
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
    return result.cqcode


@avatargenadder('狂mua', gif=True, anum=2)
def mua_gen(avatar: Image) -> MessageSegment:
    user_locs = [(58, 90), (62, 95), (42, 100), (50, 100), (56, 100), (18, 120),
                 (28, 110), (54, 100), (46, 100), (60, 100), (35, 115), (20, 120), (40, 96)]
    self_locs = [(92, 64), (135, 40), (84, 105), (80, 110), (155, 82), (60, 96),
                 (50, 80), (98, 55), (35, 65), (38, 100), (70, 80), (84, 65), (75, 65)]
    imgs = []
    avatar1 = R.get_circle_pic(avatar[0], 50)
    avatar2 = R.get_circle_pic(avatar[1], 40)
    for i in range(13):
        frame = R.img('groupfun/generator', f'kiss/frame{i}.png').open().convert('RGBA')
        x, y = user_locs[i]
        frame.paste(avatar1, (x, y), mask=avatar1)
        x, y = self_locs[i]
        frame.paste(avatar2, (x, y), mask=avatar2)
        imgs.append(frame)
    result = R.tem_img('groupfun/generator', 'kiss/output.gif')
    imgs[0].save(fp=result.path, save_all=True, append_images=imgs,
                 loop=0, duration=10, quality=80)
    return result.cqcode


@avatargenadder('狂蹭', gif=True, anum=2)
def ceng_gen(avatar: Image) -> MessageSegment:
    user_locs = [(39, 91, 75, 75, 0), (49, 101, 75, 75, 0), (67, 98, 75, 75, 0),
                 (55, 86, 75, 75, 0), (61, 109, 75, 75, 0), (65, 101, 75, 75, 0)]
    self_locs = [(102, 95, 70, 80, 0), (108, 60, 50, 100, 0), (97, 18, 65, 95, 0),
                 (65, 5, 75, 75, -20), (95, 57, 100, 55, -70), (109, 107, 65, 75, 0)]
    imgs = []
    avatar1 = R.get_circle_pic(avatar[0])
    avatar2 = R.get_circle_pic(avatar[1])
    for i in range(6):
        frame = R.img('groupfun/generator', f'rub/frame{i}.png').open().convert('RGBA')
        x, y, w, h, angle = user_locs[i]
        a1 = avatar1.resize((w, h), Image.ANTIALIAS).rotate(
            angle, Image.BICUBIC) if angle else avatar1.resize(
                (w, h), Image.ANTIALIAS)
        frame.paste(a1, (x, y), mask=a1)
        x, y, w, h, angle = self_locs[i]
        a2 = avatar2.resize((w, h), Image.ANTIALIAS).rotate(
            angle, Image.BICUBIC) if angle else avatar2.resize(
                (w, h), Image.ANTIALIAS)
        frame.paste(a2, (x, y), mask=a2)
        imgs.append(frame)
    result = R.tem_img('groupfun/generator', 'kiss/output.gif')
    imgs[0].save(fp=result.path, save_all=True, append_images=imgs,
                 loop=0, duration=10, quality=80)
    return result.cqcode
