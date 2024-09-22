import flask
import flask_login
import git
import os


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]

login_manager = flask_login.LoginManager()
login_manager.init_app(app)


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
    hash = get_git_hash()
  )


@app.route("/login", methods=["GET", "POST"])
def login():
  request = flask.request
  if request.method == "GET":
    return flask.render_template(
      "login.html",
      current_user = flask_login.current_user,
      hash = get_git_hash()
    )
  else:
    user_id = request.form.get("username")
    flask_login.login_user(
      User(user_id)
    )
    return flask.redirect("/")


@app.route("/logout", methods=["POST"])
def logout():
  flask_login.logout_user()
  return flask.redirect("/")


if __name__ == "__main__":
  app.run()
