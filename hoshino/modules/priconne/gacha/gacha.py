import random

from hoshino import util
from .. import chara
from ..pcrColleciton import pcrCharas, pcrCoins

startohiishi = {1: 1, 2: 10, 3: 50}
cardinfo = {
    1: {
        'rank': 'p1',
        'name': '一等',
        'chip': 40,
        'hiishi': 5,
        'heartchip': 5,
        'rushcoupon': 50,
    },
    2: {
        'rank': 'p2',
        'name': '二等',
        'chip': 20,
        'hiishi': 5,
        'heartchip': 3,
        'rushcoupon': 30,
    },
    3: {
        'rank': 'p3',
        'name': '三等',
        'chip': 5,
        'hiishi': 1,
        'heartchip': 3,
        'rushcoupon': 30,
    },
    4: {
        'rank': 'p4',
        'name': '四等',
        'chip': 1,
        'hiishi': 1,
        'heartchip': 2,
        'rushcoupon': 20,
    },
    5: {
        'rank': 'p5',
        'name': '五等',
        'chip': 0,
        'hiishi': 1,
        'heartchip': 1,
        'rushcoupon': 20,
    },
    6: {
        'rank': 'p6',
        'name': '六等',
        'chip': 0,
        'hiishi': 1,
        'heartchip': 0,
        'rushcoupon': 20,
    },
}

class Gacha(object):

    def __init__(self, uid, pool_name: str = "MIX"):
        super().__init__()
        self.load_pool(pool_name)
        self.uid = uid
        self.result = {
            'fes': self.fes,
            'chara': [],
            'up': 0,
            's3': 0,
            's2': 0,
            's1': 0,
            'new': [],
            'prize': self.prize,
            'p1': 0,
            'p2': 0,
            'p3': 0,
            'p4': 0,
            'p5': 0,
            'p6': 0,
            'card': [],
            'hiishi': 0,
            'chips': 0,
            'heartchip': 0,
            'rushcoupon': 0,
        }

    def load_pool(self, pool_name: str):
        config = util.load_config(__file__)
        pool = config[pool_name]
        self.fes = pool['fes']
        self.prize = pool['prize']
        self.up_prob = pool["up_prob"]*(1+int(self.fes))
        self.s3_prob = pool["s3_prob"]*(1+int(self.fes))
        self.s2_prob = pool["s2_prob"]
        self.s1_prob = 1000 - self.s2_prob - self.s3_prob
        self.up = pool["up"]
        self.star3 = self.del_up(pool["star3"])+self.del_up(pool["star3_f"])*2
        self.star2 = pool["star2"]
        self.star1 = pool["star1"] + pool['star1_f'] + pool['star1_up']*2

    def del_up(self, clist):
        return list(set(clist).difference(set(self.up)))

    def gacha_one(self, up_prob: int,
                  s3_prob: int, s2_prob: int,
                  s1_prob: int = None, only_s3=False, recordcard=False):
        '''
        sx_prob: x星概率，要求和为1000
        up_prob: UP角色概率（从3星划出）
        up_chara: UP角色名列表

        return: (单抽结果:Chara, 秘石数:int)
        ---------------------------
        |up|      |  20  |   78   |
        |   ***   |  **  |    *   |
        ---------------------------
        '''
        if s1_prob is None:
            s1_prob = 1000 - s3_prob - s2_prob
        total_ = s3_prob + s2_prob + s1_prob
        pick = random.randint(1, total_)
        if pick <= up_prob:
            getc = chara.fromname(random.choice(self.up), 3)
            self.result['up'] += 1
            self.result['chips'] += 100
            pcrCharas(self.uid, getc.id).add_chips()
        elif pick <= s3_prob:
            getc = chara.fromname(random.choice(self.star3), 3)
        elif pick <= s2_prob + s3_prob:
            getc = chara.fromname(random.choice(self.star2), 2)
        else:
            getc = chara.fromname(random.choice(self.star1), 1)
        self.result[f's{getc.star}'] += 1
        pC = pcrCharas(self.uid, getc.id)
        if not pC.check_Cexist:
            pC.add_C(getc.star)
            getc.new = True
            self.result['new'].append(getc.name)
        else:
            self.result['hiishi'] += startohiishi[getc.star]
        if not only_s3 or getc.star == 3:
            self.result['chara'].append(getc)
        if self.prize:
            card = self.prize_card()
            if recordcard:
                self.result['card'].append(card['name'])
            self.result[card['rank']] += 1
            self.result['chips'] += card['chip']
            if card['chip'] > 0:
                for i in self.up:
                    pcrCharas(self.uid, chara.name2id(i)).add_chips(card['chip'])
            self.result['hiishi'] += card['hiishi']
            self.result['heartchip'] += card['heartchip']
            self.result['rushcoupon'] += card['rushcoupon']
        return self.result

    def prize_card(self):
        pick = random.randint(0, 999)
        if pick < 5:
            card = 1
        elif pick < 10:
            card = 2
        elif pick < 50:
            card = 3
        elif pick < 100:
            card = 4
        elif pick < 235:
            card = 5
        else:
            card = 6
        return cardinfo[card]



    def gacha_ten(self):
        up = self.up_prob
        s3 = self.s3_prob
        s2 = self.s2_prob
        s1 = 1000 - s3 - s2
        for _ in range(9):    # 前9连
            self.gacha_one(up, s3, s2, s1, recordcard=True)
        self.gacha_one(up, s3, s2 + s1, 0, recordcard=True)    # 保底第10抽

        return self.result

    def gacha_tenjou(self, num=300, only_for_up=False, aimup=0):
        first_up_pos = num
        up = self.up_prob
        s3 = self.s3_prob
        s2 = self.s2_prob
        s1 = 1000 - s3 - s2
        for i in range(num):
            lup = self.result['up']
            is_10 = int((i+1) % 10 == 0)
            self.gacha_one(up, s3, s2+s1*is_10, s1*(1-is_10), True)
            rup = self.result['up']
            if lup == 0 and rup == 1:
                first_up_pos = i+1
            if lup < rup and only_for_up:
                aimid = chara.name2id(self.up[aimup])
                getid = self.result['chara'][-1].id
                if aimid == getid or self.up[aimup] in self.result['chara']:
                    self.result['first_up_pos'] = first_up_pos
                    return self.result
        self.result['first_up_pos'] = first_up_pos
        return self.result
