import flask
import git


app = flask.Flask(__name__)


def get_git_hash():
  repo = git.Repo()
  return repo.head.object.hexsha


@app.route('/', methods=['GET'])
def index():
  return flask.render_template(
    "about.html",
    hash = get_git_hash()
  )


@app.route('/login', methods=['GET'])
def login():
  repo = git.Repo()
  hash = repo.head.object.hexsha
  return flask.render_template(
    "login.html",
    hash = get_git_hash()
  )


if __name__ == "__main__":
  app.run()
