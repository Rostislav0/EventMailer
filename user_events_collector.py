import mysql.connector
import os
import re
from dotenv import load_dotenv
from sql_generator import generate_sql_query_minsk, generate_sql_query_gomel
load_dotenv()

user = os.getenv('USER')
password = os.getenv("PASSWORD")
host_minsk = os.getenv("HOST_minsk")
host_gomel = os.getenv("HOST_gomel")
db = os.getenv("DB")


def update_user_data(results, users_data):
    """
    Update the users_data dictionary with email and IP information from the query results.

    Args:
        results (list): List of tuples containing user data from the database.
        users_data (dict): Dictionary to store user emails and IP addresses.
    """
    for id, full_name, email, ip in results:
        if id in users_data.keys():
            users_data[id]['subnets'].update({ip})
            if email:
                users_data[id]['emails'].update(re.split(r'[ ,]+', email.strip()) if email else [])
        else:
            users_data[id] = {
                'subnets': {ip},
                'emails': set(re.split(r'[ ,]+', email.strip()) if email else [])
            }


def fetch_user_event_data(ip_addresses):
    """
    Fetch user event data from databases in Minsk and Gomel based on IP addresses.

    Args:
        ip_addresses (set): List of IP addresses to query.

    Returns:
        dict: Dictionary containing user emails and IP addresses.
    """
    cnx_minsk = mysql.connector.connect(user=user, password=password,
                                        host=host_minsk,
                                        database=db)
    cnx_gomel = mysql.connector.connect(user=user, password=password,
                                        host=host_gomel,
                                        database=db)
    cursor_minsk = cnx_minsk.cursor()
    cursor_gomel = cnx_gomel.cursor()

    cursor_minsk.execute(generate_sql_query_minsk(ip_addresses))
    cursor_gomel.execute(generate_sql_query_gomel(ip_addresses))

    results_minsk = cursor_minsk.fetchall()
    results_gomel = cursor_gomel.fetchall()

    cursor_minsk.close()
    cursor_gomel.close()
    cnx_minsk.close()
    cnx_gomel.close()

    users_data = {}

    update_user_data(results_minsk, users_data)
    update_user_data(results_gomel, users_data)

    return users_data
