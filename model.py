import datetime
import enum
import sqlalchemy.orm
import typing


class Base(sqlalchemy.orm.DeclarativeBase):
  pass


class LogType(enum.StrEnum):
  FORGOT_PASSWORD_EMAIL_NOT_FOUND = "FORGOT_PASSWORD_EMAIL_NOT_FOUND"
  FORGOT_PASSWORD_TOKEN_SENT = "FORGOT_PASSWORD_TOKEN_SENT"
  LOGIN_PASSWORD_INCORRECT = "LOGIN_PASSWORD_INCORRECT"
  LOGIN_SUCCESS = "LOGIN_SUCCESS"
  LOGIN_USER_NOT_FOUND = "LOGIN_USER_NOT_FOUND"
  PASSWORD_CHANGE = "PASSWORD_CHANGE"
  PASSWORD_RESET_SUCCESS = "PASSWORD_RESET_SUCCESS"
  PASSWORD_RESET_TOKEN_NOT_FOUND = "RESET_PASSWORD_RESET_TOKEN_NOT_FOUND"
  REGISTER_USER = "REGISTER_USER"
  REGISTER_USER_EMAIL_EXISTS = "REGISTER_USER_EMAIL_EXISTS"


class Log(Base):
  __tablename__ = "log"

  log_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(primary_key=True)
  timestamp: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
    sqlalchemy.DateTime(timezone=True),
    server_default=sqlalchemy.sql.func.now()
  )
  entity_id: sqlalchemy.orm.Mapped[typing.Optional[str]]
  remote_address: sqlalchemy.orm.Mapped[typing.Optional[str]]
  type: sqlalchemy.orm.Mapped[LogType]
  message: sqlalchemy.orm.Mapped[str]


class PasswordResetToken(Base):
  __tablename__ = "password_reset_token"

  token_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(primary_key=True)
  user_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.ForeignKey("user.user_id"))
  created: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
    sqlalchemy.DateTime(timezone=True),
    server_default=sqlalchemy.sql.func.now()
  )


class User(Base):
  __tablename__ = "user"

  user_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(primary_key=True)
  login_id: sqlalchemy.orm.Mapped[str]
  created: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
    sqlalchemy.DateTime(timezone=True),
    server_default=sqlalchemy.sql.func.now()
  )
  email: sqlalchemy.orm.Mapped[str]
  password_hash: sqlalchemy.orm.Mapped[str]
  name: sqlalchemy.orm.Mapped[typing.Optional[str]]
