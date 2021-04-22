from hoshino.service import Service
from hoshino.config.setu import client_id, client_secret
from hoshino import aiorequests
from hoshino.typing import CQEvent
import requests
'''
图像审核接口
'''
access_token = ''
sv = Service('setucheck', bundle='setu')
host = f'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}'
response = requests.get(host)
access_token = response.json()["access_token"]
request_url = "https://aip.baidubce.com/rest/2.0/solution/v1/img_censor/v2/user_defined"
request_url = request_url + "?access_token=" + access_token
headers = {'content-type': 'application/x-www-form-urlencoded'}

retmsg = {
    'type': {
        1: '不够涩',
        2: '鉴定完成',
        3: '鉴定完成',
        4: '审核失败',
    },
    'subtype': {
        0: '一般色情',
        1: '二次元色情',
        2: 'SM',
        3: '低俗',
        4: '儿童裸露',
        9: '女性性感',
        10: '二次元性感',
        12: '亲密行为',
        13: '二次元行为',
        15: '臀部特写',
        16: '脚部特写',
        17: '裆部特写'
    }
}


async def checker(imgurl, msgid):
    params = {"imgUrl": imgurl}
    resp = await aiorequests.post(request_url, data=params, headers=headers)
    if resp.ok:
        data = await resp.json()
        print(data)
        msg = [retmsg['type'][data["conclusionType"]]]
        if data["conclusionType"] in (2, 3):
            for i in data['data']:
                if i['type'] == 1 and i['subType'] in retmsg['subtype']:
                    msg.append(
                        f"{retmsg['subtype'][i['subType']]}指数：{i['probability']}")
        msg = '\n'.join(msg)
        msg = f'[CQ:reply,id={msgid}]'+msg
        return msg


class PicListener:
    def __init__(self):
        self.on = {}

    def get_on_off_status(self, gid, uid):
        if gid not in self.on:
            self.on[gid] = []
            return False
        else:
            return uid in self.on[gid]

    def turn_on(self, gid, uid):
        if gid not in self.on:
            self.on[gid] = [uid]
        else:
            self.on[gid].append(uid)

    def turn_off(self, gid, uid):
        if gid not in self.on:
            self.on[gid] = []
        elif uid in self.on[gid]:
            self.on[gid].remove(uid)


pls = PicListener()


@sv.on_prefix(('涩图鉴定', '色图鉴定', '瑟图鉴定'), only_to_me=True)
async def checkswitch(bot, ev: CQEvent):
    ret = []
    gid = ev.group_id
    uid = ev.user_id
    kw = ev.message.extract_plain_text().strip()
    for i in ev.message:
        if i['type'] == 'image':
            ret.append(i['data']['url'])
            break
    if not ret:
        if pls.get_on_off_status(gid, uid):
            if kw == '关闭':
                pls.turn_off(gid, uid)
                await bot.finish(ev, "鉴定模式已关闭！")
            await bot.finish(ev, "您已经在鉴定模式下啦！\n如想退出鉴定模式请发送“#涩图鉴定关闭”~")
        pls.turn_on(gid, uid)
        await bot.send(ev, "了解～请发送图片吧！支持批量噢！\n如想退出鉴定模式请发送“#涩图鉴定关闭”")
    for i in ret:
        msg = await checker(i, ev.message_id)
        await bot.send(ev, msg)

@sv.on_message('group')
async def picmessage(bot, ev: CQEvent):
    if not pls.get_on_off_status(ev.group_id, ev.user_id):
        return
    ret = []
    for i in ev.message:
        if i['type'] == 'image':
            ret.append(i['data']['url'])
    if not ret:
        return
    for i in ret:
        msg = await checker(i, ev.message_id)
        await bot.send(ev, msg)

#@sv.on_replay(startwith='打分')
async def testrep(bot, ev: CQEvent):
    kw = ev['rep_message'].extract_plain_text().strip().split()
    ind = 0
    for i in ev['quote_message']['message']:
        if i['type'] == 'image' and ind <= len(kw):
            await bot.send(ev, f'{i},{kw[ind]}分')
            ind += 1
