import hoshino
from hoshino import R
from hoshino.typing import CQEvent
import random


class Groupmaster:
    managegroups = {'default': {'role': 'member', 'needroleupdate': True}}
    PRIV_NOT_ENOUGH = 1000

    def __init__(self, ev: CQEvent = None, self_id: int = 0, group_id: int = 0):
        self.bot = hoshino.get_bot()
        if not ev:
            self.sid = self_id
            self.gid = group_id
        else:
            self.sid = ev.self_id
            self.gid = ev.group_id
        mg = Groupmaster.managegroups
        if self.gid in mg:
            self.role = mg[self.gid]['role']
        else:
            mg[self.gid] = mg['default']
        self.privs = mg[self.gid]

    # 群员信息
    async def member_info(self, user_id: int, key: str = None):
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
            if key:
                return info[key]
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
    async def honor_info(self, honor_type: str, key: str = None) -> dict:
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
            if key:
                return gh_info[key]
            return gh_info
        except Exception as e:
            hoshino.logger.exception(e)
            return {}

    # 获取vip信息
    async def vip_info(self, user_id: int, key: str = None) -> dict:
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
            if key:
                return info[key]
            return info
        except Exception as e:
            hoshino.logger.exception(e)
            return {}

    async def rolecheck(self, roleneed: str):
        await self.roleupdate()
        if self.role == 'owner':
            return True
        elif self.role == 'member':
            return False
        else:
            return roleneed == 'member'

    async def roleupdate(self):
        if self.privs['needroleupdate']:
            self.role = await self.member_info(self.sid, 'role')
            self.privs['role'] = self.role
            self.privs['needroleupdate'] = False

    # 随机成员
    async def random_member(self) -> int:
        ml = await self.member_list()
        return random.choice(ml)

    # 管理设置
    async def admin_set(self, user_id: int, status: bool = True):
        if await self.rolecheck('owner'):
            try:
                await self.bot.set_group_admin(
                    group_id=self.gid,
                    user_id=user_id,
                    enable=status
                )
            except Exception as e:
                hoshino.logger.exception(e)
                self.privs['needroleupdate'] = False
        else:
            self.privs['needroleupdate'] = False
            return Groupmaster.PRIV_NOT_ENOUGH

    # 头衔申请
    async def title_set(self, user_id, title):
        if await self.rolecheck('owner'):
            try:
                await self.bot.set_group_special_title(
                    group_id=self.gid,
                    user_id=user_id,
                    special_title=title,
                )
            except Exception as e:
                hoshino.logger.exception(e)
                self.privs['needroleupdate'] = False
        else:
            self.privs['needroleupdate'] = False
            return Groupmaster.PRIV_NOT_ENOUGH

    # 群组踢人
    async def member_kick(self, user_id: int, is_reject: bool = False):
        if await self.rolecheck(await self.member_info(user_id, 'role')):
            try:
                await self.bot.set_group_kick(
                    group_id=self.gid,
                    user_id=user_id,
                    reject_add_request=is_reject
                )
            except Exception as e:
                hoshino.logger.exception(e)
                self.privs['needroleupdate'] = False
        else:
            self.privs['needroleupdate'] = False
            return Groupmaster.PRIV_NOT_ENOUGH

    # 单人禁言
    async def member_silence(self, time: int, user_id: int = None, anonymous_flag: str = None):
        if await self.rolecheck(
                await self.member_info(user_id, 'role') if user_id else 'member'):
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
                self.privs['needroleupdate'] = False
        else:
            self.privs['needroleupdate'] = False
            return Groupmaster.PRIV_NOT_ENOUGH

    # 全员禁言
    async def group_silence(self, status: bool = True):
        if await self.rolecheck('member'):
            try:
                await self.bot.set_group_whole_ban(
                    group_id=self.gid,
                    enable=status
                )
            except Exception as e:
                hoshino.logger.exception(e)
                self.privs['needroleupdate'] = False
        else:
            self.privs['needroleupdate'] = False
            return Groupmaster.PRIV_NOT_ENOUGH

    # 群名片修改
    async def card_set(self, user_id: int, card_text: str = ''):
        if await self.rolecheck('member'):
            try:
                await self.bot.set_group_card(
                    group_id=self.gid,
                    user_id=user_id,
                    card=card_text
                )
            except Exception as e:
                hoshino.logger.exception(e)
                self.privs['needroleupdate'] = False
        else:
            return Groupmaster.PRIV_NOT_ENOUGH

    # 群名修改
    async def groupname_set(self, name: str):
        if await self.rolecheck('member'):
            try:
                await self.bot.set_group_name(
                    group_id=self.gid,
                    group_name=name
                )
            except Exception as e:
                hoshino.logger.exception(e)
                self.privs['needroleupdate'] = False
        else:
            self.privs['needroleupdate'] = False
            return Groupmaster.PRIV_NOT_ENOUGH

    # 设置精华消息
    async def essence_set(self, msg_id: int):
        if await self.rolecheck('member'):
            try:
                await self.bot.set_essence_msg(
                    message_id=msg_id
                )
            except Exception as e:
                hoshino.logger.exception(e)
                self.privs['needroleupdate'] = False
        else:
            self.privs['needroleupdate'] = False
            return Groupmaster.PRIV_NOT_ENOUGH

    # 发公告
    async def group_notice(self, content: str):
        if await self.rolecheck('member'):
            try:
                await self.bot._send_group_notice(
                    group_id=self.gid,
                    content=content
                )
            except Exception as e:
                hoshino.logger.exception(e)
                self.privs['needroleupdate'] = False
        else:
            self.privs['needroleupdate'] = False
            return Groupmaster.PRIV_NOT_ENOUGH
