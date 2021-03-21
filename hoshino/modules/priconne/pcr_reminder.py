from hoshino.service import Service, SubService
from hoshino import R
import random
sv = Service('pcr-reminder', enable_on_default=True,
             help_='PCR提醒小助手', bundle='pcr订阅', visible=False)
svtw = SubService('pcr-arena-reminder-tw', sv,
                  enable_on_default=False, help_='背刺时间提醒(台B)')
svjp = SubService('pcr-arena-reminder-jp', sv,
                  enable_on_default=False, help_='背刺时间提醒(日)')
svexpt = SubService('pcr-exp-reminder-tw', sv,
                    enable_on_default=False, help_='提醒买药小助手(台B)')
svclant = SubService('pcr-clan-reminder-tw', sv,
                     enable_on_default=False, help_='提醒会战小助手(台)',
                     visible=False)
msgbc = '主さま、准备好背刺了吗？'
msgclan = '[CQ:at,id=all]主さま、公会战要开始了哦，和伙伴一起努力吧'
msgclanp = R.img('kkl/daghuizhanle.jpg').cqcode
msgclanend = '主さま、公会战快要结束了哦'


@svtw.scheduled_job('cron', hour='14', minute='45')
async def pcr_reminder_tw():
    await svtw.broadcast(msgbc, 'pcr-reminder-tw', 0.2)


@svjp.scheduled_job('cron', hour='13', minute='45')
async def pcr_reminder_jp():
    await svjp.broadcast(msgbc, 'pcr-reminder-jp', 0.2)


@svexpt.scheduled_job('cron', hour='0,6,12,18')
async def pcr_expreminder_tw():
    await svexpt.broadcast(R.img(
        f'kkl/exp{random.randint(1, 6)}.jpg').cqcode,
        'pcr-expreminder-tw', 0.2)


@svclant.scheduled_job('cron', month='4,6,9,11', day='25', hour='4', minute='59')
@svclant.scheduled_job('cron', month='1,3,5,7,8,10,12', day='26', hour='4', minute='59')
@svclant.scheduled_job('cron', month='2', day='23', hour='4', minute='59')
async def pcr_clanstreminder_tw():
    await svclant.broadcast(msgclan, 'pcr-clanreminder-tw', 0.2)


@svclant.scheduled_job('cron', month='4,6,9,11', day='25-29', hour='5')
@svclant.scheduled_job('cron', month='1,3,5,7,8,10,12', day='26-30', hour='5')
@svclant.scheduled_job('cron', month='2', day='23-27', hour='5')
async def pcr_clanreminder_tw():
    await svclant.broadcast(msgclanp, 'pcr-clanreminder-tw', 0.2)


@svclant.scheduled_job('cron', month='4,6,9,11', day='29', hour='23')
@svclant.scheduled_job('cron', month='1,3,5,7,8,10,12', day='30', hour='23')
@svclant.scheduled_job('cron', month='2', day='27', hour='23')
async def pcr_clanendreminder_tw():
    await svclant.broadcast(msgclanend, 'pcr-clanreminder-tw', 0.2)
