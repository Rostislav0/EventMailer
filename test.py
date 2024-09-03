import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

from dotenv import load_dotenv
import os
load_dotenv()

smtp_server = "vmail.iptel.by"
port = int("465")
email_sender = "soc@iptel.by"
emailData = "autoreports@iptel.by"
password_emailData = "#,53,RILLIn"
email_recipient_for_status_email = "test@iptel.by"

message_to_client = MIMEMultipart()

message_to_client['Subject'] = "Test"
message_to_client['From'] = email_sender
message_to_client['To'] = email_recipient_for_status_email
message_to_client['Date'] = formatdate(localtime=True)

html_file_path = './templates/test.html'

with open(html_file_path, 'r', encoding='utf-8') as file:
    body = file.read()

message_to_client.attach(MIMEText(body, "html"))

try:
    with smtplib.SMTP_SSL(smtp_server, port) as server:
        server.login(emailData, password_emailData)
        server.sendmail(email_sender, email_recipient_for_status_email, message_to_client.as_string())
    print("Email sent successfully.")
except Exception as e:
    print(f"An error occurred while sending email: {e}")
