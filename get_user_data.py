import mysql.connector
import os
import re
from dotenv import load_dotenv
from form_query import form_sql_query_minsk, form_sql_query_gomel
load_dotenv()

user = os.getenv('USER')
password = os.getenv("PASSWORD")
host_minsk = os.getenv("HOST_minsk")
host_gomel = os.getenv("HOST_gomel")
db = os.getenv("DB")


def division_data_by_aid(ip_addresses):
    cnx_minsk = mysql.connector.connect(user=user, password=password,
                                        host=host_minsk,
                                        database=db)
    cnx_gomel = mysql.connector.connect(user=user, password=password,
                                        host=host_gomel,
                                        database=db)
    cursor_minsk = cnx_minsk.cursor()
    cursor_gomel = cnx_gomel.cursor()

    cursor_minsk.execute(form_sql_query_minsk(ip_addresses))
    cursor_gomel.execute(form_sql_query_gomel(ip_addresses))

    results_minsk = cursor_minsk.fetchall()
    results_gomel = cursor_gomel.fetchall()

    email_and_ips = {}

    for id, full_name, email, ip in results_minsk:
        if id in email_and_ips.keys():
            email_and_ips[id]['subnets'].update({ip})
            if email:
                email_and_ips[id]['emails'].update(re.split(r'[ ,]+', email.strip()) if email else [])
        else:
            email_and_ips[id] = {
                'subnets': {ip},
                'emails': set(re.split(r'[ ,]+', email.strip()) if email else [])
            }

    for id, full_name, email, ip in results_gomel:
        if id in email_and_ips.keys():
            email_and_ips[id]['subnets'].update({ip})
            if email:
                email_and_ips[id]['emails'].update(re.split(r'[ ,]+', email.strip()) if email else [])
        else:
            email_and_ips[id] = {
                'subnets': {ip},
                'emails': set(re.split(r'[ ,]+', email.strip()) if email else [])
            }

    cursor_minsk.close()
    cursor_gomel.close()
    cnx_minsk.close()
    cnx_gomel.close()
    return email_and_ips
