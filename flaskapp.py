import flask
import flask_login
import os

import common
import database
import intercom
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


app.register_blueprint(intercom.intercom_blueprint)
app.register_blueprint(user.user_blueprint)


@app.route("/", methods=["GET"])
def index():
  return common.render_template("about.html")


if __name__ == "__main__":
  model.Base.metadata.create_all(database.engine)
  app.run()
