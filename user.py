import argon2
import flask_wtf
import os
import wtforms
import wtforms.validators

import database
import model


argon2_memory_cost = int(os.environ.get("ARGON2_MEMORY_COST") or "65536")
argon2_time_cost = int(os.environ.get("ARGON2_TIME_COST") or "3")


class LoginForm(flask_wtf.FlaskForm):
  email = wtforms.EmailField("Email", validators=[wtforms.validators.DataRequired()])
  password = wtforms.PasswordField("Password", validators=[wtforms.validators.DataRequired()])
  remember_me = wtforms.BooleanField("Keep me logged in")
  submit = wtforms.SubmitField("Login")

  def validate_email(self, field):
    # note: this function actually validates the username _and_ password
    generic_error = "Invalid email address and / or password"
    user = database.select_user(self.email.data)
    password_hasher = argon2.PasswordHasher(
      memory_cost=argon2_memory_cost,
      time_cost=argon2_time_cost,
    )
    try:
      password_hasher.verify(user.password_hash, self.password.data)
      if password_hasher.check_needs_rehash(user.password_hash):
        database.update_user(user_id=user.user_id, password_hash=password_hasher.hash(self.password.data))
    except argon2.exceptions.VerifyMismatchError:
      raise wtforms.validators.ValidationError(generic_error)


class LogoutForm(flask_wtf.FlaskForm):
  pass


class User:
  @classmethod
  def from_db(cls, user: model.User):
    return cls(
      user_id = user.login_id,
      email = user.email,
      name = user.name
    )

  def __init__(self, user_id, email, name):
    self.user_id = user_id
    self.email = email
    self.name = name

  # Python 3 implicitly set __hash__ to None if we override __eq__
  # We set it back to its default implementation
  __hash__ = object.__hash__

  @property
  def is_active(self):
    return True

  @property
  def is_authenticated(self):
    return self.is_active

  @property
  def is_anonymous(self):
    return False

  def get_id(self):
    return self.user_id

  def get_name(self):
    if self.name:
      return self.name
    else:
      return self.email

  def __eq__(self, other):
    if isinstance(other, User):
      return self.get_id() == other.get_id()
    return NotImplemented

  def __ne__(self, other):
    equal = self.__eq__(other)
    if equal is NotImplemented:
      return NotImplemented
    return not equal
