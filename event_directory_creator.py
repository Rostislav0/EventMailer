import json
import os
import zipfile

import pandas as pd
from colorama import Fore, Style
ERROR_string = Fore.RED + "***ERROR***" + Style.RESET_ALL
WARNING_string = Fore.YELLOW + "***WARNING***" + Style.RESET_ALL


class EventDirCreator():
    def __init__(self, path_to_result_dir, path_to_original_dir, results):
        self.path_to_result_dir = path_to_result_dir
        self.results = results
        self.path_to_original_dir = path_to_original_dir

    def zip_files_exclude_email(self, path):
        with zipfile.ZipFile(f"{path}/events.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file != "email.json" and file != 'events.zip':
                        file_path = f"{path}/{file}"
                        zipf.write(file_path, file)
        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            if os.path.isfile(file_path) and filename not in ['events.zip', 'email.json']:
                os.remove(file_path)

    def create_event_directories(self):
        """
        Create directories for each user and event, filter data based on IP addresses,
        and save the results in CSV files.

        Parameters:
        results (dict): Dictionary containing user IDs and their corresponding event details.
        """
        # Create the main results directory if it doesn't exist

        for id, user in self.results.items():
            self.create_user_directory(id)
            self.process_user_events(id, user)
            self.zip_files_exclude_email(path=f"{self.path_to_result_dir}/{id}")

    def create_user_directory(self, user_id):
        """
        Create a directory for a user.

        Parameters:
        user_id (str): The ID of the user.
        """
        os.makedirs(f"{self.path_to_result_dir}/{user_id}", exist_ok=True)

    def process_user_events(self, user_id, user):
        """
        Process events for a user, filter data based on IP addresses,
        and save the results in CSV files.

        Parameters:
        user_id (str): The ID of the user.
        user (dict): Dictionary containing user details and events.
        """
        for event in user['events']:
            self.process_event(user_id, event)
        self.save_user_data(user_id, user)

    def process_event(self, user_id, event):
        """
        Process a single event, filter data based on IP addresses,
        and save the results in a CSV file.

        Parameters:
        user_id (str): The ID of the user.
        event (dict): Dictionary containing event details and IP addresses.
        """
        original_df = pd.read_csv(f'{self.path_to_original_dir}/details/{event["details"]}', encoding='utf-8-sig', delimiter=';')
        result_df = pd.DataFrame()
        try:
            filtered_df = original_df[original_df['ip'].isin(event['ips'])]
            self.check_missing_ips(filtered_df, event, user_id)
            result_df = pd.concat([result_df, filtered_df])
            self.save_dataframe_to_csv(result_df, user_id, event['details'])
        except KeyError:
            self.handle_missing_ip_column(original_df, event, user_id, result_df)

    @staticmethod
    def check_missing_ips(filtered_df, event, user_id):
        """
        Check if any IP addresses are missing in the filtered DataFrame.

        Parameters:
        filtered_df (DataFrame): The filtered DataFrame.
        event (dict): Dictionary containing event details and IP addresses.
        user_id (str):
        """
        if set(filtered_df['ip'].unique()) != set(event['ips']):
            print(WARNING_string + f"В файле {Style.BRIGHT}{event['details']}{Style.RESET_ALL} не найдены все "
                                   f"ip адреса в поле \033[3mip\033[0m для текущего event. Поверить запись в "
                                   f"директории пользователя {Style.BRIGHT}{user_id}{Style.RESET_ALL}.")

    def save_dataframe_to_csv(self, df, user_id, filename):
        """
        Save a DataFrame to a CSV file.

        Parameters:
        df (DataFrame): The DataFrame to save.
        user_id (str): The ID of the user.
        filename (str): The name of the file to save the DataFrame to.
        """
        df.to_csv(f"{self.path_to_result_dir}/{user_id}/{filename}", index=False, encoding='utf-8-sig', sep=',')

    def handle_missing_ip_column(self, original_df, event, user_id, result_df):
        """
        Handle the case where the 'ip' column is not found in the DataFrame.

        Parameters:
        original_df (DataFrame): The original DataFrame.
        event (dict): Dictionary containing event details and IP addresses.
        user_id (str): The ID of the user.
        result_df (DataFrame): The result DataFrame to concatenate filtered data to.
        """
        print(WARNING_string + f"В файле {Style.BRIGHT}{event['details']}{Style.RESET_ALL} не найдена колонка "
                               f"\033[3mip\033[0m. Поверить запись в директории пользователя {Style.BRIGHT}{user_id}"
                               f"{Style.RESET_ALL}.")
        filtered_df = original_df[original_df.apply(
            lambda row: row.astype(str).apply(lambda x: any(text in x for text in event['ips'])).any(),
            axis=1)]
        if filtered_df.empty:
            print(ERROR_string + f"Среди данных в {Style.BRIGHT}{event['details']}{Style.RESET_ALL} не "
                                 f"найдены совпадения адресов из event. Пользователь {Style.BRIGHT}{user_id}"
                                 f"{Style.RESET_ALL}.")
        result_df = pd.concat([result_df, filtered_df])
        self.save_dataframe_to_csv(result_df, user_id, event['details'])

    def save_user_data(self, user_id, user):
        """
        Save user data to JSON files.

        Parameters:
        user_id (str): The ID of the user.
        user (dict): Dictionary containing user details and events.
        """
        with open(f"{self.path_to_result_dir}/{user_id}/event_list.json", "w", encoding="utf-8") as file:
            json.dump(user['events'], file, indent=4, ensure_ascii=False)
        with open(f"{self.path_to_result_dir}/{user_id}/email.json", "w", encoding="utf-8") as file:
            json.dump(user['emails'], file, indent=4, ensure_ascii=False)
