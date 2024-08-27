import copy
import json
import zipfile
from get_user_data import division_data_by_aid
from output_results import get_result_files
import ipaddress


def unzipping_file(zip_file):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(f'./{zip_file.replace('.zip', '')}')


def check_ip_in_subnets(ip, subnets):
    ip_obj = ipaddress.ip_address(ip)
    for subnet in subnets:
        if ip_obj in ipaddress.ip_network(subnet):
            return True
    return False


def scraping_users():

    unzipping_file('details.zip')
    unzipping_file('event_list.zip')

    with open("event_list/event_list.txt") as f:
        templates = json.load(f)

    all_ips = set()
    for event in templates['events']:
        all_ips.update(event['ips'])

    separated_users = division_data_by_aid(all_ips)

    for event in templates['events']:
        for id in separated_users:
            user_ips = set()
            if not 'events' in separated_users[id]:
                separated_users[id]['events'] = []

            for ip in event['ips']:

                if check_ip_in_subnets(ip, separated_users[id]['subnets']):
                    user_ips.update({ip})

            if user_ips:
                temp_event = copy.copy(event)
                temp_event['ips'] = list(user_ips)
                separated_users[id]['events'].append(temp_event)

    get_result_files(separated_users)


scraping_users()
