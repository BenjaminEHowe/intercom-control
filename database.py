import os
import sqlalchemy
import sqlalchemy.orm
import typing

import model


connection_string = os.environ.get("SQLALCHEMY_CONNECTION_STRING") or "sqlite:///sqlite.db"
engine = sqlalchemy.create_engine(connection_string)


def delete_password_reset_tokens(user_id: str):
  with sqlalchemy.orm.Session(engine) as session:
    statement = sqlalchemy.delete(model.PasswordResetToken).where(model.PasswordResetToken.user_id == user_id)
    session.execute(statement)
    session.commit()


def insert_intercom(intercom: model.Intercom) -> model.Intercom:
  with sqlalchemy.orm.Session(engine, expire_on_commit=False) as session:
    session.add(intercom)
    session.commit()
  return intercom


def insert_logs(logs: typing.Sequence[model.Log]):
  with sqlalchemy.orm.Session(engine) as session:
    session.add_all(logs)
    session.commit()


def insert_log(log: model.Log):
  insert_logs((log, ))


def insert_password_reset_token(token: model.PasswordResetToken) -> model.PasswordResetToken:
  with sqlalchemy.orm.Session(engine, expire_on_commit=False) as session:
    session.add(token)
    session.commit()
  return token


def insert_user(user: model.User) -> model.User:
  with sqlalchemy.orm.Session(engine, expire_on_commit=False) as session:
    session.add(user)
    session.commit()
  return user


def select_intercom_by_id(intercom_id: str):
  with sqlalchemy.orm.Session(engine) as session:
    return session.scalars(
      sqlalchemy.select(model.Intercom).where(model.Intercom.intercom_id == intercom_id)
    ).one_or_none()


def select_intercoms() -> typing.Sequence[model.Intercom]:
  with sqlalchemy.orm.Session(engine) as session:
    return session.scalars(sqlalchemy.select(model.Intercom)).all()


def select_token(token_id: str) -> model.PasswordResetToken:
  with sqlalchemy.orm.Session(engine) as session:
    statement = sqlalchemy.select(model.PasswordResetToken).where(model.PasswordResetToken.token_id == token_id)
    return session.scalars(statement).one_or_none()


def select_user_by_email(email: str) -> model.User:
  with sqlalchemy.orm.Session(engine) as session:
    statement = sqlalchemy.select(model.User).where(model.User.email == email)
    return session.scalars(statement).one_or_none()


def select_user_by_login_id(login_id: str) -> model.User:
  with sqlalchemy.orm.Session(engine) as session:
    statement = sqlalchemy.select(model.User).where(model.User.login_id == login_id)
    return session.scalars(statement).one_or_none()


def select_user_by_user_id(user_id: str) -> model.User:
  with sqlalchemy.orm.Session(engine) as session:
    statement = sqlalchemy.select(model.User).where(model.User.user_id == user_id)
    return session.scalars(statement).one_or_none()


def update_intercom(intercom_id: str, **kwargs):
  with sqlalchemy.orm.Session(engine) as session:
    statement = sqlalchemy.update(model.Intercom).where(model.Intercom.intercom_id == intercom_id).values(**kwargs)
    session.execute(statement)
    session.commit()


def update_user(user_id: str, **kwargs):
  with sqlalchemy.orm.Session(engine) as session:
    statement = sqlalchemy.update(model.User).where(model.User.user_id == user_id).values(**kwargs)
    session.execute(statement)
    session.commit()
