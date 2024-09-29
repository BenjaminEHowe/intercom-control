import argon2
import flask
import flask_login
import flask_wtf
import os
import ulid
import wtforms
import wtforms.validators

import common
import database
import model


argon2_memory_cost = int(os.environ.get("ARGON2_MEMORY_COST") or "65536")
argon2_time_cost = int(os.environ.get("ARGON2_TIME_COST") or "3")

user_blueprint = flask.Blueprint("user", __name__, template_folder="templates/user")


class LoginForm(flask_wtf.FlaskForm):
  email = wtforms.EmailField("Email", validators=[wtforms.validators.DataRequired()])
  password = wtforms.PasswordField("Password", validators=[wtforms.validators.DataRequired()])
  remember_me = wtforms.BooleanField("Keep me logged in")
  submit = wtforms.SubmitField("Login")

  def validate_email(self, field):
    # note: this function actually validates the username _and_ password
    generic_error = "Invalid email address and / or password"
    user = database.select_user(self.email.data)
    if user is None:
      database.insert_log(model.Log(
        log_id = f"log_{ulid.ULID()}",
        remote_address = flask.request.remote_addr,
        type = model.LogType.LOGIN_USER_NOT_FOUND,
        message = f"User with email address {self.email.data} not found"
      ))
      raise wtforms.validators.ValidationError(generic_error)
    password_hasher = argon2.PasswordHasher(
      memory_cost=argon2_memory_cost,
      time_cost=argon2_time_cost,
    )
    try:
      password_hasher.verify(user.password_hash, self.password.data)
      if password_hasher.check_needs_rehash(user.password_hash):
        database.update_user(user_id=user.user_id, password_hash=password_hasher.hash(self.password.data))
    except argon2.exceptions.VerifyMismatchError:
      database.insert_log(model.Log(
        log_id = f"log_{ulid.ULID()}",
        entity_id = user.user_id,
        remote_address = flask.request.remote_addr,
        type = model.LogType.LOGIN_PASSWORD_INCORRECT,
        message = f"Incorrect password entered for {self.email.data}"
      ))
      raise wtforms.validators.ValidationError(generic_error)


class LogoutForm(flask_wtf.FlaskForm):
  pass


class ProfileForm(flask_wtf.FlaskForm):
  email = wtforms.EmailField("Email") # TODO: add validators=[wtforms.validators.DataRequired()] later
  name = wtforms.StringField("Name")
  submit = wtforms.SubmitField("Save")


class FlaskLoginUser:
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
    if isinstance(other, FlaskLoginUser):
      return self.get_id() == other.get_id()
    return NotImplemented

  def __ne__(self, other):
    equal = self.__eq__(other)
    if equal is NotImplemented:
      return NotImplemented
    return not equal


@user_blueprint.route("/user/login", methods=["GET", "POST"])
def login():
  form = LoginForm()
  if form.validate_on_submit():
    flask_login.login_user(
      FlaskLoginUser.from_db(database.select_user(form.email.data)),
      remember=form.remember_me.data
    )
    return flask.redirect("/")
  return common.render_template(
    "login.html",
    form = form
  )


@user_blueprint.route("/user/logout", methods=["POST"])
def logout():
  form = LogoutForm()
  if form.validate_on_submit():
    flask_login.logout_user()
  return flask.redirect("/")


@user_blueprint.route("/user/profile", methods=["GET", "POST"])
@flask_login.login_required
def profile():
  form = ProfileForm()
  if form.validate_on_submit():
    original_user_details = database.select_user_by_login_id(flask_login.current_user.get_id())
    new_details = {}
    if form.name.data != original_user_details.name:
      new_details["name"] = form.name.data
    if new_details:
      database.update_user(original_user_details.user_id, **new_details)
      return flask.redirect("/user/profile")
  user_details = database.select_user_by_login_id(flask_login.current_user.get_id())
  form.email.data = user_details.email
  form.name.data = user_details.name
  return common.render_template(
    "user/profile.html",
    form = form
  )
