import os
import sqlalchemy
import sqlalchemy.orm
import typing

import model


connection_string = os.environ.get("SQLALCHEMY_CONNECTION_STRING") or "sqlite:///sqlite.db"
engine = sqlalchemy.create_engine(connection_string)


def insert_logs(logs: typing.Sequence[model.Log]):
  with sqlalchemy.orm.Session(engine) as session:
    session.add_all(logs)
    session.commit()


def insert_log(log: model.Log):
  insert_logs((log, ))


def insert_users(users: typing.Sequence[model.User]):
  with sqlalchemy.orm.Session(engine) as session:
    session.add_all(users)
    session.commit()


def insert_user(user: model.User):
  insert_users((user, ))


def select_user(email: str) -> model.User:
  with sqlalchemy.orm.Session(engine) as session:
    statement = sqlalchemy.select(model.User).where(model.User.email == email)
    return session.scalars(statement).one_or_none()


def select_user_by_login_id(login_id: str) -> model.User:
  with sqlalchemy.orm.Session(engine) as session:
    statement = sqlalchemy.select(model.User).where(model.User.login_id == login_id)
    return session.scalars(statement).one_or_none()


def update_user(user_id: str, **kwargs):
  with sqlalchemy.orm.Session(engine) as session:
    statement = sqlalchemy.update(model.User).where(model.User.user_id == user_id).values(**kwargs)
    session.execute(statement)
    session.commit()
