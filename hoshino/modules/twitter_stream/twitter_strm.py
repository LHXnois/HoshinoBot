import asyncio
import importlib
import os
from posixpath import split
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Iterable, Set
from itertools import chain
import pytz
import hoshino
from hoshino import Service, priv, util, R, sucmd
from hoshino.service import sucmd
from hoshino.config import twitter as cfg, Proxies
from hoshino.typing import MessageSegment as ms, CommandSession
from hoshino.typing import CommandSession, CQEvent

import peony
from peony import PeonyClient

try:
    import ujson as json
except Exception:
    import json


sv = Service("twitter-poller", use_priv=priv.SUPERUSER, manage_priv=priv.SUPERUSER, visible=False)
sv_lhx_fav = Service("lhx-favorite-twitter", help_="蓝红心精选画师推特转发", enable_on_default=False, bundle="artist")
bot = hoshino.get_bot()
daemon = None
follow_collection = [
    Service("twitter-stream-test", enable_on_default=False, manage_priv=priv.SUPERUSER, visible=False),
    Service("kc-twitter", help_="艦これ推特转发", enable_on_default=False, bundle="kancolle"),
    Service("pcr-twitter", help_="日服Twitter转发", enable_on_default=False, bundle="pcr订阅"),
    Service("uma-twitter", help_="ウマ娘推特转发", enable_on_default=False, bundle="umamusume"),
    Service("pripri-twitter", help_="番剧《公主代理人》官推转发", enable_on_default=False),
    Service("coffee-favorite-twitter", help_="咖啡精选画师推特转发", enable_on_default=False, bundle="artist"),
    Service("moe-artist-twitter", help_="萌系画师推特转发", enable_on_default=False, bundle="artist"),
    Service("depress-artist-twitter", help_="致郁系画师推特转发", enable_on_default=False, bundle="artist"),
    sv_lhx_fav,
    Service('azur-twitter', help_='瓜游Twitter转发', enable_on_default=False, bundle='azur订阅'),
]


@dataclass
class FollowEntry:
    services: Set[Service] = field(default_factory=set)
    media_only: bool = False
    profile_image: str = None


class TweetRouter:
    def __init__(self):
        self.follows: Dict[str, FollowEntry] = defaultdict(FollowEntry)
        self.needrestart = False

    def add(self, service: Service, follow_names: Iterable[str]):
        for f in follow_names:
            self.follows[f].services.add(service)

    def set_media_only(self, screen_name, media_only=True):
        if screen_name not in self.follows:
            raise KeyError(f"`{screen_name}` not in `TweetRouter.follows`.")
        self.follows[screen_name].media_only = media_only

    def load(self, service_follow_dict, media_only_users):
        for s in follow_collection:
            self.add(s, service_follow_dict[s.name])
        for x in media_only_users:
            self.set_media_only(x)


class UserIdCache:
    _cache_file = os.path.expanduser("~/.hoshino/twitter_uid_cache.json")

    def __init__(self) -> None:
        self.cache = {}
        if os.path.isfile(self._cache_file):
            try:
                with open(self._cache_file, "r", encoding="utf8") as f:
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
                    await util.botdebuginfo(f'推特添加订阅{i}时出现问题{e}')
                else:
                    self.cache[i] = user.id
        follow_ids = [self.cache[i]
                      for i in screen_names if i not in error_name]
        with open(self._cache_file, 'w', encoding='utf8') as f:
            json.dump(self.cache, f)
        return follow_ids


@dataclass
class Twittermaster:
    client: PeonyClient = None
    router: TweetRouter = None
    user_id_cache: UserIdCache = None


Tm = Twittermaster()


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


@bot.on_startup
async def start_daemon():
    global daemon
    loop = asyncio.get_event_loop()
    daemon = loop.create_task(twitter_stream_daemon())


async def twitter_stream_daemon():
    Tm.client = PeonyClient(consumer_key=cfg.consumer_key,
                            consumer_secret=cfg.consumer_secret,
                            access_token=cfg.access_token_key,
                            access_token_secret=cfg.access_token_secret,
                            proxy=Proxies['http'])
    async with Tm.client:
        while True:
            try:
                await open_stream(Tm.client)
            except (KeyboardInterrupt, asyncio.CancelledError):
                sv.logger.info("Twitter stream daemon exited.")
                return
            except Exception as e:
                sv.logger.exception(e)
                sv.logger.error(
                    (f"Error {type(e)} Occurred in twitter stream. "
                     "Restarting stream in 5s."))
                await asyncio.sleep(5)


async def open_stream(client: PeonyClient):
    Tm.router = TweetRouter()
    router = Tm.router
    router.load(cfg.follows, cfg.media_only_users())
    Tm.user_id_cache = UserIdCache()
    follow_ids = await Tm.user_id_cache.convert(client, router.follows)
    sv.logger.info(f"订阅推主={router.follows.keys()}, {follow_ids=}")
    try:
        await util.botdebuginfo(f'twitter_stream已启动！关注数{len(follow_ids)}')
    except Exception:
        pass
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
                reply_to = tweet.get("in_reply_to_screen_name")
                if reply_to and reply_to != screen_name:
                    continue    # 忽略对他人的评论，保留自评论

                entry = router.follows[screen_name]
                media = tweet.get("extended_entities", {}).get("media", [])
                if entry.media_only and not media:
                    continue    # 无附带媒体，订阅选项media_only=True时忽略

                msg = format_tweet(tweet)
                if '桐生ココ' in msg:
                    continue
                if "quoted_status" in tweet:
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
                    await s.broadcast(msg, f" @{screen_name} 推文", 0.2)

            else:
                #sv.logger.debug("Ignore non-tweet event.")
                pass
            if router.needrestart:
                router.needrestart = False
                return


@sv.on_prefix('推特订阅', only_to_me=True)
async def addfollow(bot, ev: CQEvent):
    kw = ev.message.extract_plain_text().strip().split()
    count = 0
    router = Tm.router
    for i in kw:
        if i in router.follows:
            sve = (si.name for si in router.follows[i].services)
            await bot.send(ev, f'{i}已存在订阅于{list(sve)}')
            continue
        try:
            await Tm.client.api.users.show.get(screen_name=i)
        except Exception as e:
            await util.botdebuginfo(f'推特添加订阅{i}时出现问题{e}')
            continue
        router.add(sv_lhx_fav, [i])
        router.set_media_only(i)
        cfg.follows["lhx-favorite-twitter"].append(i)
        count += 1
    if count:
        cfg.follows["lhx-favorite-twitter"].sort()
        cfg.lhx_fav.write(cfg.follows["lhx-favorite-twitter"])
        await bot.send(ev, '订阅成功')
        router.needrestart = True


@sv.on_prefix('取消推特订阅', only_to_me=True)
async def disaddfollow(bot, ev: CQEvent):
    kw = ev.message.extract_plain_text().strip()
    if not kw:
        return
    if kw not in cfg.follows["lhx-favorite-twitter"]:
        await bot.finish(ev, '不存在或不能取消的订阅')
    router = Tm.router
    router.follows.pop(kw)
    cfg.follows["lhx-favorite-twitter"].remove(kw)
    cfg.lhx_fav.write(cfg.follows["lhx-favorite-twitter"])
    databin = R.data('twitter/lhx_fav_bin.json', 'json')
    if not databin.exist:
        databin.write([kw])
    else:
        databin.write(databin.read+[kw])
    await bot.send(ev, '取消成功')
    router.needrestart = True


@sucmd('重载推特订阅', force_private=False)
async def reloadfollow(session: CommandSession):
    lhx_fav_data = R.data('twitter/lhx_fav.json', 'json')

    if not lhx_fav_data.exist:
        await session.finish('找不到lhx_fav.json')
    router = Tm.router
    lhx_fav_new = list(set(cfg.lhx_fav.read).difference(
        set(cfg.follows["moe-artist-twitter"] +
            cfg.follows["coffee-favorite-twitter"] +
            cfg.follows["depress-artist-twitter"])
    ))
    nofollow = list(set(cfg.follows["lhx-favorite-twitter"]).difference(set(lhx_fav_new)))
    if nofollow:
        list(map(router.follows.pop, nofollow))
    cfg.follows["lhx-favorite-twitter"] = lhx_fav_new
    router.add(sv_lhx_fav, cfg.follows["lhx-favorite-twitter"])
    list(map(router.set_media_only, cfg.follows["lhx-favorite-twitter"]))
    router.needrestart = True
    await session.send('已重载')


@sucmd("reload-twitter-stream-daemon", force_private=False, aliases=("重启转推", "重载转推"))
async def reload_twitter_stream_daemon(session: CommandSession):
    try:
        daemon.cancel()
        importlib.reload(cfg)
        await start_daemon()
        await session.send('ok')
    except Exception as e:
        sv.logger.exception(e)
        await session.send(f'Error: {type(e)}')
