import argon2
import flask_wtf
import os
import wtforms
import wtforms.validators


argon2_memory_cost = int(os.environ.get("ARGON2_MEMORY_COST") or "65536")
argon2_time_cost = int(os.environ.get("ARGON2_TIME_COST") or "3")


class LoginForm(flask_wtf.FlaskForm):
  username = wtforms.StringField("Username", validators=[wtforms.validators.DataRequired()])
  password = wtforms.PasswordField("Password", validators=[wtforms.validators.DataRequired()])
  remember_me = wtforms.BooleanField("Keep me logged in")
  submit = wtforms.SubmitField("Login")

  def validate_username(self, field):
    # note: this function actually validates the username _and_ password
    generic_error = "Invalid username and / or password"
    users = {
      "user": "$argon2id$v=19$m=65536,t=3,p=4$+vAURrm9UMTsji9V23LXZw$T9A8ivcrWDHXd2/iAGalnwDhbFTBVl2v3u3ywtxZ6FY", # ShouldBeHashed
    }
    if self.username.data not in users.keys():
      raise wtforms.validators.ValidationError(generic_error)
    password_hasher = argon2.PasswordHasher(
      memory_cost=argon2_memory_cost,
      time_cost=argon2_time_cost,
    )
    try:
      password_hasher.verify(users[self.username.data], self.password.data)
      # TODO: check if password needs rehash, see https://argon2-cffi.readthedocs.io/en/23.1.0/howto.html
    except argon2.exceptions.VerifyMismatchError:
      raise wtforms.validators.ValidationError(generic_error)


class LogoutForm(flask_wtf.FlaskForm):
  pass


class User:
  def __init__(self, user_id):
    self.user_id = str(user_id)

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

  def __eq__(self, other):
    if isinstance(other, User):
      return self.get_id() == other.get_id()
    return NotImplemented

  def __ne__(self, other):
    equal = self.__eq__(other)
    if equal is NotImplemented:
      return NotImplemented
    return not equal
