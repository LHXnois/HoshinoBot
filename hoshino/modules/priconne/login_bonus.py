import random
from hoshino import Service, R
from hoshino.typing import CQEvent
from hoshino.util import DailyNumberLimiter, escape
from .pcrColleciton import pcrCoins

sv = Service('pcr-login-bonus', bundle='pcr娱乐', help_='[星乃签到] 给主さま盖章章')

lmt = DailyNumberLimiter(1)
login_presents = [
    '扫荡券×5',  '特级EXP药水×10', '普通EXP药水×5',  '上级精炼石×8',
    '扫荡券×10', '特级EXP药水×15', '普通EXP药水×15', '上级精炼石×15',
    '扫荡券×15', '特级EXP药水×20', '上级精炼石×3',   '白金转蛋券×1',
]
login_jewel = [
    50, 100, 150, 300, 500, 1000, 1500, 3000, 5000, 8000, 10000, 20000,
    50, 50, 50, 50, 50, 50, 50, 50, 100, 100, 100, 100, 100, 150, 150,
    300, 300, 500, 500, 1000, 1500, 3000,
]
todo_list = [
    '找伊绪老师上课',
    '给宫子买布丁',
    '和真琴寻找伤害优衣的人',
    '找镜哥探讨女装',
    '跟吉塔一起登上骑空艇',
    '和霞一起调查伤害优衣的人',
    '和佩可小姐一起吃午饭',
    '找小小甜心玩过家家',
    '帮碧寻找新朋友',
    '去真步真步王国',
    '找镜华补习数学',
    '陪胡桃排练话剧',
    '和初音一起午睡',
    '成为露娜的朋友',
    '帮铃莓打扫咲恋育幼院',
    '和静流小姐一起做巧克力',
    '去伊丽莎白农场给栞小姐送书',
    '观看慈乐之音的演出',
    '解救挂树的队友',
    '来一发十连',
    '井一发当期的限定池',
    '给妈妈买一束康乃馨',
    '购买黄金保值',
    '竞技场背刺',
    '给别的女人打钱',
    '氪一单',
    '努力工作，尽早报答妈妈的养育之恩',
    '成为魔法少女',
    '搓一把日麻'
]


@sv.on_fullmatch(('签到', '盖章', '妈', '妈?', '妈妈', '妈!', '妈！', '妈妈！', '盖章章'), only_to_me=True)
async def give_okodokai(bot, ev: CQEvent):
    uid = ev.user_id
    if not lmt.check(uid):
        await bot.send(ev, '明日はもう一つプレゼントをご用意してお待ちしますね', at_sender=True)
        return
    lmt.increase(uid)
    present = random.choice(login_presents)
    jewel = random.choice(login_jewel)
    pcrCoins(ev.user_id, '宝石').add_C(jewel)
    todo = random.choice(todo_list)
    await bot.send(ev, f'\nおかえりなさいませ、主さま{R.img("priconne/kokkoro_stamp.png").cqcode}\n{present}を獲得しました\n随机获得宝石×{jewel}\n私からのプレゼントです\n主人今天要{todo}吗？', at_sender=True)

@sv.on_fullmatch('我的宝石')
async def my_jewel(bot, ev: CQEvent):
    jewel = pcrCoins(ev.user_id, '宝石').cnum
    user = ev.sender['card']
    if not user:
        user = ev.sender['nickname']
    msg = f'\n {user} ======= 宝石：{jewel} ======='.split()
    await bot.send(ev, escape('\n'.join(msg)), at_sender=True)