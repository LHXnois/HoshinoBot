from hoshino import Service, priv, R, util
from hoshino.typing import CQEvent, MessageSegment

sv = Service('_help_', manage_priv=priv.SUPERUSER, visible=False)

TOP_MANUAL = '''
===================
   - HoshinoBot -
- Kokkoro Edition -
    - 使用说明 -
===================
发送方括号[]内的关键词即可触发
※#前缀也可以用bot昵称或@bot代替
※功能采取模块化管理，群管理可控制开关

[!帮助] 会战管理v2<未开启>
[#怎么拆日和] 竞技场查询
[#十连] 转蛋模拟
[#pcr速查] 常用网址
[切噜一下] 切噜语转换
[lssv] 查看功能模块的开关状态（群管理限定）
[来杯咖啡] 骚扰蓝红心（bushi
[喵] 和bot用猫猫语交流

发送以下关键词查看更多：
[#帮助pcr会战]
[#帮助pcr查询]
[#帮助pcr娱乐]
[#帮助pcr订阅]
[#helpfun]
[#helpmaster]
[#help通用]
========
※除这里中写明外 另有其他隐藏功能:)
※隐藏功能属于赠品 不保证可用性
※本bot开源，可自行搭建
※服务器运行及开发维护需要成本，赞助支持请私戳作者
※您的支持是本bot更新维护的动力
※※调教时请注意使用频率，您的滥用可能会导致bot账号被封禁
'''.strip()

def gen_bundle_manual(bundle_name, service_list, gid):
    manual = [bundle_name]
    service_list = sorted(service_list, key=lambda s: s.name)
    for sv in service_list:
        if sv.visible:
            spit_line = '=' * max(0, 18 - len(sv.name))
            manual.append(f"|{'○' if sv.check_enabled(gid) else '×'}| {sv.name} {spit_line}")
            if sv.help:
                manual.append(sv.help)
    return '\n'.join(manual)


@sv.on_prefix(('help', '帮助'), only_to_me=True)
async def send_help(bot, ev: CQEvent):
    bundle_name = ev.message.extract_plain_text().strip()
    bundles = Service.get_bundles()
    if not bundle_name:
        msg = TOP_MANUAL
    elif bundle_name in bundles:
        msg = gen_bundle_manual(bundle_name, bundles[bundle_name], ev.group_id)
    elif bundle_name in 'bundle系列':
        msg = '\n'.join(bundles.keys())
    else:
        return
    msg = R.text2pic(msg)
    msg = MessageSegment.image(util.pic2b64(msg))
    await bot.send(ev, msg)
