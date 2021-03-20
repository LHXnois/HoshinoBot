import os
from peewee import Model, SqliteDatabase
from peewee import IntegerField, CharField, CompositeKey

# ====================================== #
db = {}
for i in ['Coins', 'Charas']:
    dbpath = os.path.expanduser(f'~/.hoshino/{i}.db')
    os.makedirs(os.path.dirname(dbpath), exist_ok=True)
    db[i] = SqliteDatabase(dbpath)


class CModel(Model):
    uid = IntegerField(index=True)
    cname = CharField()
    cnum = IntegerField(default=0, index=True)

    class Meta:
        primary_key = CompositeKey('uid', 'cname')
        order_by = ('uid', 'cname', )
        indexes = (
            # create a unique on uid/name
            (('uid', 'cname'), True),
            (('uid', 'cnum'), False)
        )


class Coins(CModel):
    cname = CharField(default='Coin')

    class Meta:
        database = db['Coins']


class Charas(CModel):
    star = IntegerField(default=1)

    class Meta:
        database = db['Charas']


# ============================================ #


class Cmaster:
    Clist = {}

    def __init__(self, uid: int, cname, type, bundle=None):
        if bundle:
            class _(type):

                class Meta:
                    table_name = bundle
            self.db = _
        else:
            self.db = type
        self.db.create_table()
        Cmaster.db = self.db
        self.cname = self.Cmapping(cname)
        self.uid = uid
        self.c = self.get_C
        self.cnum = self.c.cnum

    @classmethod
    def Cmapping(self, cname: str) -> str:
        if cname in self.Clist:
            cname = self.Clist[cname]
        return cname

    @classmethod
    def reCmapping(self, cname: str) -> str:
        for i in self.Clist:
            if self.Clist[i] == cname:
                cname = i
                break
        return cname

    @property
    def get_C(self):
        try:
            return self.db.get_or_create(uid=self.uid, cname=self.cname)[0]
        except Exception as e:
            raise Exception(f'查找表发生错误{str(e)}')

    def add_C(self, num: int) -> int:
        self.cnum += num
        self.__update_C()
        return self.get_C

    def red_C(self, num: int, min_to_zero: bool = True) -> int:
        self.cnum -= num
        if min_to_zero and self.cnum < 0:
            self.cnum = 0
        self.__update_C()
        return self.get_C

    def __update_C(self):
        self.set_Cvalue('cnum', self.cnum)

    def set_Cvalue(self, vname, value):
        try:
            self.db.update({vname: value}).where(
                self.db.uid == self.uid, self.db.cname == self.cname).execute()
        except Exception as e:
            raise Exception(f'更新表发生错误{str(e)}')

    def check_C(self, cneed: int = 1) -> bool:
        return self.cnum >= cneed

    def get_all_C(self, Clist=None) -> dict:
        try:
            if Clist:
                result = self.db.select(self.db.cname, self.db.cnum).where(
                    self.db.uid == self.uid, self.db.cname.in_(Clist))
            else:
                result = self.db.select(self.db.cname, self.db.cnum).where(
                    self.db.uid == self.uid)
            cdic = {self.reCmapping(
                x.cname): x.cnum for x in result.iterator()}
        except Exception as e:
            raise Exception(f'查找表发生错误{str(e)}')
        return cdic

    @classmethod
    def del_C(self, cname, uid: int = None):
        cname = self.Cmapping(cname)
        try:
            if uid is not None:
                self.db.delete().where(
                    self.db.uid == uid, self.db.cname == cname).execute()
            else:
                self.db.delete().where(self.db.cname == cname).execute()
        except Exception as e:
            raise Exception(f'更新表发生错误{str(e)}')

    @classmethod
    def del_user(self, uid: int):
        try:
            self.db.delete().where(self.db.uid == uid).execute()
        except Exception as e:
            raise Exception(f'更新表发生错误{str(e)}')

    @classmethod
    def get_Crank(self, cname: str, uidrange: list) -> list:
        cname = self.Cmapping(cname)
        try:
            result = self.db.select(self.db.uid, self.db.cnum).order_by(
                -self.db.cnum).where(
                    self.db.cname == cname, self.db.uid.in_(uidrange))
            rankdic = list(map(lambda x: {x.uid: x.cnum}, result.iterator()))
        except Exception as e:
            raise Exception(f'查找表发生错误{str(e)}')
        return rankdic


class Coinsmaster(Cmaster):
    db = Coins
    '''
    #货币系统\n
    from hoshino.unit import Coinsmaster\n
    这是触发示例\n
    Cm = Coinsmaster(uid:用户id, coinname:货币名称) #货币名称默认为Coin\n
    num = Cm.cnum 获取货币数量\n
    Cm.add_C(num)增加num的货币\n
    Cm.red_C(num)减少num的货币，最低降为0\n
    Cm.check_C(num)检查是否有num那么多的货币\n
    Cm.get_all_C(货币列表) 以字典格式返回所有货币信息，{coinname：coinnum}\n

    #以下是静态方法，不需要实例化\n
    Coinsmaster.get_Crank(coinname: str, uidrange: list)获取所给用户列表的货币数量排名\n
    Coinsmaster.del_C(coinname,uid)删除货币coinname，若不提供uid则删除所有用户的该\n
    Coinsmaster.del_user(uid)删除用户所有记录\n
    '''

    def __init__(self, uid: int, coinname: str = 'Coin', bundle='coins'):
        if not coinname:
            raise TypeError('货币名不能为空！')
        if db['Coins'].is_closed():
            db['Coins'].connect()
        super().__init__(uid, coinname, Coins, bundle)

    def __del__(self):
        db['Coins'].close()


class Charasmaster(Cmaster):

    def __init__(self, uid: int, cname, bundle, type=Charas):
        if not cname:
            raise TypeError('角色名不能为空！')
        if db['Charas'].is_closed():
            db['Charas'].connect()
        super().__init__(uid, cname, type, bundle)

    def __del__(self):
        db['Charas'].close()

    @property
    def check_Cexist(self) -> bool:
        return super().check_C(cneed=1)

    def get_exist_C(self, Clist=None):
        try:
            if Clist:
                result = self.db.select(self.db.cname, self.db.star).order_by(
                    -self.db.star).where(
                    self.db.uid == self.uid,
                    self.db.cname.in_(Clist),
                    self.db.cnum > 0)
            else:
                result = self.db.select(self.db.cname, self.db.star).order_by(
                    -self.db.star).where(
                        self.db.uid == self.uid, self.db.cnum > 0)
            eclist = [(self.reCmapping(
                x.cname), x.star) for x in result.iterator()]
        except Exception as e:
            raise Exception(f'查找表发生错误{str(e)}')
        return eclist
