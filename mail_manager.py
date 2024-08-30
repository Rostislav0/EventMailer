import smtplib
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.policy import default
import imaplib
import email
import sys

from dotenv import load_dotenv
import os
load_dotenv()

smtp_server = os.getenv("SMTP_SERVER")
port = int(os.getenv("SMTP_PORT"))
email_sender = os.getenv("EMAIL_SENDER")
password_sender = os.getenv("PASSWORD_EMAIL_SENDER")
email_recipient = os.getenv("EMAIL_RECIPIENT")
password_recipient = os.getenv("PASSWORD_EMAIL_RECIPIENT")


def send_email():
    message = MIMEMultipart()
    message['subject'] = 'Test'
    message['from'] = email_sender
    message['to'] = email_recipient

    body = 'Test message'
    message.attach(MIMEText(body, 'plain'))

    filenames = ['details.zip', 'event_list.zip']

    for filename in filenames:
        attachment = open(filename, 'rb')


        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={filename}')

        message.attach(part)


    server = smtplib.SMTP_SSL(smtp_server, 465)
    server.login(email_sender, password_sender)
    server.sendmail(email_sender, email_recipient, message.as_string())
    server.quit()


def receive_email():
    mail = imaplib.IMAP4_SSL(smtp_server)
    mail.login(email_recipient, password_recipient)
    mail.select('inbox')

    status, data = mail.search(None, "ALL")

    email_ids = data[0].split()
    for email_id in email_ids:
        status, data = mail.fetch(email_id, '(RFC822)')
        raw_email = data[0][1]


        msg = email.message_from_bytes(raw_email, policy=default)
        print(msg)
        subject = msg['subject']
        from_ = msg['from']
        to = msg['to']

        if msg.is_multipart():
            for part in msg.iter_parts():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()

        print(f"Subject: {subject}")
        print(f"From: {from_}")
        print(f"To: {to}")
        print(f"Body: {body}")

    mail.logout()

receive_email()