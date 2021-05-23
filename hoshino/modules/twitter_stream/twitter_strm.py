import asyncio
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Iterable, Set

import hoshino
import peony
import pytz
from hoshino import Service, priv, util, R
from hoshino.service import sucmd
from hoshino.config import twitter as cfg
from hoshino.config import Proxies
from hoshino.typing import MessageSegment as ms
from peony import PeonyClient
from itertools import chain
try:
    import ujson as json
except Exception:
    import json


@dataclass
class FollowEntry:
    services: Set[Service] = field(default_factory=set)
    media_only: bool = False
    profile_image: str = None


class TweetRouter:
    def __init__(self):
        self.follows: Dict[str, FollowEntry] = {}
        self.needrestart = False

    def add(self, service: Service, follow_names: Iterable[str]):
        for f in follow_names:
            if f not in self.follows:
                self.follows[f] = FollowEntry()
            self.follows[f].services.add(service)

    def set_media_only(self, screen_name, media_only=True):
        self.follows[screen_name].media_only = media_only


sv = Service("twitter-poller", use_priv=priv.SUPERUSER,
             manage_priv=priv.SUPERUSER, visible=False)
sv_kc = Service("kc-twitter", help_="艦これ推特转发",
                enable_on_default=False, bundle="kancolle")
sv_pcr = Service("pcr-twitter", help_="日服Twitter转发",
                 enable_on_default=False, bundle="pcr订阅")
sv_blhx = Service('azur-twitter', enable_on_default=False,
                  help_='瓜游Twitter转发', bundle='azur订阅')
sv_uma = Service("uma-twitter", help_="ウマ娘推特转发",
                 enable_on_default=False, bundle="umamusume")
sv_pripri = Service("pripri-twitter", help_="番剧《公主代理人》官推转发",
                    enable_on_default=False)
sv_coffee_fav = Service("coffee-favorite-twitter",
                        help_="咖啡精选画师推特转发",
                        enable_on_default=False, bundle="artist")
sv_lhx_fav = Service("lhx-favorite-twitter", help_="蓝红心精选画师推特转发",
                     enable_on_default=False, bundle="artist")
sv_moe_artist = Service("moe-artist-twitter", help_="萌系画师推特转发",
                        enable_on_default=False, bundle="artist")
sv_depress_artist = Service(
    "depress-artist-twitter",
    help_="致郁系画师推特转发", enable_on_default=False, bundle="artist")
sv_test = Service("twitter-stream-test", enable_on_default=False,
                  manage_priv=priv.SUPERUSER, visible=False)

router = TweetRouter()
router.add(sv_kc, ["ywwuyi"])
router.add(sv_pcr, ["priconne_redive", "priconne_anime"])
router.add(sv_blhx, ['azurlane_staff', 'azurlane_bisoku'])
# router.add(sv_pripri, ["pripri_anime"])
router.add(sv_uma, ["uma_musu", "uma_musu_anime"])
router.add(sv_test, ["LHXnois"])

depress_artist = ["tkmiz"]
coffee_fav = ["shiratamacaron", "k_yuizaki",
              "suzukitoto0323", "usagicandy_taku"]
moe_artist = [
    "koma_momozu", "santamatsuri", "panno_mimi", "suimya", "Anmi_", "mamgon",
    "kazukiadumi", "Setmen_uU", "bakuPA", "kantoku_5th", "done_kanda",
    "siragagaga", "fuzichoco", "miyu_miyasaka", "naco_miyasaka", "tsukimi08",
    "tsubakininiwawa", "_Dan_ball", "ominaeshin", "gomalio_y", "izumiyuhina",
    "1kurusk", "amsrntk3", "kani_biimu", "Nakkar7", "li_hongbo", "nahaki_401",
    "ukiukisoda", "yukkieeeeeen", "riko0202", "hoshi_u3",
]
lhx_fav = R.data('twitter/lhx_fav.json', 'json')
if not lhx_fav.exist:
    lhx_fav.write([])
lhx_fav = list(set(lhx_fav.read).difference(
    set(moe_artist+coffee_fav+depress_artist)))


router.add(sv_coffee_fav, coffee_fav)
router.add(sv_moe_artist, moe_artist)
router.add(sv_depress_artist, depress_artist)
router.add(sv_lhx_fav, lhx_fav)
for i in chain(coffee_fav, moe_artist, depress_artist, lhx_fav):
    router.set_media_only(i)


class UserIdCache:
    _cache_file = os.path.expanduser('~/.hoshino/twitter_uid_cache.json')

    def __init__(self) -> None:
        self.cache = {}
        if os.path.isfile(self._cache_file):
            try:
                with open(self._cache_file, 'r', encoding='utf8') as f:
                    self.cache = json.load(f)
            except Exception as e:
                sv.logger.exception(e)
                sv.logger.error(
                    (f"{type(e)} occured when loading"
                     " `twitter_uid_cache.json`, using empty cache."))

    async def convert(self,
                      client: PeonyClient,
                      screen_names: Iterable[str],
                      cached=True):
        if not cached:
            self.cache = {}
        error_name = []
        for i in screen_names:
            if i not in self.cache:
                try:
                    user = await client.api.users.show.get(screen_name=i)
                except Exception as e:
                    error_name.append(i)
                    await hoshino.get_bot().send_private_msg(
                        user_id=hoshino.config.SUPERUSERS[0],
                        message=f'推特添加订阅{i}时出现问题{e}')
                else:
                    self.cache[i] = user.id
        follow_ids = [self.cache[i]
                      for i in screen_names if i not in error_name]
        with open(self._cache_file, 'w', encoding='utf8') as f:
            json.dump(self.cache, f)
        return follow_ids


def format_time(time_str):
    dt = datetime.strptime(time_str, r"%a %b %d %H:%M:%S %z %Y")
    dt = dt.astimezone(pytz.timezone("Asia/Shanghai"))
    return (f"{util.month_name(dt.month)}"
            f"{util.date_name(dt.day)}・"
            f"{util.time_name(dt.hour, dt.minute)}")


def format_tweet(tweet):
    name = tweet.user.name
    screen_name = tweet.user.screen_name
    time = format_time(tweet.created_at)
    text = tweet.text
    media = tweet.get('extended_entities', {}).get('media', [])
    imgs = ' '.join([str(ms.image(m.media_url)) for m in media])
    msg = f"@{name} (@{screen_name}) \n{time}\n\n{text}"
    if imgs:
        msg = f"{msg}\n{imgs}"
    return msg


bot = hoshino.get_bot()


@bot.on_startup
async def start_daemon():
    loop = asyncio.get_event_loop()
    loop.create_task(twitter_stream_daemon())


async def twitter_stream_daemon():
    client = PeonyClient(consumer_key=cfg.consumer_key,
                         consumer_secret=cfg.consumer_secret,
                         access_token=cfg.access_token_key,
                         access_token_secret=cfg.access_token_secret,
                         proxy=Proxies['http'])
    async with client:
        while True:
            try:
                await open_stream(client)
            except KeyboardInterrupt:
                return
            except Exception as e:
                sv.logger.exception(e)
                sv.logger.error(
                    (f"Error {type(e)} Occurred in twitter stream. "
                     "Restarting stream in 5s."))
                await asyncio.sleep(5)


user_id_cache = UserIdCache()


async def open_stream(client: PeonyClient):
    # follow_ids = [(await client.api.users.show.get(
    #                   screen_name=i)).id for i in router.follows]
    follow_ids = await user_id_cache.convert(client, router.follows)
    sv.logger.info(f"订阅推主={router.follows.keys()}, {follow_ids=}")
    stream = client.stream.statuses.filter.post(follow=follow_ids)
    async with stream:
        async for tweet in stream:

            # sv.logger.info("Got twitter event.")
            if peony.events.tweet(tweet):
                screen_name = tweet.user.screen_name
                if screen_name not in router.follows:
                    continue    # 推主不在订阅列表
                if peony.events.retweet(tweet):
                    continue    # 忽略纯转推
                reply_to = tweet.get('in_reply_to_screen_name')
                if reply_to and reply_to != screen_name:
                    continue    # 忽略对他人的评论，保留自评论

                entry = router.follows[screen_name]
                media = tweet.get('extended_entities', {}).get('media', [])
                if entry.media_only and not media:
                    continue    # 无附带媒体，订阅选项media_only=True时忽略

                msg = format_tweet(tweet)

                if 'quoted_status' in tweet:
                    quoted_msg = format_tweet(tweet.quoted_status)
                    msg = f"{msg}\n\n>>>>>\n{quoted_msg}"

                old_profile_img = entry.profile_image
                entry.profile_image = tweet.user.get(
                    "profile_image_url_https") or entry.profile_image
                if old_profile_img and entry.profile_image != old_profile_img:
                    big_img = re.sub(
                        r'_normal(\.(jpg|jpeg|png|gif|jfif|webp))$',
                        r'\1',
                        entry.profile_image,
                        re.I)
                    msg = [msg, f"@{screen_name} 更换了头像\n{ms.image(big_img)}"]

                sv.logger.info(f"推送推文：\n{msg}")
                for s in entry.services:
                    await s.broadcast(msg, f' @{screen_name} 推文', 0.3)

            else:
                sv.logger.debug("Ignore non-tweet event.")
            if router.needrestart:
                router.needrestart = False
                return


@sv.on_prefix('推特订阅', only_to_me=True)
async def addfollow(bot, ev):
    kw = ev.message.extract_plain_text().strip()
    if not kw:
        return
    if kw in router.follows:
        sve = (i.name for i in router.follows[kw].services)
        await bot.finish(ev, f'订阅已存在于{list(sve)}')
    router.add(sv_lhx_fav, [kw])
    router.set_media_only(kw)
    lhx_fav.append(kw)
    lhx_fav.sort()
    R.data('twitter/lhx_fav.json', 'json').write(lhx_fav)
    await bot.send(ev, '订阅成功')
    router.needrestart = True


@sv.on_prefix('取消推特订阅', only_to_me=True)
async def disaddfollow(bot, ev):
    kw = ev.message.extract_plain_text().strip()
    if not kw:
        return
    if kw not in lhx_fav:
        await bot.finish(ev, '不存在或不能取消的订阅')
    router.follows.pop(kw)
    lhx_fav.remove(kw)
    R.data('twitter/lhx_fav.json', 'json').write(lhx_fav)
    databin = R.data('twitter/lhx_fav_bin.json', 'json')
    if not databin.exist:
        databin.write([kw])
    else:
        databin.write(databin.read+[kw])
    await bot.send(ev, '取消成功')
    router.needrestart = True
