import flask
import git


app = flask.Flask(__name__)


@app.route('/', methods=['GET'])
def index():
  repo = git.Repo()
  hash = repo.head.object.hexsha
  return flask.render_template(
    "about.html",
    hash=hash
  )


if __name__ == "__main__":
  app.run()
