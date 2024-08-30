import shutil
import smtplib
import sqlite3
import zipfile
from datetime import datetime
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.policy import default
import imaplib
import email
from email.header import decode_header
import sys
from user_event_manager import manage_user_event
import json

from dotenv import load_dotenv
import os

load_dotenv()

smtp_server = os.getenv("SMTP_SERVER")
port = int(os.getenv("SMTP_PORT"))
email_sender = os.getenv("EMAIL_SENDER")
password_sender = os.getenv("PASSWORD_EMAIL_SENDER")
email_recipients = ['test@iptel.by']
password_recipient = os.getenv("PASSWORD_EMAIL_RECIPIENT")
email_cert = os.getenv("EMAIL_CERT")
password_cert = os.getenv("PASSWORD_EMAIL_CERT")

def files_proccesor(path_to_results, body, subject):

    for user_id in os.listdir(path_to_results):
        file_names = os.listdir(f"{path_to_results}/{user_id}")
        file_names.remove('email.json')
        path_to_user = f"{path_to_results}/{user_id}"
        with open(f"{path_to_user}/email.json") as f:
            email_recipients = json.load(f)

        send_emails(body, subject, email_recipients, file_names, path_to_user)
        return file_names

def send_emails(body, subject, email_recipients, file_names, path_to_user):
    message_to_client = MIMEMultipart()

    message_to_client['Subject'] = subject
    message_to_client['From'] = email_sender
    message_to_client['To'] = ", ".join(email_recipients)

    message_to_client.attach(MIMEText(body, "html"))
    filenames = file_names

    for filename in filenames:
        with open(f"{path_to_user}/{filename}", 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={filename}')
            message_to_client.attach(part)

    try:
        with smtplib.SMTP_SSL(smtp_server, 465) as server:
            server.login(email_sender, password_sender)
            server.sendmail(email_sender, email_recipients, message_to_client.as_string())
            print("Email sent successfully.")
    except Exception as e:
        print(f"An error occurred while sending email: {e}")


def process_new_email():
    global mail, conn
    try:
        mail = imaplib.IMAP4_SSL(smtp_server)

        mail.login(email_cert, password_cert)

        mail.select("INBOX/exchange")

        status, messages = mail.search(None, "ALL")
        message_numbers = messages[0].split()
        latest_email_id = message_numbers[-1]

        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()

        date_tuple = email.utils.parsedate_tz(msg["Date"])
        local_date = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))

        email_date_for_db = local_date.strftime("%Y-%m-%d %H:%M:%S")
        email_date = local_date.strftime("%Y%m%d_%H%M%S")
        subject = msg["Subject"]
        conn = sqlite3.connect("emails.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM emails WHERE email_date = ?", (email_date_for_db,))
        result = cursor.fetchone()

        if result is None:
            try:

                process_attachments(msg, email_date)
                manage_user_event(email_date)

                #files_proccesor(path_to_results=f"results/{email_date}", body=body, subject=subject)
                cursor.execute("INSERT INTO emails (email_date, status) VALUES (?, ?)", (email_date_for_db, 1))
                conn.commit()
                print("Новое письмо успешно обработано")
                shutil.rmtree(f"original_data/{email_date}")
            except Exception as error:
                cursor.execute("INSERT INTO emails (email_date, status) VALUES (?, ?)", (email_date_for_db, 0))
                print(f"Новое письмо обработано c ошибками:\n{error}")
        else:
            print("Письмо уже обработано")



    except Exception as e:
        print(f"An error occurred during processing: {e}")
    finally:
        conn.close()
        mail.logout()




def process_attachments(msg, date_time):
    for part in msg.walk():
        if part.get_content_type() == "application/zip":
            filename = part.get_filename()
            if filename:
                new_filename = os.path.splitext(filename)[0]
                os.makedirs(f"original_data/{date_time}", exist_ok=True)
                with open(f"original_data/{date_time}/" + new_filename + ".zip", "wb") as f:
                    f.write(part.get_payload(decode=True))
                with zipfile.ZipFile(f"original_data/{date_time}/" + new_filename + ".zip", 'r') as zip_file:
                    zip_file.extractall(f"original_data/{date_time}/" + new_filename)
                os.remove(f"original_data/{date_time}/" + new_filename + ".zip")



process_new_email()
