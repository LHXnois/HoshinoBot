from hoshino import Service, priv
from hoshino.typing import NoticeSession

import psutil


sv = Service('status', help_='服务器状态', bundle='master', use_priv=priv.SUPERUSER)


@sv.on_notice('notify.poke')
async def pokepoke(session: NoticeSession):
    if session.event.target_id != session.event.self_id:
        return
    data = []
    data.append("CPU:")
    for index, per_cpu in enumerate(
            psutil.cpu_percent(interval=1, percpu=True)):
        data.append(f"  core{index + 1}: {int(per_cpu):02d}%")
    data.append(
        f"Memory: {int(psutil.virtual_memory().percent):02d}%")
    data.append("Disk:")
    for d in psutil.disk_partitions():
        data.append(
            f"  {d.mountpoint}: "
            f"{int(psutil.disk_usage(d.mountpoint).percent):02d}%")
        break
    await session.send('\n'.join(data))
