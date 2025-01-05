from ast import Index

import flask
import flask_login
import flask_wtf
import re
import wtforms

import common
import database
import model


CALL_POINT_MAX_RING_SECS = 240
CALL_POINT_MIN_RING_SECS = 10
CALL_POINT_NAME_MAX_LENGTH = 15
CALL_POINT_NUMBER_OF_OPTIONAL_NUMBERS = 7


intercom_blueprint = flask.Blueprint("intercom", __name__, template_folder="templates/intercom")


def validate_phone_number_uk(form, field):
  number = field.data

  if number == "":
    return

  # normalise format
  if number.startswith("+"):
    if number.startswith("+44"):
      number.replace("+44", "0", 1)
    else:
      raise wtforms.validators.ValidationError("Only UK phone numbers are allowed, international format numbers should start with +44")
  number.replace(" ", "")

  if len(number) not in (10, 11):
    raise wtforms.validators.ValidationError("UK phone numbers should be 10 or 11 digits long")

  if (number.startswith("05")
      or number.startswith("084")
      or number.startswith("087")
      or number.startswith("09")):
    raise wtforms.validators.ValidationError("Premium rate numbers are not allowed")

  # see https://www.ofcom.org.uk/phones-and-broadband/phone-numbers/numbering-data/ for number ranges

  if (number.startswith("01481")
      or number.startswith("07781")
      or number.startswith("07839")
      or number.startswith("07911")):
    raise wtforms.validators.ValidationError("Guernsey numbers are not allowed")

  if (number.startswith("01624")
      or number.startswith("074184")
      or number.startswith("074520")
      or number.startswith("074521")
      or number.startswith("074522")
      or number.startswith("074523")
      or number.startswith("074524")
      or number.startswith("074525")
      or number.startswith("074526")
      or number.startswith("074576")
      or number.startswith("07524")
      or number.startswith("07624")
      or number.startswith("07924")):
    raise wtforms.validators.ValidationError("Isle of Man numbers are not allowed")

  if (number.startswith("01534")
      or number.startswith("07509")
      or number.startswith("07700")
      or number.startswith("07797")
      or number.startswith("07829")
      or number.startswith("07937")):
    raise wtforms.validators.ValidationError("Jersey numbers are not allowed")


class AddIntercomForm(flask_wtf.FlaskForm):
  name = wtforms.StringField("Name", validators=[wtforms.validators.InputRequired()])
  serial_number = wtforms.StringField("Serial Number", validators=[wtforms.validators.InputRequired()])
  phone_number = wtforms.StringField("Phone Number", validators=[wtforms.validators.InputRequired(), validate_phone_number_uk])
  submit = wtforms.SubmitField("Add Intercom")

  # TODO: consider adding custom validation for serial number


class AddUnitForm(flask_wtf.FlaskForm):
  name = wtforms.StringField("Name", validators=[wtforms.validators.InputRequired()])
  submit = wtforms.SubmitField("Add Unit")


class AddCallPointForm(flask_wtf.FlaskForm):
  number = wtforms.StringField("Number", validators=[wtforms.validators.InputRequired()])
  submit = wtforms.SubmitField("Add Call Point")

  # TODO: validate that number is unique on intercom


class CallPointContactForm(flask_wtf.Form):
  number = wtforms.StringField(validators=[validate_phone_number_uk])
  note = wtforms.StringField()
  ring_secs = wtforms.IntegerField(validators=[wtforms.validators.Optional()])
  mon = wtforms.BooleanField(default=True)
  tue = wtforms.BooleanField(default=True)
  wed = wtforms.BooleanField(default=True)
  thu = wtforms.BooleanField(default=True)
  fri = wtforms.BooleanField(default=True)
  sat = wtforms.BooleanField(default=True)
  sun = wtforms.BooleanField(default=True)

  def validate_ring_secs(self, field):
    if self.number == "":
      if field.data is not None:
        raise wtforms.validators.ValidationError("Ring time must not be set if no number is set")
    else:
      if field.data is None:
        raise wtforms.validators.ValidationError("Ring time must be set if a number is set")
      elif field.data < CALL_POINT_MIN_RING_SECS:
        raise wtforms.validators.ValidationError(f"Ring time must be at least {str(CALL_POINT_MIN_RING_SECS)} seconds")
      elif field.data > CALL_POINT_MAX_RING_SECS:
        raise wtforms.validators.ValidationError(f"Ring time must not exceed {str(CALL_POINT_MAX_RING_SECS)} seconds")


class EditCallPointForm(flask_wtf.FlaskForm):
  name = wtforms.StringField("Name", validators=[wtforms.validators.InputRequired()])
  first_number = wtforms.StringField(validators=[wtforms.validators.InputRequired(), validate_phone_number_uk])
  first_number_note = wtforms.StringField()
  first_number_ring_secs = wtforms.IntegerField()
  first_number_mon = wtforms.BooleanField(default=True)
  first_number_tue = wtforms.BooleanField(default=True)
  first_number_wed = wtforms.BooleanField(default=True)
  first_number_thu = wtforms.BooleanField(default=True)
  first_number_fri = wtforms.BooleanField(default=True)
  first_number_sat = wtforms.BooleanField(default=True)
  first_number_sun = wtforms.BooleanField(default=True)
  optional_contacts = wtforms.FieldList(wtforms.FormField(CallPointContactForm), min_entries=CALL_POINT_NUMBER_OF_OPTIONAL_NUMBERS)
  submit = wtforms.SubmitField("Save changes")

  def validate_name(selfself, field):
    if len(field.data) > CALL_POINT_NAME_MAX_LENGTH:
      raise wtforms.validators.ValidationError("Call point name cannot exceed 15 characters in length")
    if not re.match(r"^[A-Za-z0-9\&\-\+\(\)\/\*\:\;\!\?\ ]*$", field.data):
      raise wtforms.validators.ValidationError(
        "Call point name can only contain letters, numbers, and basic punctuation")

  def validate_first_number_ring_secs(self, field):
      if field.data < CALL_POINT_MIN_RING_SECS:
        raise wtforms.validators.ValidationError(f"Ring time must be at least {str(CALL_POINT_MIN_RING_SECS)} seconds")
      elif field.data > CALL_POINT_MAX_RING_SECS:
        raise wtforms.validators.ValidationError(f"Ring time must not exceed {str(CALL_POINT_MAX_RING_SECS)} seconds")


class EditIntercomForm(flask_wtf.FlaskForm):
  name = wtforms.StringField("Name", validators=[wtforms.validators.InputRequired()])
  display_name = wtforms.StringField("Display Name")
  phone_number = wtforms.StringField("Phone Number", validators=[wtforms.validators.InputRequired()])
  submit = wtforms.SubmitField("Edit Intercom")

  # TODO: validate display name character limit (and charset)


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
    "intercom_add.html",
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
    if form.phone_number.data != intercom.phone_number:
      new_details["phone_number"] = form.phone_number.data
    if new_details:
      database.update_intercom(intercom_id, **new_details)
      # TODO: if we updated the display name, send a SMS
      intercom = database.select_intercom_by_id(intercom_id)
  flask.session["current_intercom_id"] = intercom.intercom_id
  form.name.data = intercom.name
  form.display_name.data = intercom.display_name
  form.phone_number.data = intercom.phone_number
  # TODO: add call point numbers to units and sort
  return common.render_template(
    "intercom.html",
    form = form,
    intercom = intercom
  )


@intercom_blueprint.route("/intercom/<intercom_id>/unit/add", methods=["GET", "POST"])
@flask_login.login_required
def add_intercom_unit(intercom_id):
  # TODO: allow an existing unit to be added
  intercom = database.select_intercom_by_id(intercom_id)
  if intercom is None:
    return flask.abort(404)
  form = AddUnitForm()
  if form.validate_on_submit():
    database.insert_unit(model.Unit(
      name = form.name.data,
      intercoms = [intercom]
    ))
    return flask.redirect(f"/intercom/{intercom_id}")
  return common.render_template(
    "unit_add.html",
    form = form,
    intercom = intercom
  )


@intercom_blueprint.route("/intercom/<intercom_id>/unit/<unit_id>", methods=["GET", "POST"])
@flask_login.login_required
def edit_intercom_unit(intercom_id, unit_id):
  intercom = database.select_intercom_by_id(intercom_id)
  unit = database.select_unit_by_id(unit_id)
  if intercom is None or unit is None or intercom.intercom_id not in [i.intercom_id for i in unit.intercoms]:
    return flask.abort(404)
  call_points = database.select_call_points_by_intercom_id_and_unit_id(
    intercom_id = intercom.intercom_id,
    unit_id = unit.unit_id
  )
  return common.render_template(
    "unit.html",
    intercom = intercom,
    unit = unit,
    call_points = call_points
  )


@intercom_blueprint.route("/intercom/<intercom_id>/unit/<unit_id>/call_point/add", methods=["GET", "POST"])
@flask_login.login_required
def add_intercom_unit_call_point(intercom_id, unit_id):
  intercom = database.select_intercom_by_id(intercom_id)
  unit = database.select_unit_by_id(unit_id)
  if intercom is None or unit is None or intercom.intercom_id not in [i.intercom_id for i in unit.intercoms]:
    return flask.abort(404)
  form = AddCallPointForm()
  if form.validate_on_submit():
    default_contacts = [{
      "number": "01444663303",
      "note": "",
      "ring_secs": 10,
      "mon": True,
      "tue": True,
      "wed": True,
      "thu": True,
      "fri": True,
      "sat": True,
      "sun": True
    }]
    default_contacts += [{
      "number": "",
      "note": "",
      "ring_secs": None,
      "mon": True,
      "tue": True,
      "wed": True,
      "thu": True,
      "fri": True,
      "sat": True,
      "sun": True
    }] * CALL_POINT_NUMBER_OF_OPTIONAL_NUMBERS
    database.insert_call_point(model.CallPoint(
      intercom_id = intercom_id,
      unit_id = unit_id,
      number = form.number.data,
      name = f"Flat {form.number.data}",
      contacts = default_contacts
    ))
    return flask.redirect(f"/intercom/{intercom_id}/unit/{unit_id}")
  return common.render_template(
    "call_point_add.html",
    intercom = intercom,
    unit = unit,
    form = form
  )


@intercom_blueprint.route("/intercom/<intercom_id>/unit/<unit_id>/call_point/<call_point_id>", methods=["GET", "POST"])
@flask_login.login_required
def edit_intercom_unit_call_point(intercom_id, unit_id, call_point_id):
  intercom = database.select_intercom_by_id(intercom_id)
  unit = database.select_unit_by_id(unit_id)
  if intercom is None or unit is None or intercom.intercom_id not in [i.intercom_id for i in unit.intercoms]:
    return flask.abort(404)
  call_point = database.select_call_point_by_id(call_point_id)
  if call_point is None or call_point.intercom_id != intercom_id:
    return flask.abort(404)
  form = EditCallPointForm()
  if form.validate_on_submit():
    new_details = {}
    contacts_from_form = [
      {
        "number": form.first_number.data,
        "note": form.first_number_note.data,
        "ring_secs": form.first_number_ring_secs.data,
        "mon": form.first_number_mon.data,
        "tue": form.first_number_tue.data,
        "wed": form.first_number_wed.data,
        "thu": form.first_number_thu.data,
        "fri": form.first_number_fri.data,
        "sat": form.first_number_sat.data,
        "sun": form.first_number_sun.data,
      }
    ]
    contacts_from_form += form.optional_contacts.data
    if form.name.data != call_point.name:
      new_details["name"] = form.name.data
    if contacts_from_form != call_point.contacts:
      new_details["contacts"] = contacts_from_form
    if new_details:
      database.update_call_point(call_point_id, **new_details)
      # TODO: send SMS if required
    return flask.redirect(f"/intercom/{intercom_id}/unit/{unit_id}/call_point/{call_point_id}")
  form.name.data = call_point.name
  form.first_number.data = call_point.contacts[0]["number"]
  form.first_number_note.data = call_point.contacts[0]["note"]
  form.first_number_ring_secs.data = call_point.contacts[0]["ring_secs"]
  form.first_number_mon.data = call_point.contacts[0]["mon"]
  form.first_number_tue.data = call_point.contacts[0]["tue"]
  form.first_number_wed.data = call_point.contacts[0]["wed"]
  form.first_number_thu.data = call_point.contacts[0]["thu"]
  form.first_number_fri.data = call_point.contacts[0]["fri"]
  form.first_number_sat.data = call_point.contacts[0]["sat"]
  form.first_number_sun.data = call_point.contacts[0]["sun"]
  for i in range(CALL_POINT_NUMBER_OF_OPTIONAL_NUMBERS):
    try:
      form.optional_contacts[i].number.data = call_point.contacts[i+1]["number"]
      form.optional_contacts[i].note.data = call_point.contacts[i+1]["note"]
      form.optional_contacts[i].ring_secs.data = call_point.contacts[i+1]["ring_secs"]
      form.optional_contacts[i].mon.data = call_point.contacts[i+1]["mon"]
      form.optional_contacts[i].tue.data = call_point.contacts[i+1]["tue"]
      form.optional_contacts[i].wed.data = call_point.contacts[i+1]["wed"]
      form.optional_contacts[i].thu.data = call_point.contacts[i+1]["thu"]
      form.optional_contacts[i].fri.data = call_point.contacts[i+1]["fri"]
      form.optional_contacts[i].sat.data = call_point.contacts[i+1]["sat"]
      form.optional_contacts[i].sun.data = call_point.contacts[i+1]["sun"]
    except IndexError:
      pass
  return common.render_template(
    "call_point_edit.html",
    intercom = intercom,
    unit = unit,
    call_point = call_point,
    form = form
  )
