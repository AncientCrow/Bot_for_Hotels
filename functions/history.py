import sqlite3
from datetime import datetime


class User:
    users = dict()

    def __init__(self, user_id, user_name):
        self.user_id = user_id
        self.user_name = user_name


def create_table() -> None:
    """
    Создает базу данных SQL если она не была создана ранее
    """

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users(
                user_id INT unique,
                user_name TEXT)
        """)
    cursor.execute("""CREATE TABLE IF NOT EXISTS history(
                    user_id INT,
                    date TEXT,
                    city TEXT,
                    hotels TEXT)
                    
            """)
    conn.commit()


def add_user(user: User) -> None:
    """
    Добавляет пользователя в таблицу при выполнения условия,
    если условие не выполняется, то ничего не происходит
    """

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    user_info = [user.user_id, user.user_name]
    conn.commit()
    cursor.execute(f"SELECT user_id FROM users WHERE user_id = {user.user_id}")
    data = cursor.fetchone()
    if data is None:
        cursor.execute("INSERT INTO users VALUES(?,?);", user_info)
        conn.commit()


def get_user(user_id: str) -> tuple:
    """
    Функция отвечает за получение id пользователя и будет использоваться в функции,
    отвечающей за выдачу истории запросов у бота

    Parameters:
    -------------
        user_id : str
            id пользователя, который будет искаться в базе данных SQL

    Returns:
    ---------
        record : tuple[int]
            кортеж состоящий из одного элемента - id пользователя.
            потребуется в выводе историй запросов пользователя
    """
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT user_id FROM history WHERE user_id = {user_id}")
    record = cursor.fetchone()
    return record


def add_search_history_city(user_id, hotels: list[dict]) -> None:
    """
    Функция отвечает за добавление истории запросов пользователя формата
     id Y-m-d-H:M, город, отели/
    """
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    date = datetime.today().strftime('%Y-%m-%d-%H:%M')
    user_info = [user_id, date]
    hotels_add = []
    for number, hotel in enumerate(hotels):
        if number == 0:
            user_info.append(hotel['locality'])
        hotels_add.append(hotel['name'])
    hotels_add = ", ".join(hotels_add)
    user_info.append(hotels_add)
    cursor.execute("INSERT INTO history VALUES(?,?,?,?);", user_info)
    conn.commit()
