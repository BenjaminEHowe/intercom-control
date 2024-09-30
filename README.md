# Intercom Control
A web user interface for controlling intercoms.

## Insert user into database

`INSERT INTO "user" (user_id, login_id, email, password_hash, name) VALUES('user_01J8TPT026FPVFDXA5J88EV4NB', 'login_01J8TPSQFQ0WFBQ3T6TDEBDG1J', 'ben@intercom.experimental.win', '$argon2id$v=19$m=65536,t=3,p=4$+vAURrm9UMTsji9V23LXZw$T9A8ivcrWDHXd2/iAGalnwDhbFTBVl2v3u3ywtxZ6FY', NULL);`

(password is `ShouldBeHashed`)

## Environment Variables

- `SECRET_KEY` (required): used by Flask for signing the session cookie, see [Flask's documentation](https://flask.palletsprojects.com/en/3.0.x/config/#SECRET_KEY) for more information.
- `ARGON2_MEMORY_COST`: parameter used for password hashing memory cost, see [argon2-cffi documentation](https://argon2-cffi.readthedocs.io/en/stable/parameters.html) for more information.
- `ARGON2_TIME_COST`: parameter used for password hashing time cost, see [argon2-cffi documentation](https://argon2-cffi.readthedocs.io/en/stable/parameters.html) for more information.
- `SQLALCHEMY_CONNECTION_STRING` (defaults to SQLite): database connection string to use with [SQLAlchemy](https://www.sqlalchemy.org/).
- `SMTP_SERVER` (practically required): server for sending emails via SMTP.
- `SMTP_PORT` (defaults to `465`): port for sending emails over SMTP (using implicit TLS).
- `SMTP_USER`: user for sending email via SMTP server.
- `SMTP_PASSWORD`: password for sending email via SMTP server.
- `SMTP_SENDER`: sender email address if different from `SMTP_USER`.
