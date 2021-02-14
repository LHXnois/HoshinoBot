import hoshino
from hoshino import R
from hoshino.typing import CQEvent
import random


class Groupmaster:
    managegroups = {'owner': set(), 'admin': set(), 'administrator': set()}

    def __init__(self, ev: CQEvent = None, self_id: int = 0, group_id: int = 0):
        self.bot = hoshino.get_bot()
        if not ev:
            self.sid = self_id
            self.gid = group_id
        else:
            self.sid = ev.self_id
            self.gid = ev.group_id
        for i in Groupmaster.managegroups:
            if self.gid in Groupmaster.managegroups[i]:
                self.role = i
                break
        else:
            await self.roleupdate()

    # 群员信息
    async def member_info(self, user_id: int) -> dict:
        '''info内容
            group_id	int64	群号
            user_id	int64	QQ 号
            nickname	string	昵称
            card	string	群名片／备注
            sex	string	性别, male 或 female 或 unknown
            age	int32	年龄
            area	string	地区
            join_time	int32	加群时间戳
            last_sent_time	int32	最后发言时间戳
            level	string	成员等级
            role	string	角色, owner 或 admin 或 member
            unfriendly	boolean	是否不良记录成员
            title	string	专属头衔
            title_expire_time	int64	专属头衔过期时间戳
            card_changeable	boolean	是否允许修改群名片
        '''
        try:
            info = await self.bot.get_group_member_info(
                group_id=self.gid,
                user_id=user_id,
                no_cache=True
            )
            return info
        except Exception as e:
            hoshino.logger.exception(e)
            return {}

    # 群成员列表
    async def member_list(self, only_uid: bool = True) -> list:
        try:
            mlist = await self.bot.get_group_member_list(
                group_id=self.gid,
                self_id=self.sid
            )
            if only_uid:
                mlist = [i['user_id'] for i in mlist]
            return mlist
        except Exception as e:
            hoshino.logger.exception(e)
            return []

    # 群荣誉信息
    async def honor_info(self, honor_type: str) -> dict:
        '''响应数据
            group_id	int64	群号
            current_talkative	object	当前龙王, 仅 type 为 talkative 或 all 时有数据
            talkative_list	array	历史龙王, 仅 type 为 talkative 或 all 时有数据
            performer_list	array	群聊之火, 仅 type 为 performer 或 all 时有数据
            legend_list	array	群聊炽焰, 仅 type 为 legend 或 all 时有数据
            strong_newbie_list	array	冒尖小春笋, 仅 type 为 strong_newbie 或 all 时有数据
            emotion_list	array	快乐之源, 仅 type 为 emotion 或 all 时有数据

            其中 current_talkative 字段的内容如下：
            user_id	int64	QQ 号
            nickname	string	昵称
            avatar	string	头像 URL
            day_count	int32	持续天数

            其它各 *_list 的每个元素是一个 json 对象, 内容如下：
            user_id	int64	QQ 号
            nickname	string	昵称
            avatar	string	头像 URL
            description	string	荣誉描述
        '''
        try:
            gh_info = await self.bot.get_group_honor_info(
                group_id=self.gid,
                type=honor_type
            )
            return gh_info
        except Exception as e:
            hoshino.logger.exception(e)
            return {}

    # 获取vip信息
    async def vip_info(self, user_id: int) -> dict:
        '''info 内容
            user_id	int64	QQ 号
            nickname	string	用户昵称
            level	int64	QQ 等级
            level_speed	float64	等级加速度
            vip_level	string	会员等级
            vip_growth_speed	int64	会员成长速度
            vip_growth_total	int64	会员成长总值
        '''
        try:
            info = await self.bot._get_vip_info(
                user_id=user_id
            )
            return info
        except Exception as e:
            hoshino.logger.exception(e)
            return {}

    def rolecheck(self, roleneed: str):
        if self.role == 'owner':
            return True
        elif self.role == 'member':
            return False
        else:
            return roleneed == 'member'

    async def roleupdate(self):
        for i in Groupmaster.managegroups:
            Groupmaster.managegroups[i].discard(self.gid)
        self.role = await self.member_info(self.sid)['role']
        if self.role in 'owneradministrator':
            Groupmaster.managegroups[self.role].add(self.gid)

    # 随机成员
    async def random_member(self) -> int:
        ml = await self.member_list()
        return random.choice(ml)

    # 头衔
    async def title_get(self, user_id: int) -> str:
        return await self.member_info(user_id)['title']

    # 头像
    async def avatar(self, user_id: int, s: int = 100) -> R.TemImg:
        apiPath = f'http://q1.qlogo.cn/g?b=qq&nk={user_id}&s={s}'
        avatartem = await R.tem_gocqimg(apiPath)
        if not avatartem.exist:
            avatartem = R.tem_img(f'groupmaster/avatar/{user_id}_{s}.png')
            if not avatartem.exist:
                await avatartem.download(apiPath)
        return avatartem

    # 管理设置
    async def admin_set(self, user_id: int, status: bool = True):
        if self.rolecheck('owner'):
            try:
                await self.bot.set_group_admin(
                    group_id=self.gid,
                    user_id=user_id,
                    enable=status
                )
            except Exception as e:
                hoshino.logger.exception(e)
                await self.roleupdate()

    # 头衔申请
    async def title_set(self, user_id, title):
        if not self.rolecheck('owner'):
            try:
                await self.bot.set_group_special_title(
                    group_id=self.gid,
                    user_id=user_id,
                    special_title=title,
                )
            except Exception as e:
                hoshino.logger.exception(e)
                await self.roleupdate()

    # 群组踢人
    async def member_kick(self, user_id: int, is_reject: bool = False):
        if self.rolecheck(await self.member_info(user_id)['role']):
            try:
                await self.bot.set_group_kick(
                    group_id=self.gid,
                    user_id=user_id,
                    reject_add_request=is_reject
                )
            except Exception as e:
                hoshino.logger.exception(e)
                await self.roleupdate()

    # 单人禁言
    async def member_silence(self, time: int, user_id: int = None, anonymous_flag: str = None):
        if self.rolecheck(
                await self.member_info(user_id)['role'] if user_id else 'member'):
            try:
                if anonymous_flag:
                    await self.bot.set_group_anonymous_ban(
                        group_id=self.gid,
                        anonymous_flag=anonymous_flag,
                        duration=time,
                        self_id=self.sid
                    )
                else:
                    await self.bot.set_group_ban(
                        group_id=self.gid,
                        user_id=user_id,
                        duration=time,
                        self_id=self.sid
                    )
            except Exception as e:
                hoshino.logger.exception(e)
                await self.roleupdate()

    # 全员禁言
    async def gruop_silence(self, status: bool = True):
        if self.rolecheck('member'):
            try:
                await self.bot.set_group_whole_ban(
                    group_id=self.gid,
                    enable=status
                )
            except Exception as e:
                hoshino.logger.exception(e)
                await self.roleupdate()

    # 群名片修改
    async def card_edit(self, user_id: int, card_text: str = ''):
        if self.rolecheck('member'):
            try:
                await self.bot.set_group_card(
                    group_id=self.gid,
                    user_id=user_id,
                    card=card_text
                )
            except Exception as e:
                hoshino.logger.exception(e)
                await self.roleupdate()

    # 群名修改
    async def group_name(self, name: str):
        if self.rolecheck('member'):
            try:
                await self.bot.set_group_name(
                    group_id=self.gid,
                    group_name=name
                )
            except Exception as e:
                hoshino.logger.exception(e)
                await self.roleupdate()

    # 设置精华消息
    async def set_essence(self, msg_id: int):
        if self.rolecheck('member'):
            try:
                await self.bot.set_essence_msg(
                    message_id=msg_id
                )
            except Exception as e:
                hoshino.logger.exception(e)
                await self.roleupdate()

    # 发公告
    async def group_notice(self, content: str):
        if self.rolecheck('member'):
            try:
                await self.bot._send_group_notice(
                    group_id=self.gid,
                    content=content
                )
            except Exception as e:
                hoshino.logger.exception(e)
                await self.roleupdate()
