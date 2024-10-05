import datetime
import enum
import secrets
import sqlalchemy.orm
import typing
import ulid

import common


def generate_id(
  prefix: typing.Optional[str],
  secure: bool = False
):
  if secure:
    identifier = secrets.token_urlsafe(16)
  else:
    identifier = str(ulid.ULID())
  if prefix:
    return f"{prefix}_{identifier}"
  else:
    return identifier


class Base(sqlalchemy.orm.DeclarativeBase):
  pass


class LogType(enum.StrEnum):
  FORGOT_PASSWORD_EMAIL_NOT_FOUND = "FORGOT_PASSWORD_EMAIL_NOT_FOUND"
  FORGOT_PASSWORD_TOKEN_SENT = "FORGOT_PASSWORD_TOKEN_SENT"
  INTERCOM_ADDED = "INTERCOM_ADDED"
  LOGIN_PASSWORD_HASH_INVALID = "LOGIN_PASSWORD_HASH_INVALID"
  LOGIN_PASSWORD_INCORRECT = "LOGIN_PASSWORD_INCORRECT"
  LOGIN_SUCCESS = "LOGIN_SUCCESS"
  LOGIN_USER_NOT_FOUND = "LOGIN_USER_NOT_FOUND"
  PASSWORD_CHANGE = "PASSWORD_CHANGE"
  PASSWORD_RESET_SUCCESS = "PASSWORD_RESET_SUCCESS"
  PASSWORD_RESET_TOKEN_NOT_FOUND = "RESET_PASSWORD_RESET_TOKEN_NOT_FOUND"
  REGISTER_USER = "REGISTER_USER"
  REGISTER_USER_EMAIL_EXISTS = "REGISTER_USER_EMAIL_EXISTS"


class Intercom(Base):
  __tablename__ = "intercom"

  intercom_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(primary_key=True, default=lambda:generate_id("intercom"))
  name: sqlalchemy.orm.Mapped[str]
  display_name: sqlalchemy.orm.Mapped[typing.Optional[str]]
  serial_number: sqlalchemy.orm.Mapped[str]
  phone_number: sqlalchemy.orm.Mapped[str]


class Log(Base):
  __tablename__ = "log"

  log_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(primary_key=True, default=lambda:generate_id("log"))
  timestamp: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
    sqlalchemy.DateTime(timezone=True),
    server_default = sqlalchemy.sql.func.now()
  )
  user_id: sqlalchemy.orm.Mapped[typing.Optional[str]]
  entity_id: sqlalchemy.orm.Mapped[typing.Optional[str]]
  remote_address: sqlalchemy.orm.Mapped[typing.Optional[str]]
  type: sqlalchemy.orm.Mapped[LogType]
  message: sqlalchemy.orm.Mapped[str]


class PasswordResetToken(Base):
  __tablename__ = "password_reset_token"

  token_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
    primary_key = True,
    default = lambda:generate_id(prefix="token", secure=True)
  )
  user_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.ForeignKey("user.user_id"))
  created: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
    sqlalchemy.DateTime(timezone=True),
    server_default = sqlalchemy.sql.func.now()
  )


class User(Base):
  __tablename__ = "user"

  user_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(primary_key=True, default=lambda:generate_id("user"))
  login_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(default=lambda:generate_id("login"))
  created: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
    sqlalchemy.DateTime(timezone=True),
    server_default = sqlalchemy.sql.func.now()
  )
  email: sqlalchemy.orm.Mapped[str]
  password_hash: sqlalchemy.orm.Mapped[str]
  name: sqlalchemy.orm.Mapped[typing.Optional[str]]
