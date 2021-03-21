import asyncio
from os.path import split
import random
import re
from collections import defaultdict
from datetime import datetime
from functools import partial, wraps

import pytz
from nonebot import MessageSegment as ms
from TwitterAPI import TwitterAPI, TwitterResponse

import hoshino
from hoshino import util, Service, priv, R
from hoshino.typing import CQEvent
from hoshino.config import twitter as cfg
from hoshino.config import Proxies

api = TwitterAPI(cfg.consumer_key, cfg.consumer_secret, cfg.access_token_key,
                 cfg.access_token_secret, proxy_url=Proxies['http'])
sv = Service('twitter-poller', use_priv=priv.SUPERUSER,
             manage_priv=priv.SUPERUSER, visible=False)

URL_TIMELINE = 'statuses/user_timeline'

subr_dic = {}
subr_dic['news'] = {
    # 'KanColle_STAFF', 'C2_STAFF',
    Service('kc-twitter', enable_on_default=False, help_='艦これ官推转发', bundle='kancolle'): ['ywwuyi'],
    Service('pcr-twitter', enable_on_default=True, help_='日服Twitter转发', bundle='pcr订阅'): ['priconne_redive', 'priconne_anime'],
    Service('azur-twitter', enable_on_default=True, help_='瓜游Twitter转发', bundle='azur订阅'): ['azurlane_staff', 'azurlane_bisoku'],
    # Service('pripri-twitter', enable_on_default=False, visible=False): ['pripri_anime'],
}
subr_dic['illust'] = {
    Service('coffee-favorite-twitter', manage_priv=priv.SUPERUSER,
            enable_on_default=False, visible=False): ['shiratamacaron', 'k_yuizaki', 'suzukitoto0323'],
    Service('lhx-favorite-twitter', manage_priv=priv.SUPERUSER,
            enable_on_default=False,
            visible=False): ['shiratamacaron', 'k_yuizaki', 'suzukitoto0323',
                             'tsukimi08', 'blade4649', 'itiri', 'MauveSR',
                             'hoshi_u3', 'gurasion0310', 'amsrntk3',
                             'nejikirio', 'siragagaga', 'kedamaa'],
}

latest_info = {}
# { account: {last_tweet_id: int, profile_image: str } }
latest_info['news'] = {}
for _, ids in subr_dic['news'].items():     # initialize
    for account in ids:
        latest_info['news'][account] = {'last_tweet_id': 0,
                                        'profile_image': '', 'media_only': False}

# { account: {last_tweet_id: int, profile_image: str } }
latest_info['illust'] = {}
for _, ids in subr_dic['illust'].items():     # initialize
    for account in ids:
        latest_info['illust'][account] = {'last_tweet_id': 0,
                                          'profile_image': '', 'media_only': True}


@wraps(api.request)
async def twt_request(*args, **kwargs):
    return await asyncio.get_event_loop().run_in_executor(
        None, partial(api.request, *args, **kwargs))


def update_latest_info(bundle: str, account: str, rsp: TwitterResponse):
    for item in rsp.get_iterator():
        if item['id'] > latest_info[bundle][account]['last_tweet_id']:
            latest_info[bundle][account]['last_tweet_id'] = item['id']
            if item['user']['screen_name'] == account:
                latest_info[bundle][account]['profile_image'] = item['user']['profile_image_url']


def time_formatter(time_str):
    dt = datetime.strptime(time_str, r"%a %b %d %H:%M:%S %z %Y")
    dt = dt.astimezone(pytz.timezone('Asia/Shanghai'))
    return f"{util.month_name(dt.month)}{util.date_name(dt.day)}・{util.time_name(dt.hour, dt.minute)}"


async def tweet_formatter(item):
    name = item['user']['name']
    time = time_formatter(item['created_at'])
    text = item['full_text']
    if 'media' in item['entities']:
        img = []
        is_extend = 'extended_' if 'extended_entities' in item else ''
        for i in item[f'{is_extend}entities']['media']:
            if i['type'] in 'photoanimated_gif':
                url = i['media_url']
                imgname = url.split('/')[-1]
                imgget = await R.tem_img('twitter', imgname).download(url, True)
                img.append(f"{imgget.cqcode}")
        img = '\n'.join(img)
    else:
        img = ''
    return f"@{name}\n{time}\n\n{text}{img}"


def has_media(item):
    try:
        return bool(item['entities']['media'][0]['media_url'])
    except Exception:
        return False


async def poll_new_tweets(bundle: str, account: str):
    if not latest_info[bundle][account]['last_tweet_id']:   # on the 1st time
        params = {'screen_name': account, 'count': '1'}
        rsp = await twt_request(URL_TIMELINE, params)
        update_latest_info(bundle, account, rsp)
        return []
    else:       # on other times
        params = {
            'screen_name': account,
            'count': '10',
            'since_id': latest_info[bundle][account]['last_tweet_id'],
            'tweet_mode': 'extended',
            'include_rts': False,
        }
        rsp = await twt_request(URL_TIMELINE, params)
        old_profile_image = latest_info[bundle][account]['profile_image']
        update_latest_info(bundle, account, rsp)
        new_profile_image = latest_info[bundle][account]['profile_image']

        items = rsp.get_iterator()
        if latest_info[bundle][account]['media_only']:
            items = filter(has_media, items)
        # tweets = list(map(tweet_formatter, items))
        tweets = [await tweet_formatter(i) for i in items]
        if new_profile_image != old_profile_image and old_profile_image:
            ptype = new_profile_image.split('.')[-1]
            big_img = await R.tem_img('twitter/avatar',
                                      f'{account}.{ptype}'
                                      ).download(new_profile_image, True)
            tweets.append(f"@{account} 更换了头像\n{big_img.cqcode}")
        return tweets


# Requests/15-min window: 900  == 1 req/s
_subr_num = len(latest_info['news'])
_freq = 20 * _subr_num
sv.logger.info(f"twitter_poller works at {_subr_num} / {_freq} seconds")


@sv.scheduled_job('interval', seconds=_freq)
async def twitter_poller_news():
    await twitter_poller('news')


@sv.scheduled_job('interval', hours=3)
async def twitter_poller_illust():
    await twitter_poller('illust')
    util.add_delay_job(twitter_poller, 'illustpoller', 300, ['illust'])


async def twitter_poller(bundle: str):
    buf = {}
    for account in latest_info[bundle]:
        try:
            buf[account] = await poll_new_tweets(bundle, account)
            if l := len(buf[account]):
                sv.logger.info(f"成功获取@{account}的新推文{l}条")
                try:
                    debuggroup = hoshino.config.DEBUGGROUP[0]
                    assert debuggroup
                    await hoshino.get_bot().send_group_msg(
                        group_id=debuggroup, message='发现twitter更新！')
                except Exception:
                    pass
            else:
                sv.logger.info(f"未检测到@{account}的新推文")
        except Exception as e:
            sv.logger.exception(e)
            sv.logger.error(f"获取@{account}的推文时出现异常{type(e)}")

    for ssv, subr_list in subr_dic[bundle].items():
        twts = []
        for account in subr_list:
            twts.extend(buf.get(account, []))
        if twts:
            await ssv.broadcast(twts, ssv.name, 0.5, retry=5)


@sv.on_prefix('看推', only_to_me=True)     # for test
async def one_tweet(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    try:
        account = args[0]
    except Exception:
        account = 'azurlane_staff'  # 'KanColle_STAFF'
    try:
        count = min(int(args[1]), 15)
        if count <= 0:
            count = 3
    except Exception:
        count = 3
    params = {
        'screen_name': account,
        'count': count,
        'tweet_mode': 'extended',
    }
    rsp = await twt_request(URL_TIMELINE, params)
    items = rsp.get_iterator()
    if account in latest_info['illust'] and latest_info['illust'][account]['media_only']:
        items = filter(has_media, items)
    #twts = list(map(tweet_formatter, items))
    twts = [await tweet_formatter(i) for i in items]
    for t in twts:
        try:
            await bot.send(ev, t)
        except Exception:
            await asyncio.sleep(0.01)
            await bot.send(ev, t)
        await asyncio.sleep(0.5)
