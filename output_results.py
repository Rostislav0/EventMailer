import json
import sys
import os
import pandas as pd
from colorama import init, Fore, Style
ERROR_string = Fore.RED + "***ERROR***" + Style.RESET_ALL
WARNING_string = Fore.YELLOW + "***WARNING***" + Style.RESET_ALL
test_events = [
    {
        "archive": "details.zip",
        "type": "Sinkhole HTTP",
        "details": "Sinkhole HTTP.csv",
        "ips": [
            "80.94.229.3",
            "80.94.223.3"
        ],
        "description": "Узлы сети, которые используются для выхода в Интернет скомпрометированным(и) хостом(хостами) и которые имели соединения с HTTP-Sinkhole.\r\nSinkholing/Синкхолинг — это метод, при котором ресурс, используемый злоумышленниками для управления вредоносным ПО, перехватывается и анализируются для выявления соединившихся зараженных устройств.\r\nТехнические подробности во вложении.\r\nВремя в UTC+0.",
        "recommendation": "Просим связаться с нами, если указанные действия проводили Вы (Ваша организация), если нет, то необходимо оперативно провести проверку информации и принять соответствующие меры для прекращения вредоносной активности.\r\nЧасто могут быть использованы следующие варианты:\r\n1. Проверка на наличие ВПО и/или следов компрометации сервера/инфраструктуры.\r\n2. Проведение поиска и устранения уязвимостей.\r\n3. Регулярные обновления ПО."
    }
]
def get_result_files(results):
    os.makedirs(f"./results", exist_ok=True)
    for id, user in results.items():
        os.makedirs(f"./results/{id}", exist_ok=True)
        for event in user['events']:
            original_df = pd.read_csv(f'details/{event['details']}', encoding='utf-8-sig', delimiter=';')
            result_df = pd.DataFrame()
            try:
                filtered_df = original_df[original_df['ip'].isin(event['ips'])]

                if set(filtered_df['ip'].unique()) != set(event['ips']):
                    print(
                        WARNING_string + f"В файле {Style.BRIGHT}{event['details']}{Style.RESET_ALL} не найдены все ip адреса в поле \033[3mip\033[0m для текущего event. Поверить запись в директории пользователя {Style.BRIGHT}{id}{Style.RESET_ALL}.")
                result_df = pd.concat([result_df, filtered_df])
                result_df.to_csv(f"results/{id}/{event['details']}", index=False, encoding='utf-8-sig', sep=',')
            except:
                print(WARNING_string + f"В файле {Style.BRIGHT}{event['details']}{Style.RESET_ALL} не найдена колонка \033[3mip\033[0m. Поверить запись в директории пользователя {Style.BRIGHT}{id}{Style.RESET_ALL}.")
                filtered_df = original_df[original_df.apply(
                    lambda row: row.astype(str).apply(lambda x: any(text in x for text in event['ips'])).any(),
                    axis=1)]
                if filtered_df.empty:
                    print(ERROR_string + f"Среди данных в {Style.BRIGHT}{event['details']}{Style.RESET_ALL} не найдены совпадения адресов из event. Пользователь {Style.BRIGHT}{id}{Style.RESET_ALL}.")
                result_df = pd.concat([result_df, filtered_df])
                result_df.to_csv(f"results/{id}/{event['details']}", index=False, encoding='utf-8-sig',
                                 sep=',')

        with open(f"./results/{id}/event_list.json", "w", encoding="utf-8") as file:
            json.dump(user['events'], file, indent=4, ensure_ascii=False)
        with open(f"./results/{id}/email.json", "w", encoding="utf-8") as file:
            json.dump(user['emails'], file, indent=4, ensure_ascii=False)
