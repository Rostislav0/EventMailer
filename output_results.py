import json
import sys
import os
import pandas as pd

test_events = [
    {
        "archive": "details.zip",
        "type": "Sinkhole HTTP",
        "details": "Sinkhole HTTP.csv",
        "ips": [
            "80.94.229.3"
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
                result_df = pd.concat([result_df, filtered_df])
                result_df.to_csv(f"results/{id}/{event['details']}", index=False, encoding='utf-8-sig', sep=',')
            except:
                print(f"Не записались данные для пользователя: {id}\nСобытие:")
                print(event)

        with open(f"./results/{id}/event_list.json", "w", encoding="utf-8") as file:
            json.dump(user['events'], file, indent=4, ensure_ascii=False)
        with open(f"./results/{id}/email.json", "w", encoding="utf-8") as file:
            json.dump(user['emails'], file, indent=4, ensure_ascii=False)


#results = {501036: {'subnets': {'79.98.53.50/32'}, 'emails': ['1381115@gmail.com'], 'events': [{'archive': 'details.zip', 'type': 'Accessible MySQL', 'details': 'Accessible MySQL.csv', 'ips': ['79.98.53.50'], 'description': 'Узлы сети, на которых доступен экземпляр MySQL на порте 3306/TCP.\r\nМаловероятно, что вам нужна MySQL, доступная из Интернета и, следовательно, дополнительная внешняя поверхность атаки.\r\nВремя в UTC+0.', 'recommendation': 'Обязательно использовать аутентификацию на сервере.\r\nОграничить доступ из сети Интернет, если в нем нет обоснованной необходимости.\r\nПроверить на наличие ВПО и/или следов компрометации сервера, а также провести поиск и устранение уязвимостей.'}, {'archive': 'details.zip', 'type': 'Accessible SSH', 'details': 'Accessible SSH.csv', 'ips': ['79.98.53.50'], 'description': 'Это информационное уведомление для учета в работе об узлах сети, на которых запущена служба Secure Shell (SSH) и доступна в Интернете.\r\nНаправляется для контроля и учета доступных в сети Интернет оборудования и сервисов, а так же напоминания о возможных рисках.\r\nВАЖНО. Оценка состояния уязвимости устройств не производится.\r\nВремя в UTC+0.', 'recommendation': 'Рекомендуется проверить указанную информацию и при необходимости принять соответствующие меры.\r\nЧасто могут быть использованы следующие варианты:\r\n1. Закрыть порт, если больше нет необходимости его использования.\r\n2. Если сервис нелегитимный, то следует максимально оперативно ограничить к нему доступ и проверить устройство на наличие ВПО и/или следов компрометации, а также провести поиск и устранение уязвимостей.\r\n3. Ограничить прямой доступ к ресурсу из сети Интернет, если в нем нет обоснованной необходимости.\r\n4. Использовать VPN или убедиться что приняты все необходимые/доступные меры по обеспечению безопасного доступа (например, мониторинг доступа, настройка безопасного подключения для уменьшения вероятности проведения успешной атаки: использование ключа и сложного пароля, смена стандартного порта, запрет подключения root, ограничение перечня разрешенных пользователей и IP).\r\n5. Регулярные обновления ПО.'}]}}
#get_result_files(results)

original_df = pd.read_csv(f'details/{test_events[0]['details']}', encoding='utf-8-sig', delimiter=';')
result_df = pd.DataFrame()
try:
    filtered_df = original_df[original_df['ip'].isin(test_events[0]['ips'])]
    result_df = pd.concat([result_df, filtered_df])
    #result_df.to_csv(f"results/{id}/{test_events[0]['details']}", index=False, encoding='utf-8-sig', sep=',')
except:
    print(f"Не записались данные для пользователя: {503191}\nСобытие:")
    print(test_events[0])