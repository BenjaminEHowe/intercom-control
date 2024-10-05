import flask
import flask_login
import flask_wtf
import wtforms

import common
import database
import model


intercom_blueprint = flask.Blueprint("intercom", __name__, template_folder="templates/intercom")


class AddIntercomForm(flask_wtf.FlaskForm):
  name = wtforms.StringField("Name", validators=[wtforms.validators.DataRequired()])
  serial_number = wtforms.StringField("Serial Number", validators=[wtforms.validators.DataRequired()])
  phone_number = wtforms.StringField("Phone Number", validators=[wtforms.validators.DataRequired()])
  submit = wtforms.SubmitField("Add Intercom")

  # TODO: consider adding custom validation for serial number and phone number


@intercom_blueprint.route("/intercom/add", methods=["GET", "POST"])
@flask_login.login_required
def add_intercom():
  form = AddIntercomForm()
  if form.validate_on_submit():
    user = database.select_user_by_login_id(flask_login.current_user.get_id())
    intercom = database.insert_intercom(model.Intercom(
      name = form.name.data,
      serial_number = form.serial_number.data,
      phone_number = form.phone_number.data
    ))
    database.insert_log(model.Log(
      remote_address = flask.request.remote_addr,
      entity_id = intercom.intercom_id,
      user_id = user.user_id,
      type = model.LogType.INTERCOM_ADDED,
      message = "Intercom added"
    ))
    return flask.redirect(f"/intercom/{intercom.intercom_id}")
  return common.render_template(
    "new_intercom.html",
    form = form
  )


@intercom_blueprint.route("/intercom/<intercom_id>", methods=["GET"])
@flask_login.login_required
def get_intercom(intercom_id):
  intercom = database.select_intercom_by_id(intercom_id)
  if intercom is None:
    return flask.abort(404)
  return common.render_template(
    "intercom.html",
    intercom = intercom
  )

