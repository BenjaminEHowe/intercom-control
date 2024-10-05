import flask
import flask_login
import flask_wtf
import git

import database


class LogoutForm(flask_wtf.FlaskForm):
  pass


def get_git_hash():
  repo = git.Repo()
  return repo.head.object.hexsha


def render_template(name, **kwargs):
  args = {
    "current_user": flask_login.current_user,
    "hash": get_git_hash(),
    "logout_form": LogoutForm(),
  }

  if flask_login.current_user.is_authenticated:
    args["intercoms"] = sorted(database.select_intercoms(), key=lambda intercom: intercom.name)

    current_intercom_id = flask.session.get("current_intercom_id")
    if current_intercom_id is not None:
      current_intercom = database.select_intercom_by_id(current_intercom_id)
      if current_intercom is not None:
        args["current_intercom_id"] = current_intercom_id
        args["current_intercom_name"] = current_intercom.name

  return flask.render_template(
    name,
    **args,
    **kwargs
  )
