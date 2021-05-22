from typing import Union
from hoshino import C
from .chara import fromid


class pcrCoins(C.Coinsmaster):
    Clist = {
        '宝石': 'jewel',
        '女神的秘石': 'hiishi',
        '秘石': 'hiishi',
        '母猪石': 'hiishi',
        '卢比': 'lubi',
        '卢币': 'lubi',
        'mana': 'mana',
        '玛娜': 'mana',
        '公主之心': 'heart',
        '公主之心碎片': 'heartchip',
        '心碎': 'heartchip',
        '扫荡券': 'rushcoupon'
    }

    def __init__(self, uid: int, coinname: str):
        super().__init__(uid, coinname=coinname, bundle='pcr')


class pcrCharas(C.Charasmaster):
    def __init__(self, uid: int, cid: int = 1000):
        class pcrC(C.Charas):
            cname = C.IntegerField()
            clv = C.IntegerField(default=1)
            rank = C.IntegerField(default=0)
            uwlv = C.IntegerField(default=0)
            loverank = C.IntegerField(default=0)
            chip = C.IntegerField(default=0)
        super().__init__(uid, cid, 'pcr', type=pcrC)

    def set_star(self, star):
        self.set_Cvalue('star', star)

    @property
    def chrar(self):
        return fromid(self.cname, self.c.star)

    def add_C(self, star=1) -> int:
        self.set_star(star)
        return super().add_C(1)

    def add_chips(self, chip=100):
        chip = self.c.chip + chip
        self.set_Cvalue('chip', chip)
