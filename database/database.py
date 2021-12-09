import sqlite3
from datetime import datetime
from typing import List, Tuple


def create_table() -> None:
    """
    Создает базу данных SQL если она не была создана ранее
    """

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users(
                user_id INT unique,
                user_name TEXT,
                date_in TEXT,
                date_out TEXT)
        """)
    cursor.execute("""CREATE TABLE IF NOT EXISTS history(
                    user_id INT,
                    command TEXT,
                    date TEXT,
                    city TEXT,
                    hotels TEXT)  
            """)
    cursor.execute("""CREATE TABLE IF NOT EXISTS parameters(
                        user_id INT,
                        hotel_count INT,
                        photo_answer TEXT,
                        photo_count INT)
            """)
    conn.commit()


def add_user(user_id, user_name) -> None:
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
    user_info = [user_id, user_name, None, None]
    conn.commit()
    cursor.execute(f"SELECT user_id FROM users WHERE user_id = {user_id}")
    data = cursor.fetchone()
    if data is None:
        cursor.execute("INSERT INTO users VALUES(?,?,?,?);", user_info)
        conn.commit()


def get_dates(user_id: int) -> Tuple[str, str]:
    """
    Функция предназначена для получения кортежа с датами въезда и выезда из отеля

    Parameters:
    -------------
        user_id : int
            id пользователя

    """
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT date_in, date_out FROM users WHERE user_id = {user_id}")
    result = cursor.fetchone()
    return result


def update_dates(user_id: int, date_in: str = None, date_out: str = None) -> None:
    """
    Функция отвечает за принятие id пользователя, а также даты въезда и выезда
    в последующем это записывается в базу данных по id пользователя, чтобы забрать
    в функции get_dates

    Parameters:
    -------------
        user_id : int
            id пользователя, для нахождения в базе данных

        date_in : str
            дата въезда, принимается строкой, изначально None

        date-out : str
            дата выезда, принимается строкой, изначально None
    """

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    if date_in and date_out is not None:
        cursor.execute(f"UPDATE users SET date_out = Null, date_in = Null WHERE user_id = {user_id}")
        conn.commit()
    elif date_in is not None:
        cursor.execute(f"UPDATE users SET date_in = '{date_in}' WHERE user_id = {user_id}")
        conn.commit()
    elif date_out is not None:
        cursor.execute(f"UPDATE users SET date_out = '{date_out}' WHERE user_id = {user_id}")
        conn.commit()


def check_dates(user_id: int) -> Tuple[bool, int]:
    """
    Функция предназначена для проверки наличия в базе данныйх по указанному id
    записей даты въезда и выезда, и если значение None, то возвращает кортеж из False и числа

    Parameters:
    -------------
        user_id : int
            id пользователя
    """

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT date_in FROM users WHERE user_id = {user_id}")
    result_1 = cursor.fetchone()
    cursor.execute(f"SELECT date_out FROM users WHERE user_id = {user_id}")
    result_2 = cursor.fetchone()
    if result_1[0] is None:
        return True, 1
    elif result_2[0] is None:
        return True, 2


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
    for hotel in hotels:
        hotels_add.append(f"{hotel}|")
    hotels_add = ", ".join(hotels_add)
    user_info.append(hotels_add)
    cursor.execute("INSERT INTO history VALUES(?,?,?,?);", user_info)
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
            history_count = len(rows)
            for row in rows[:3]:
                time = row[2]
                command = row[1]
                hotels = row[3].split("|")
                hotel_message = ""

                for hotel in hotels:
                    hotel = hotel.replace(", ", " ")
                    hotel_message += f"{hotel}"

                message += f"\n<b>Время запроса: {time}</b>\nКоманда: {command}\nОтели:\n{hotel_message}"
        return message, history_count
    except ValueError:
        return False, 0


def update_request(user_id: int, hotels_count: int = None, answer: str = None, photos_count: int = None,
                   request: int = None):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    if hotels_count is not None:
        cursor.execute(f"""UPDATE parameters SET hotel_count = {hotels_count} WHERE user_id = {user_id}""")
        conn.commit()
    elif answer is not None:
        cursor.execute(f"""UPDATE parameters SET photo_answer = '{answer}' WHERE user_id = {user_id}""")
        conn.commit()
    elif photos_count is not None:
        cursor.execute(f"""UPDATE parameters SET photo_count = {photos_count} WHERE user_id = {user_id}""")
        conn.commit()
    elif (hotels_count and answer and photos_count and request) is None:
        cursor.execute(f"SELECT user_id FROM parameters WHERE user_id = {user_id}")
        data = cursor.fetchone()
        if data is None:
            info = [user_id, None, None, None]
            cursor.execute("INSERT INTO parameters VALUES(?,?,?,?);", info)
            conn.commit()

    if request is not None:
        if request == 0:
            cursor.execute(f"""UPDATE parameters SET
                    hotel_count = Null,
                    photo_answer = Null,
                    photo_count = Null
                    WHERE user_id = {user_id} """)
            conn.commit()
        if request == 1:
            cursor.execute(f"""SELECT hotel_count, photo_answer FROM parameters WHERE user_id = {user_id}""")
            result = cursor.fetchone()
            return result
        if request == 2:
            cursor.execute(f"""SELECT photo_count FROM parameters WHERE user_id = {user_id}""")
            result = cursor.fetchone()
            return result
