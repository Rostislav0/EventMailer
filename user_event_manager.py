import copy
import json
import os
import zipfile
from user_events_collector import fetch_user_event_data
from event_directory_creator import EventDirCreator
import ipaddress


def check_ip_in_subnets(ip, subnets):
    """
    Checks if the given IP address belongs to any of the provided subnets.

    Parameters:
    ip (str): The IP address to check.
    subnets (list): A list of subnets to check against.

    Returns:
    bool: True if the IP address is in any of the subnets, False otherwise.
    """
    ip_obj = ipaddress.ip_address(ip)
    for subnet in subnets:
        if ip_obj in ipaddress.ip_network(subnet):
            return True
    return False


def load_event_templates(file_path):
    """
    Loads event templates from a specified file.

    Parameters:
    file_path (str): The path to the file containing event templates.

    Returns:
    dict: The loaded event templates as a dictionary.
    """
    with open(file_path) as f:
        return json.load(f)


def collect_all_ips(events):
    """
    Collects all unique IP addresses from a list of events.

    Parameters:
    events (list): A list of event dictionaries, each containing an 'ips' key.

    Returns:
    set: A set of all unique IP addresses.
    """
    all_ips = set()
    for event in events:
        all_ips.update(event['ips'])
    return all_ips


def process_user_events(events, separated_users):
    """
    Processes user events and associates them with the corresponding users.

    Parameters:
    events (list): A list of event dictionaries.
    separated_users (dict): A dictionary of users, each containing 'emails' and 'subnets'.

    Modifies:
    separated_users (dict): Adds processed events to each user.
    """
    for event in events:
        for id in separated_users:
            # Convert emails to a list if not already done
            separated_users[id]['emails'] = list(separated_users[id]['emails'])
            user_ips = set()
            if not 'events' in separated_users[id]:
                separated_users[id]['events'] = []

            # Check if event IPs belong to user's subnets
            for ip in event['ips']:
                if check_ip_in_subnets(ip, separated_users[id]['subnets']):
                    user_ips.update({ip})

            # If there are matching IPs, add the event to the user's events
            if user_ips:
                temp_event = copy.copy(event)
                temp_event['ips'] = list(user_ips)
                separated_users[id]['events'].append(temp_event)


def manage_user_event(date_time):

    os.makedirs(f"./results", exist_ok=True)
    os.makedirs(f"./results/{date_time}", exist_ok=True)
    path_to_result_dir = f"./results/{date_time}"
    path_to_original_dir = f"./original_data/{date_time}"
    templates = load_event_templates(f"original_data/{date_time}/event_list/event_list.txt")

    all_ips = collect_all_ips(templates['events'])
    separated_users = fetch_user_event_data(all_ips)

    process_user_events(templates['events'], separated_users)
    EventDirCreator(path_to_result_dir, path_to_original_dir, separated_users).create_event_directories()
