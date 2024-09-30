import os
import smtplib


smtp_server = os.environ.get("SMTP_SERVER")
smtp_port = int(os.environ.get("SMTP_PORT") or "465")
smtp_user = os.environ.get("SMTP_USER")
smtp_password = os.environ.get("SMTP_PASSWORD")
smtp_sender = os.environ.get("SMTP_SENDER") or smtp_user

use_smtp = smtp_server and smtp_port and smtp_user and smtp_password


def send_email(to, message):
  if not use_smtp:
    print("Printing email to stdout as SMTP environment variables are not defined...")
    print(message)
    return
  with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
    server.login(smtp_user, smtp_password)
    message = f"From: {smtp_sender}\nTo:{to}\n{message}"
    server.sendmail(smtp_sender, to, message)


def generate_forgot_password_message(base_url, token=None):
  message = f"""\
Subject: Intercom Control Password Reset

Hello,

Someone, hopefully you, has requested a password reset for your account at {base_url}.\n
"""
  if token:
    message += f"To reset your password, visit {base_url}user/reset-password?token={token}\n\n"
  else:
    message += "Unfortunately we couldn't find an account for you with this email address.\n\n"
  message += "Have a great day!\n"
  return message
