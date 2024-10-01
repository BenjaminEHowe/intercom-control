import flask
import flask_login
import flask_wtf
import git
import secrets
import typing
import ulid


class LogoutForm(flask_wtf.FlaskForm):
  pass


def generate_id(
  prefix: typing.Optional[str],
  secure: bool = False
):
  if secure:
    identifier = secrets.token_urlsafe(16)
  else:
    identifier = str(ulid.ULID())
  if prefix:
    return f"{prefix}_{identifier}"
  else:
    return identifier


def get_git_hash():
  repo = git.Repo()
  return repo.head.object.hexsha


def render_template(name, **kwargs):
  return flask.render_template(
    name,
    current_user = flask_login.current_user,
    hash = get_git_hash(),
    logout_form=LogoutForm(),
    **kwargs
  )
