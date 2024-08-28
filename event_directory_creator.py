import json
import sys
import os
import pandas as pd
from colorama import init, Fore, Style
ERROR_string = Fore.RED + "***ERROR***" + Style.RESET_ALL
WARNING_string = Fore.YELLOW + "***WARNING***" + Style.RESET_ALL


def create_event_directories(results):
    """
    Create directories for each user and event, filter data based on IP addresses,
    and save the results in CSV files.

    Parameters:
    results (dict): Dictionary containing user IDs and their corresponding event details.
    """
    # Create the main results directory if it doesn't exist
    os.makedirs(f"./results", exist_ok=True)

    for id, user in results.items():
        create_user_directory(id)
        process_user_events(id, user)


def create_user_directory(user_id):
    """
    Create a directory for a user.

    Parameters:
    user_id (str): The ID of the user.
    """
    os.makedirs(f"./results/{user_id}", exist_ok=True)


def process_user_events(user_id, user):
    """
    Process events for a user, filter data based on IP addresses,
    and save the results in CSV files.

    Parameters:
    user_id (str): The ID of the user.
    user (dict): Dictionary containing user details and events.
    """
    for event in user['events']:
        process_event(user_id, event)
    save_user_data(user_id, user)


def process_event(user_id, event):
    """
    Process a single event, filter data based on IP addresses,
    and save the results in a CSV file.

    Parameters:
    user_id (str): The ID of the user.
    event (dict): Dictionary containing event details and IP addresses.
    """
    original_df = pd.read_csv(f'details/{event["details"]}', encoding='utf-8-sig', delimiter=';')
    result_df = pd.DataFrame()
    try:
        filtered_df = filter_dataframe_by_ip(original_df, event['ips'])
        check_missing_ips(filtered_df, event)
        result_df = pd.concat([result_df, filtered_df])
        save_dataframe_to_csv(result_df, user_id, event['details'])
    except KeyError:
        handle_missing_ip_column(original_df, event, user_id, result_df)


def filter_dataframe_by_ip(df, ips):
    """
    Filter a DataFrame based on a list of IP addresses.

    Parameters:
    df (DataFrame): The original DataFrame.
    ips (list): List of IP addresses to filter by.

    Returns:
    DataFrame: The filtered DataFrame.
    """
    return df[df['ip'].isin(ips)]


def check_missing_ips(filtered_df, event):
    """
    Check if any IP addresses are missing in the filtered DataFrame.

    Parameters:
    filtered_df (DataFrame): The filtered DataFrame.
    event (dict): Dictionary containing event details and IP addresses.
    """
    if set(filtered_df['ip'].unique()) != set(event['ips']):
        print(WARNING_string + f"В файле {Style.BRIGHT}{event['details']}{Style.RESET_ALL} не найдены все "
                               f"ip адреса в поле \033[3mip\033[0m для текущего event. Поверить запись в "
                               f"директории пользователя {Style.BRIGHT}{user_id}{Style.RESET_ALL}.")


def save_dataframe_to_csv(df, user_id, filename):
    """
    Save a DataFrame to a CSV file.

    Parameters:
    df (DataFrame): The DataFrame to save.
    user_id (str): The ID of the user.
    filename (str): The name of the file to save the DataFrame to.
    """
    df.to_csv(f"results/{user_id}/{filename}", index=False, encoding='utf-8-sig', sep=',')


def handle_missing_ip_column(original_df, event, user_id, result_df):
    """
    Handle the case where the 'ip' column is not found in the DataFrame.

    Parameters:
    original_df (DataFrame): The original DataFrame.
    event (dict): Dictionary containing event details and IP addresses.
    user_id (str): The ID of the user.
    result_df (DataFrame): The result DataFrame to concatenate filtered data to.
    """
    print(WARNING_string + f"В файле {Style.BRIGHT}{event['details']}{Style.RESET_ALL} не найдена колонка "
                           f"\033[3mip\033[0m. Поверить запись в директории пользователя {Style.BRIGHT}{user_id}{Style.RESET_ALL}.")
    filtered_df = original_df[original_df.apply(
        lambda row: row.astype(str).apply(lambda x: any(text in x for text in event['ips'])).any(),
        axis=1)]
    if filtered_df.empty:
        print(ERROR_string + f"Среди данных в {Style.BRIGHT}{event['details']}{Style.RESET_ALL} не "
                             f"найдены совпадения адресов из event. Пользователь {Style.BRIGHT}{user_id}{Style.RESET_ALL}.")
    result_df = pd.concat([result_df, filtered_df])
    save_dataframe_to_csv(result_df, user_id, event['details'])


def save_user_data(user_id, user):
    """
    Save user data to JSON files.

    Parameters:
    user_id (str): The ID of the user.
    user (dict): Dictionary containing user details and events.
    """
    with open(f"./results/{user_id}/event_list.json", "w", encoding="utf-8") as file:
        json.dump(user['events'], file, indent=4, ensure_ascii=False)
    with open(f"./results/{user_id}/email.json", "w", encoding="utf-8") as file:
        json.dump(user['emails'], file, indent=4, ensure_ascii=False)
