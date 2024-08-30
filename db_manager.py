import sqlite3

# Подключение к базе данных
conn = sqlite3.connect('emails.db')
cursor = conn.cursor()

# Удаление всех записей из таблицы
cursor.execute("DELETE FROM emails")

# Сохранение изменений
conn.commit()

# Закрытие соединения
conn.close()