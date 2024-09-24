import argon2
import flask
import flask_login
import flask_wtf
import git
import os
import wtforms
import wtforms.validators


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]
argon2_memory_cost = int(os.environ.get("ARGON2_MEMORY_COST") or "65536")
argon2_time_cost = int(os.environ.get("ARGON2_TIME_COST") or "3")

login_manager = flask_login.LoginManager()
login_manager.init_app(app)


class LoginForm(flask_wtf.FlaskForm):
  username = wtforms.StringField("Username", validators=[wtforms.validators.DataRequired()])
  password = wtforms.PasswordField("Password", validators=[wtforms.validators.DataRequired()])

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
  def __init__(self, id):
    self.id = str(id)

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
    return self.id

  def __eq__(self, other):
    if isinstance(other, User):
      return self.get_id() == other.get_id()
    return NotImplemented

  def __ne__(self, other):
    equal = self.__eq__(other)
    if equal is NotImplemented:
      return NotImplemented
    return not equal


def get_git_hash():
  repo = git.Repo()
  return repo.head.object.hexsha


@login_manager.user_loader
def user_loader(user_id):
  return User(user_id)


@app.route("/", methods=["GET"])
def index():
  return flask.render_template(
    "about.html",
    current_user = flask_login.current_user,
    hash = get_git_hash(),
    logout_form = LogoutForm()
  )


@app.route("/login", methods=["GET", "POST"])
def login():
  form = LoginForm()
  if form.validate_on_submit():
    user_id = form.username.data
    flask_login.login_user(
      User(user_id)
    )
    return flask.redirect("/")
  return flask.render_template(
    "login.html",
    current_user = flask_login.current_user,
    form = form,
    hash = get_git_hash(),
    logout_form = LogoutForm()
  )


@app.route("/logout", methods=["POST"])
def logout():
  form = LogoutForm()
  if form.validate_on_submit():
    flask_login.logout_user()
  return flask.redirect("/")


if __name__ == "__main__":
  app.run()
