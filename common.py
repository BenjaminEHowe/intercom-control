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
  return flask.render_template(
    name,
    current_user = flask_login.current_user,
    hash = get_git_hash(),
    intercoms = sorted(database.select_intercoms(), key=lambda intercom: intercom.name),
    logout_form = LogoutForm(),
    session = flask.session,
    **kwargs
  )
