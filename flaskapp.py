import flask
import flask_login
import os

import common
import database
import model
import user


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.session_protection = "strong" # see https://flask-login.readthedocs.io/en/0.6.3/#session-protection

@login_manager.user_loader
def user_loader(login_id):
  return user.FlaskLoginUser.from_db(database.select_user_by_login_id(login_id))


@app.route("/", methods=["GET"])
def index():
  return common.render_template("about.html")


@app.route("/login", methods=["GET", "POST"])
def login():
  form = user.LoginForm()
  if form.validate_on_submit():
    flask_login.login_user(
      user.FlaskLoginUser.from_db(database.select_user(form.email.data)),
      remember=form.remember_me.data
    )
    return flask.redirect("/")
  return common.render_template(
    "login.html",
    form = form
  )


@app.route("/logout", methods=["POST"])
def logout():
  form = user.LogoutForm()
  if form.validate_on_submit():
    flask_login.logout_user()
  return flask.redirect("/")


@app.route("/user/profile", methods=["GET", "POST"])
@flask_login.login_required
def profile():
  form = user.ProfileForm()
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


if __name__ == "__main__":
  model.Base.metadata.create_all(database.engine)
  app.run()
