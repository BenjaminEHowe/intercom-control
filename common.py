import flask
import flask_login
import git

import user


def get_git_hash():
  repo = git.Repo()
  return repo.head.object.hexsha


def render_template(name, **kwargs):
  return flask.render_template(
    name,
    current_user = flask_login.current_user,
    hash = get_git_hash(),
    logout_form=user.LogoutForm(),
    **kwargs
  )
