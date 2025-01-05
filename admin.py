import flask
import flask_login

import common
import database


admin_blueprint = flask.Blueprint("admin", __name__, template_folder="templates/admin")


@admin_blueprint.route("/admin/users")
@flask_login.login_required
def users():
  user = database.select_user_by_login_id(flask_login.current_user.get_id())
  if not user.superuser:
    flask.abort(403)
  return common.render_template(
    "users.html",
    users = database.select_users()
  )
