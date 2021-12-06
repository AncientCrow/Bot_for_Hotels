import sqlite3
from datetime import datetime
from typing import List


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
                    command TEXT,
                    date TEXT,
                    city TEXT,
                    hotels TEXT)  
            """)
    conn.commit()


def add_user(user: User) -> None:
    """
    Добавляет пользователя в таблицу при выполнения условия,
    если условие не выполняется, то ничего не происходит

    Parameters:
    -------------
        user : User
            класс пользователя, хранит в себе id и имя пользователя
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


def add_search_history_city(user_id: int, command: str, hotels: List[dict]) -> None:
    """
    Функция отвечает за добавление истории запросов пользователя формата
    id Y-m-d-H:M, город, отели/

     Parameters:
     -------------
        user_id : int
            id пользователя для добавления в базу данных

        command : str
            команда, которая была использована пользователем

        hotels : list[dict]
            список содержащий внутри себя словарь с данными об отелях
    """

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    date = datetime.today().strftime('%Y-%m-%d-%H:%M')
    user_info = [user_id, command, date]
    hotels_add = []
    for number, hotel in enumerate(hotels):
        if number == 0:
            user_info.append(hotel['locality'])
        hotels_add.append(hotel['name'])
    hotels_add = ", ".join(hotels_add)
    user_info.append(hotels_add)
    cursor.execute("INSERT INTO history VALUES(?,?,?,?,?);", user_info)
    conn.commit()


def get_history(user_id: int) -> tuple:
    """
    Функция принимающая id пользователя и выводящая 3 последних запроса пользователя
    если в базе данных нет информации о запросах пользователя то возвращается false,
    если в базе меньше 3 запросов пользователя то будет произведён вывод меньшего числа запросов

    Parameters:
    -------------
        user_id : int
            id пользователя для поиска в базе данных
    """

    try:
        connect = sqlite3.connect('database.db')
        with connect:
            cursor = connect.cursor()
            sql_text = "SELECT * FROM history WHERE user_id = ?"
            cursor.execute(sql_text, (user_id,))
            rows = cursor.fetchall()

            if len(rows) == 0:
                raise ValueError
            rows = rows[::-1]

            message = ""
            for row in rows[:3]:
                time = row[2]
                command = row[1]
                city = row[3]
                hotels = row[4].split(", ")
                hotel_message = ""
                history_count = len(hotels)
                for hotel in hotels:
                    hotel_message += f"{hotel}\n"

                message += f"\nВремя запроса: {time}\nКоманда: {command}\nГород: {city}\nОтели:\n{hotel_message}\n"
        return message, history_count
    except ValueError:
        return False, 0
