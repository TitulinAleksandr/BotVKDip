import psycopg2
import sqlalchemy
from sqlalchemy import create_engine, MetaData, Table, Integer, String, \
    Column, DateTime, ForeignKey, Numeric
import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
from datetime import datetime

Db_cb = declarative_base()

class Vk_users(Db_cb):
    __tablename__ = 'vk_users'

    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.String, unique=True)

class Contacts(Db_cb):
    __tablename__ = 'contacts'

    id = sq.Column(sq.Integer, primary_key=True)
    c_date = sq.Column(sq.DateTime,default=datetime.now)
    user_id = sq.Column(sq.Integer, sq.ForeignKey('vk_users.id'))

    vk_user = relationship("Vk_users")

class Persons(Db_cb):
    __tablename__ = 'persons'

    id = sq.Column(sq.Integer, primary_key=True)
    p_status = sq.Column(sq.Integer)
    user_id = sq.Column(sq.Integer, sq.ForeignKey('vk_users.id'), unique=True)

    vk_user = relationship("Vk_users")

engine = create_engine("postgresql+psycopg2://postgres:openBD@localhost:5432/vk_cbot")

# Db_cb.metadata.drop_all(engine) #удалить все таблицы
Db_cb.metadata.create_all(engine) #создать все таблицы

#
session = Session(bind=engine)

def add_vkid(id):
    u = Vk_users(vk_id=id)
    session.add(u)
    session.commit()

def add_contacts(id, date):
    id = search_id(id)
    u = Contacts(user_id=id, c_date=date)
    session.add(u)
    session.commit()

def add_person(id, st):
    s = search_id(id)
    if not s:
        add_vkid(id)
        print(f"добавили id{id} в базу")
    else:
        print(f"id{id} уже в базе")
    id = search_id(id)
    s = search_person(id)
    if not s:
        u = Persons(user_id=id, p_status=st)
        session.add(u)
        session.commit()
        print("добавили персону в базу")
    else: print("персона уже в базе")

def search_id(uid):
    r = session.query(Vk_users.id).filter(Vk_users.vk_id == uid).first()
    session.commit()
    if r:
        r = r[0]
    return r

def search_vkid(uid):
    r = session.query(Vk_users.vk_id).filter(Vk_users.id == uid).first()
    session.commit()
    if r:
        r = r[0]
    return r

def search_person(uid):
    r = session.query(Persons.id).filter(Persons.user_id == uid).first()
    session.commit()
    if r:
        r = r[0]
    return r

def search_count_persons(status):
    r = session.query(Persons.id).filter(Persons.p_status == status).count()
    session.commit()
    return r

def set_person_status(uid, status):
    r = session.query(Persons.id).filter(Persons.user_id == uid).first()
    if r:
        r = r[0]
    print(f'id{r} set status {status}')
    r = session.query(Persons.id).filter(Persons.user_id == uid).first()
    session.commit()
    i = session.query(Persons).get(r)
    i.p_status = status
    session.add(i)
    session.commit()

def list_person_status(status):
    r = session.query(Persons.id).filter(Persons.p_status == status).all()
    print(f'id{r} status {status}')
    session.commit()
    return r
