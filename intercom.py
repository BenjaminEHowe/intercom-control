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


class EditIntercomForm(AddIntercomForm):
  display_name = wtforms.StringField("Display Name")
  submit = wtforms.SubmitField("Edit Intercom")

  # TODO: validate display name character limit


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


@intercom_blueprint.route("/intercom/<intercom_id>", methods=["GET", "POST"])
@flask_login.login_required
def edit_intercom(intercom_id):
  intercom = database.select_intercom_by_id(intercom_id)
  if intercom is None:
    return flask.abort(404)
  form = EditIntercomForm()
  if form.validate_on_submit():
    new_details = {}
    if form.name.data != intercom.name:
      new_details["name"] = form.name.data
    if form.display_name.data != intercom.display_name:
      new_details["display_name"] = form.display_name.data
    if form.serial_number.data != intercom.serial_number:
      new_details["serial_number"] = form.serial_number.data
    if form.phone_number.data != intercom.phone_number:
      new_details["phone_number"] = form.phone_number.data
    if new_details:
      database.update_intercom(intercom_id, **new_details)
      # TODO: if we updated the display name, send a SMS
      intercom = database.select_intercom_by_id(intercom_id)
  flask.session["current_intercom_id"] = intercom.intercom_id
  flask.session["current_intercom_name"] = intercom.name
  form.name.data = intercom.name
  form.display_name.data = intercom.display_name
  form.serial_number.data = intercom.serial_number
  form.phone_number.data = intercom.phone_number
  return common.render_template(
    "intercom.html",
    form = form,
    intercom = intercom
  )
