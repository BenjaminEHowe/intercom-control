import argon2
import flask
import flask_login
import flask_wtf
import os
import wtforms
import wtforms.validators
from flask import request

import common
import database
import mail
import model


argon2_memory_cost = int(os.environ.get("ARGON2_MEMORY_COST") or "65536")
argon2_time_cost = int(os.environ.get("ARGON2_TIME_COST") or "3")
password_hasher = argon2.PasswordHasher(
  memory_cost = argon2_memory_cost,
  time_cost = argon2_time_cost,
)

user_blueprint = flask.Blueprint("user", __name__, template_folder="templates/user")


class PasswordTwiceForm(flask_wtf.FlaskForm):
  password = wtforms.PasswordField("Password", validators=[wtforms.validators.DataRequired()])
  password_again = wtforms.PasswordField("Password, again", validators=[wtforms.validators.DataRequired()])

  def validate_token(self, field):
    if database.select_token(field.data) is None:
      database.insert_log(model.Log(
        remote_address = flask.request.remote_addr,
        type = model.LogType.PASSWORD_RESET_TOKEN_NOT_FOUND,
        message = f"Password reset token {field.data} not found"
      ))
      raise wtforms.validators.ValidationError("Invalid password reset token")

  def validate_password(self, field):
    min_length = 12
    if len(field.data) < min_length:
      raise wtforms.validators.ValidationError(f"Password should be at least {str(min_length)} characters long")


  def validate_password_again(self, field):
    if field.data != self.password.data:
      raise wtforms.validators.ValidationError("Passwords do not match")


class ChangePasswordForm(PasswordTwiceForm):
  current_password = wtforms.PasswordField("Password", validators=[wtforms.validators.DataRequired()])
  submit = wtforms.SubmitField("Change Password")

  def validate_current_password(self, field):
    flask_login_user = flask_login.current_user
    user = database.select_user_by_login_id(flask_login_user.get_id())
    try:
      password_hasher.verify(user.password_hash, field.data)
    except argon2.exceptions.VerifyMismatchError:
      raise wtforms.validators.ValidationError("Password is incorrect")


class ForgotPasswordForm(flask_wtf.FlaskForm):
  email = wtforms.EmailField("Email", validators=[wtforms.validators.DataRequired()])
  submit = wtforms.SubmitField("Request Password Reset")


class LoginForm(flask_wtf.FlaskForm):
  email = wtforms.EmailField("Email", validators=[wtforms.validators.DataRequired()])
  password = wtforms.PasswordField("Password", validators=[wtforms.validators.DataRequired()])
  remember_me = wtforms.BooleanField("Keep me logged in")
  submit = wtforms.SubmitField("Login")

  def validate_email(self, field):
    # note: this function actually validates the username _and_ password
    generic_error = "Invalid email address and / or password"
    user = database.select_user_by_email(self.email.data)
    if user is None:
      database.insert_log(model.Log(
        remote_address = flask.request.remote_addr,
        type = model.LogType.LOGIN_USER_NOT_FOUND,
        message = f"User with email address {self.email.data} not found"
      ))
      raise wtforms.validators.ValidationError(generic_error)
    try:
      password_hasher.verify(user.password_hash, self.password.data)
      if password_hasher.check_needs_rehash(user.password_hash):
        database.update_user(user_id=user.user_id, password_hash=password_hasher.hash(self.password.data))
    except argon2.exceptions.VerifyMismatchError:
      database.insert_log(model.Log(
        user_id = user.user_id,
        entity_id = user.user_id,
        remote_address = flask.request.remote_addr,
        type = model.LogType.LOGIN_PASSWORD_INCORRECT,
        message = "Incorrect password entered"
      ))
      raise wtforms.validators.ValidationError(generic_error)
    except argon2.exceptions.InvalidHashError:
      database.insert_log(model.Log(
        user_id = user.user_id,
        entity_id = user.user_id,
        remote_address = flask.request.remote_addr,
        type = model.LogType.LOGIN_PASSWORD_HASH_INVALID,
        message = f"Password hash \"{user.password_hash}\" is invalid"
      ))
      raise wtforms.validators.ValidationError(generic_error)


class ProfileForm(flask_wtf.FlaskForm):
  email = wtforms.EmailField("Email") # TODO: add validators=[wtforms.validators.DataRequired()] later
  name = wtforms.StringField("Name")
  submit = wtforms.SubmitField("Save")


class RegisterForm(flask_wtf.FlaskForm):
  email = wtforms.EmailField("Email", validators=[wtforms.validators.DataRequired()])
  submit = wtforms.SubmitField("Register")


class ResetPasswordForm(PasswordTwiceForm):
  token = wtforms.HiddenField(validators=[wtforms.validators.DataRequired()])
  submit = wtforms.SubmitField("Request Password Reset")


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


def _generate_and_send_reset_token(user: model.User):
  token = database.insert_password_reset_token(model.PasswordResetToken(user_id=user.user_id))
  database.insert_log(model.Log(
    user_id = user.user_id,
    entity_id = user.user_id,
    remote_address = flask.request.remote_addr,
    type = model.LogType.FORGOT_PASSWORD_TOKEN_SENT,
    message = f"Sending forgot password reset token email to {user.email}"
  ))
  mail.send_email(
    to = user.email,
    message = mail.generate_forgot_password_message(flask.request.root_url, token.token_id)
  )


@user_blueprint.route("/user/change-password", methods=["GET", "POST"])
@flask_login.login_required
def change_password():
  form = ChangePasswordForm()
  success = False
  if form.validate_on_submit():
    user = database.select_user_by_login_id(flask_login.current_user.get_id())
    database.insert_log(model.Log(
      user_id = user.user_id,
      entity_id = user.user_id,
      remote_address = flask.request.remote_addr,
      type = model.LogType.PASSWORD_CHANGE,
      message = "Password changed"
    ))
    database.update_user(
      user_id = user.user_id,
      password_hash = password_hasher.hash(form.password.data)
    )
    success = True
  return common.render_template(
    "change_password.html",
    form = form,
    success = success
  )


@user_blueprint.route("/user/forgot-password", methods=["GET", "POST"])
def forgot_password():
  if flask_login.current_user.is_authenticated:
    return flask.redirect("/")
  form = ForgotPasswordForm()
  if form.validate_on_submit():
    email = form.email.data
    user = database.select_user_by_email(form.email.data)
    if user is None:
      database.insert_log(model.Log(
        remote_address = flask.request.remote_addr,
        type = model.LogType.FORGOT_PASSWORD_EMAIL_NOT_FOUND,
        message = f"Sending account not found forgot password email to {email}"
      ))
      mail.send_email(
        to = email,
        message = mail.generate_forgot_password_message(flask.request.root_url)
      )
    else:
      _generate_and_send_reset_token(user)
  return common.render_template(
    "forgot_password.html",
    form = form
  )


@user_blueprint.route("/user/login", methods=["GET", "POST"])
def login():
  form = LoginForm()
  if form.validate_on_submit():
    user = database.select_user_by_email(form.email.data)
    database.insert_log(model.Log(
      user_id = user.user_id,
      entity_id = user.user_id,
      remote_address = flask.request.remote_addr,
      type = model.LogType.LOGIN_SUCCESS,
      message = f"Successfully logged in"
    ))
    flask_login.login_user(
      FlaskLoginUser.from_db(user),
      remember=form.remember_me.data
    )
    return flask.redirect("/")
  return common.render_template(
    "login.html",
    form = form
  )


@user_blueprint.route("/user/logout", methods=["POST"])
def logout():
  form = common.LogoutForm()
  if form.validate_on_submit():
    flask_login.logout_user()
    flask.session.clear()
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


@user_blueprint.route("/user/register", methods=["GET", "POST"])
def register():
  if flask_login.current_user.is_authenticated:
    return flask.redirect("/")
  form = RegisterForm()
  if form.validate_on_submit():
    email = form.email.data
    user = database.select_user_by_email(email)
    if user is None:
      # TODO: consider adding the below database operations into a single transaction
      user = database.insert_user(model.User(
        email = email,
        password_hash = "invalid"
      ))
      database.insert_log(model.Log(
        user_id = user.user_id,
        entity_id = user.user_id,
        remote_address = flask.request.remote_addr,
        type = model.LogType.REGISTER_USER,
        message = f"Created new user for {email}"
      ))
      _generate_and_send_reset_token(user)
    else:
      database.insert_log(model.Log(
        user_id = user.user_id,
        entity_id = user.user_id,
        remote_address = flask.request.remote_addr,
        type = model.LogType.FORGOT_PASSWORD_TOKEN_SENT,
        message = f"Registration attempt by {user.email} but email address already exists"
      ))
      mail.send_email(
        to = user.email,
        message = mail.generate_registration_account_exists_message(flask.request.root_url)
      )
  return common.render_template(
    "register.html",
    form = form
  )


@user_blueprint.route("/user/reset-password", methods=["GET", "POST"])
def reset_password():
  if flask_login.current_user.is_authenticated:
    return flask.redirect("/")
  form = ResetPasswordForm()
  token_from_query = request.args.get("token")
  if token_from_query:
    form.token.data = token_from_query
  if form.validate_on_submit():
    token = database.select_token(form.token.data)
    user = database.select_user_by_user_id(token.user_id)
    # TODO: consider adding the below database operations into a single transaction
    database.insert_log(model.Log(
      user_id = user.user_id,
      entity_id = user.user_id,
      remote_address = flask.request.remote_addr,
      type = model.LogType.PASSWORD_RESET_SUCCESS,
      message = f"Password successfully reset"
    ))
    database.update_user(
      user_id = user.user_id,
      password_hash = password_hasher.hash(form.password.data)
    )
    database.delete_password_reset_tokens(user.user_id)
    flask_login.login_user( FlaskLoginUser.from_db(user) )
    return flask.redirect("/user/profile")
  return common.render_template(
    "reset_password.html",
    form = form
  )
