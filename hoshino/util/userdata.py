from operator import index
import os
from peewee import ForeignKeyField, Model, SqliteDatabase, IntegerField, CharField, CompositeKey

dbpath = os.path.expanduser('~/.hoshino/Usersdata.db')
os.makedirs(os.path.dirname(dbpath), exist_ok=True)

db = SqliteDatabase(dbpath)


class BaseModel(Model):

    class Meta:
        u"""指定数据库."""
        database = db


class Users(BaseModel):
    uid = IntegerField(unique=True, primary_key=True)
    nickname = CharField(null=True)
    favorpoint = IntegerField(default=0)
    safelevel = IntegerField(default=0)


class Groups(BaseModel):
    gid = IntegerField(unique=True, primary_key=True)
    safelevel = IntegerField(default=0)
    myrole = CharField(default='member')


class Groupmembers(BaseModel):
    gid = ForeignKeyField(Groups, backref='members')
    uid = ForeignKeyField(Users, backref='groups')
    card = CharField(null=True)
    title = CharField(null=True)

    class Meta:
        primary_key = CompositeKey('uid', 'gid')
        indexs = (
            # create a unique on uid/name
            (('uid', 'gid'), True),
        )

db.connect()
db.create_tables([Users, Groups, Groupmembers])
db.close()
