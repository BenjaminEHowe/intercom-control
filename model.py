import datetime
import enum
import sqlalchemy.orm
import typing


class Base(sqlalchemy.orm.DeclarativeBase):
  pass


class LogType(enum.StrEnum):
  LOGIN_PASSWORD_INCORRECT = "LOGIN_PASSWORD_INCORRECT"
  LOGIN_USER_NOT_FOUND = "LOGIN_USER_NOT_FOUND"


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


class User(Base):
  __tablename__ = "user"

  user_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(primary_key=True)
  login_id: sqlalchemy.orm.Mapped[str]
  email: sqlalchemy.orm.Mapped[str]
  password_hash: sqlalchemy.orm.Mapped[str]
  name: sqlalchemy.orm.Mapped[typing.Optional[str]]
