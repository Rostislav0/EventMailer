import shutil
import smtplib
import sqlite3
import sys
import zipfile
from datetime import datetime
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.header import decode_header
import imaplib
import email
from email.utils import formatdate
from user_event_manager import manage_user_event
import json
from dotenv import load_dotenv
import os

load_dotenv()

smtp_server = os.getenv("SMTP_SERVER")
port = int(os.getenv("SMTP_PORT"))
email_sender = os.getenv("EMAIL_SENDER")
password_sender = os.getenv("PASSWORD_EMAIL_SENDER")
email_recipient = os.getenv("EMAIL_RECIPIENT")


def decode_mime_header(header):
    decoded_header = decode_header(header)
    return ''.join(
        str(part.decode(encoding if encoding else 'utf-8')) if isinstance(part, bytes) else part
        for part, encoding in decoded_header
    )

def files_processor(path_to_results, path_to_problem_users, body, subject):
    users_without_email_addresses = []

    for user_id in os.listdir(path_to_results):
        path_to_user = f"{path_to_results}/{user_id}"
        with open(f"{path_to_user}/email.json") as f:
            email_recipients = json.load(f)

        if not email_recipients:
            os.makedirs(path_to_problem_users, exist_ok=True)
            users_without_email_addresses.append(user_id)
            shutil.copytree(path_to_user, f"{path_to_problem_users}/{user_id}", dirs_exist_ok=True)
            continue
        file_names = os.listdir(f"{path_to_results}/{user_id}")
        file_names.remove('email.json')

        send_emails(body, subject, email_recipients, file_names, path_to_user)
    return users_without_email_addresses


def send_status_email(id_status, subject='',path_to_problem_users='', users_without_email_addresses='', error=''):
    statuses = {0: f'Ошибка в парсинге письма: {error}', 1: f'Письмо успешно обработано',
                2: f'Письмо уже обработано', 3: f'Ошибка в получении архивов из письма: {error}',
                4: f'Ошибка в обработке данных пользователей: {error}', 5: f'Ошибка в отправке писем: {error}'}

    status_message = MIMEMultipart()

    status_message['Subject'] = subject if subject else "Невозможно обработать письмо!"
    status_message['From'] = email_sender
    status_message['To'] = email_recipient
    status_message['Date'] = formatdate(localtime=True)
    body = f"""{f" - Количество пользователей без адреса: {len(users_without_email_addresses)}.\n"
    f"Список account id: {', '.join(users_without_email_addresses)}" if users_without_email_addresses
                                                                    else ''}
Письмо обработано с результатом: "{statuses[id_status]}"    
                """
    status_message.attach(MIMEText(body, 'plain'))

    if id_status == 1 and os.path.isdir(path_to_problem_users):
        zip_file_name = 'users_without_emails'
        shutil.make_archive(zip_file_name, 'zip', path_to_problem_users)

        with open(f"{zip_file_name}.zip", 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={zip_file_name}.zip')
            status_message.attach(part)

    try:
        with smtplib.SMTP_SSL(smtp_server, port) as server:
            server.login(email_sender, password_sender)
            server.sendmail(email_sender, email_recipient, status_message.as_string())
        print("Status email sent successfully.")
    except Exception as e:
        print(f"An error occurred while sending status email: {e}")
    #shutil.rmtree(path_to_problem_users, ignore_errors=True)
    sys.exit()


def send_emails(body, subject, email_recipients, file_names, path_to_user):
    message_to_client = MIMEMultipart()

    message_to_client['Subject'] = subject
    message_to_client['From'] = email_sender
    message_to_client['To'] = ", ".join(email_recipients)
    message_to_client['Date'] = formatdate(localtime=True)

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
        with smtplib.SMTP_SSL(smtp_server, port) as server:
            server.login(email_sender, password_sender)
            server.sendmail(email_sender, email_recipients, message_to_client.as_string())
        print("Email sent successfully.")
    except Exception as e:
        print(f"An error occurred while sending email: {e}")


def process_emails(date='', account_ids=None):
    try:
        mail = imaplib.IMAP4_SSL(smtp_server)

        mail.login(email_sender, password_sender)

        mail.select("INBOX")
        if date:
            date_object = datetime.strptime(date, "%d.%m.%Y")  # Преобразуем строку в объект datetime
            formatted_date = date_object.strftime("%d-%b-%Y")
            search_criteria = f'(ON "{formatted_date}")'
            status, messages = mail.search(None, search_criteria)
            email_ids = messages[0].split()
            search_subject = "Оповещение о событиях безопасности"
            for e_id in email_ids:
                status, msg_data = mail.fetch(e_id, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])
                subject_valid = decode_mime_header(msg['Subject'])

                if search_subject in subject_valid:
                    process_a_email(mail, msg, account_ids, check_db=0)
        else:  # Get last message without filters
            status, messages = mail.search(None, "ALL")
            message_numbers = messages[0].split()
            email_id = message_numbers[-1]

            status, msg_data = mail.fetch(email_id, "(RFC822)")

            msg = email.message_from_bytes(msg_data[0][1])
            process_a_email(mail, msg)
    except Exception as error:
        print(f'Ошибка в получении писем: {error}')


def process_a_email(mail, msg, account_ids=None, check_db=1):
    global conn
    try:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()
        mail.logout()
        date_tuple = email.utils.parsedate_tz(msg["Date"])
        local_date = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))

        email_date_for_db = local_date.strftime("%Y-%m-%d %H:%M:%S")
        email_date = local_date.strftime("%Y%m%d_%H%M%S")
        subject = msg["Subject"]
        conn = sqlite3.connect("emails.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM emails WHERE email_date = ?", (email_date_for_db,))
        result = cursor.fetchone()
        path_to_results = f"./results/{email_date}"
        path_to_problem_users = f"./problem_users/{email_date}"
        if (result is None) or check_db == 0:

            os.makedirs(path_to_results, exist_ok=True)

            try:
                process_attachments(msg, email_date)
            except Exception as error:
                # print(f"Ошибка в получении архивов из письма:\n{error}")
                cursor.execute("INSERT INTO emails (email_date, status) VALUES (?, ?)", (email_date_for_db, 3))
                send_status_email(subject=subject, id_status=3, path_to_problem_users=path_to_problem_users,
                                  error=error)
            try:
                manage_user_event(email_date, account_ids)
            except Exception as error:
                # print(f"Ошибка в обработке данных пользователей:\n{error}")
                cursor.execute("INSERT INTO emails (email_date, status) VALUES (?, ?)", (email_date_for_db, 4))
                send_status_email(subject=subject, id_status=4, path_to_problem_users=path_to_problem_users,
                                  error=error)

            try:
                pass
                #users_without_email_addresses = files_processor(path_to_results=path_to_results,
                #                                                path_to_problem_users=path_to_problem_users, body=body,
                #                                                subject=subject)
            except Exception as error:
                # print(f"Ошибка в отправке писем:\n{error}")
                cursor.execute("INSERT INTO emails (email_date, status) VALUES (?, ?)", (email_date_for_db, 5))
                send_status_email(subject=subject, id_status=5, path_to_problem_users=path_to_problem_users, error=error)

            cursor.execute("INSERT INTO emails (email_date, status, no_mails) VALUES (?, ?, ?)",
                           (email_date_for_db, 1, len(users_without_email_addresses)))
            conn.commit()

            shutil.rmtree(f"original_data/{email_date}", ignore_errors=True)

            shutil.rmtree(path_to_results, ignore_errors=True)
            # print("Новое письмо успешно обработано")
            send_status_email(subject=subject, users_without_email_addresses=users_without_email_addresses,
                              id_status=1, path_to_problem_users=path_to_problem_users)


        else:
            # print("Письмо уже обработано")
            send_status_email(subject=subject, id_status=2, path_to_problem_users=path_to_problem_users)
    except Exception as error:
        # print(f"Ошибка в парсинге письма: {e}")
        send_status_email(id_status=0, error=error)
    finally:
        conn.close()


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


process_emails(date="30.08.2024", account_ids=[4555])  # date="30.08.2024", account_ids=[4555]
