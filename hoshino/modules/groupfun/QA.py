import os
import peewee as pw
from hoshino.typing import CQEvent
from aiocqhttp import Message
import random
from hoshino import Service, priv, R
from hoshino.Gm import Gm
globalQ = set()
groupQ = {}
userQ = {}
groupuserQ = {}
sv = Service('QA', manage_priv=priv.ADMIN, enable_on_default=False, help_='''
我问你答，调教time！（bushi
ps：请不要教太多奇怪的东西！
[我问xxx你答yyy] 添加问答
*每个人每个群数据独立
[有人问xxx你答yyy] 添加群内全局问答(管理员限定)
------如果希望多个答案随机回答可将“你答”改为“你随机答”一个一个添加
[看看我问] 看看本群个人问题
[看看有人问] 看看本群全局问题
[不要回答xxx] 删除回答，多个答案要一个一个删'''.strip())

dbpath = os.path.expanduser('~/.hoshino/QA.db')
os.makedirs(os.path.dirname(dbpath), exist_ok=True)
db = pw.SqliteDatabase(dbpath)


class QA(pw.Model):
    quest = pw.TextField()
    answer = pw.TextField(default='')
    gid = pw.IntegerField(default=0)  # 0 for none and 1 for all
    uid = pw.IntegerField(default=0)
    create_time = pw.TimestampField()

    class Meta:
        database = db
        primary_key = pw.CompositeKey('quest', 'gid', 'uid', 'create_time')


def init():
    if not os.path.exists(dbpath):
        db.connect()
        db.create_tables([QA])
        db.close()


init()
# recovery from database


def cacheinit(gid, uid):
    if gid not in groupQ:
        groupQ[gid] = set()
    if uid not in userQ:
        userQ[uid] = set()
    if gid not in groupuserQ:
        groupuserQ[gid] = {uid: set()}
    elif uid not in groupuserQ[gid]:
        groupuserQ[gid][uid] = set()


def recovery():
    for qu in QA.select():
        cacheinit(qu.gid, qu.uid)
        if qu.uid == 1:
            if qu.gid == 1:
                globalQ.add(qu.quest)
            else:
                groupQ[qu.gid].add(qu.quest)
        else:
            if qu.gid == 1:
                userQ[qu.uid].add(qu.quest)
            else:
                groupuserQ[qu.gid][qu.uid].add(qu.quest)


recovery()


async def stor_pic(msg: str, stor=True) -> str:
    msg = Message(msg)
    for i in msg:
        if i['type'] == 'image':
            if stor:
                img = await R.download_img_form_msg(i, 'QA')
                i['data']['file'] = img.file + img.suffix
            i['data'].pop('url')
    return str(msg)


async def storQA(bot, ev: CQEvent, gid: int, uid: int) -> str:
    msg = str(ev.message).split('你答', 1)
    single = True
    if len(msg) != 2:
        msg = str(ev.message).split('你随机答', 1)
        single = False
        if len(msg) != 2:
            return
    if msg[0] == '':
        await bot.finish(ev, '问题不能为空哦')
    if msg[1] == '':
        await bot.finish(ev, '回答不能为空哦')
    if Gm.check_command(msg[0]):
        await bot.finish(ev, '与指令冲突哦')
    Qu = await stor_pic(msg[0], False)
    An = await stor_pic(msg[1])
    try:
        if single:
            QAdata = QA.get_or_create(
                quest=Qu,
                gid=gid,
                uid=uid,
            )[0]
            QAdata.answer = An
            QAdata.save()
        else:
            QA.replace(
                quest=Qu,
                gid=gid,
                uid=uid,
                answer=An,
            ).execute()
        await bot.send(ev, '好的我记住了')
        return Qu
    except Exception as e:
        await bot.send(ev, f'存入数据库时出现了问题...{e}')


def load_pic(An: str) -> str:
    An = Message(An)
    for i in An:
        if i['type'] == 'image':
            i['data']['file'] = r'file:///' + R.tem_img('QA',
                                                        i['data']['file']).path
    return str(An)


def del_pic(An: str):
    An = Message(An)
    for i in An:
        if i['type'] == 'image':
            R.tem_img('QA', i['data']['file']).delete()


async def delqa(bot, ev: CQEvent, Qu: str, gid: int, uid: int):
    if (i := QA.get_or_none(quest=Qu, uid=uid, gid=gid)):
        An = i.answer
        Ans = load_pic(An)
        i.delete_instance()
        if not QA.get_or_none(quest=Qu, uid=uid, gid=gid):
            if uid == 1:
                if gid == 1:
                    globalQ.discard(Qu)
                else:
                    groupQ[gid].discard(Qu)
            else:
                if gid == 1:
                    userQ[uid].discard(Qu)
                else:
                    groupuserQ[gid][uid].discard(Qu)
        await bot.send(ev, f'我不再回答{Ans}了')
        del_pic(An)
        await bot.finish(ev)


@sv.on_prefix('我本群问')
async def addGUQA(bot, ev: CQEvent):
    uid = ev.user_id
    gid = ev.group_id
    cacheinit(gid, uid)
    Qu = await storQA(bot, ev, gid, uid)
    groupuserQ[gid][uid].add(Qu)


@sv.on_prefix('我问', '我说')
async def addUQA(bot, ev: CQEvent):
    uid = ev.user_id
    cacheinit(ev.group_id, uid)
    Qu = await storQA(bot, ev, 1, uid)
    userQ[uid].add(Qu)


@sv.on_prefix('有人问', '大家问')
async def addGQA(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '管理员才能使用有人问哦')
    gid = ev.group_id
    cacheinit(gid, ev.user_id)
    Qu = await storQA(bot, ev, gid, 1)
    groupQ[gid].add(Qu)


@sv.on_prefix('全局有人问')
async def addAQA(bot, ev: CQEvent):
    if priv.check_priv(ev, priv.SUPERUSER):
        Qu = await storQA(bot, ev, 1, 1)
        globalQ.add(Qu)


@sv.on_prefix('不要回答', '删除问答')
async def delQA(bot, ev: CQEvent):
    Qu = await stor_pic(str(ev.message), False)
    gid = ev.group_id
    cacheinit(ev.group_id, ev.user_id)
    if priv.check_priv(ev, priv.SUPERUSER) and Qu in globalQ:
        await delqa(bot, ev, Qu, 1, 1)
    gid = ev.group_id
    if priv.check_priv(ev, priv.ADMIN) and Qu in groupQ[gid]:
        await delqa(bot, ev, Qu, gid, 1)
    uid = ev.user_id
    if Qu in userQ[uid]:
        await delqa(bot, ev, Qu, 1, uid)
    if Qu in groupuserQ[gid][uid]:
        await delqa(bot, ev, Qu, gid, uid)


@sv.on_fullmatch('看看有人问')
async def lookgQA(bot, ev: CQEvent):
    cacheinit(ev.group_id, ev.user_id)
    Qlist = globalQ.union(groupQ[ev.group_id])
    Qlist = ' | '.join(Qlist)
    await bot.send(ev, '本群的问题有：\n'+Qlist)


@sv.on_fullmatch('看看我问')
async def lookuQA(bot, ev: CQEvent):
    uid = ev.user_id
    gid = ev.group_id
    cacheinit(gid, uid)
    Qlist = userQ[uid].union(groupuserQ[gid][uid])
    Qlist = ' | '.join(Qlist)
    await bot.send(ev, '的问题有：\n'+Qlist, at_sender=True)


@sv.on_message('group')
async def QandA(bot, ev: CQEvent):
    msg = await stor_pic(str(ev.message), False)
    gid = ev.group_id
    uid = ev.user_id
    cacheinit(gid, uid)
    if msg in globalQ:
        gid = 1
        uid = 1
    elif msg in groupQ[gid]:
        uid = 1
    elif msg in userQ[uid]:
        gid = 1
    elif msg not in groupuserQ[gid][uid]:
        return
    An = QA.select(QA.answer).where(QA.quest == msg,
                                    QA.gid == gid,
                                    QA.uid == uid)
    An = [load_pic(i.answer) for i in An]
    await bot.send(ev, random.choice(An))
