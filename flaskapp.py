import flask
import flask_login
import os

import common
import user


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.session_protection = "strong" # see https://flask-login.readthedocs.io/en/0.6.3/#session-protection

@login_manager.user_loader
def user_loader(user_id):
  return user.User(user_id)


@app.route("/", methods=["GET"])
def index():
  return common.render_template("about.html")


@app.route("/login", methods=["GET", "POST"])
def login():
  form = user.LoginForm()
  if form.validate_on_submit():
    user_id = form.username.data
    flask_login.login_user(
      user.User(user_id),
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


if __name__ == "__main__":
  app.run()
