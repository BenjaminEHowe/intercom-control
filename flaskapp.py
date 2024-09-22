import flask
import flask_login
import flask_wtf
import git
import os
import wtforms
import wtforms.validators


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]

login_manager = flask_login.LoginManager()
login_manager.init_app(app)


class LoginForm(flask_wtf.FlaskForm):
  username = wtforms.StringField("Username", validators=[wtforms.validators.DataRequired()])


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
      return NotImmplemented
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
    form = LoginForm(),
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
