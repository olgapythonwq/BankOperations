from datetime import datetime

from src.utils import operations_file_path, from_xl_to_df

transactions = from_xl_to_df(operations_file_path)
min_date = transactions.formatted_date.min()
max_date = transactions.formatted_date.max()


def get_user_date() -> str:
    """Функция, запрашивающая у пользователя доту и возвращающая дату в формате YYYY-MM-DD HH:MM:SS"""
    min_date_str = min_date.strftime("%Y-%m-%d")
    max_date_str = max_date.strftime("%Y-%m-%d")
    print(f"Введите дату, на которую Вы бы хотели видеть результаты между {min_date_str} и {max_date_str}")

    while True:
        user_answer = input("Дата (ГГГГ-ММ-ДД): ")
        try:
            user_date = datetime.strptime(user_answer, "%Y-%m-%d")
            if min_date.date() <= user_date.date() <= max_date.date():
                return user_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                print(f"Дата вне допустимого диапазона. Введите дату между {min_date_str} и {max_date_str}.")
        except ValueError:
            print("Неверный формат. Пожалуйста, используйте формат ГГГГ-ММ-ДД (например, 2024-04-23).")


def get_user_year_month() -> tuple:
    """Функция, запрашивающая у пользователя год и месяц"""
    min_date_str = min_date.strftime("%Y-%m")
    max_date_str = max_date.strftime("%Y-%m")
    print(f"Введите год и месяц для расчёта предыдущих трёх месяцев между {min_date_str} и {max_date_str}")
    while True:
        user_answer = input('Год и месяц (ГГГГ-ММ): ')
        try:
            user_date = datetime.strptime(user_answer, "%Y-%m")
            if min_date <= user_date <= max_date:
                print(f"{user_date.year}, {user_date.month}")
                return user_date.year, user_date.month
            else:
                print(f"Ваш выбор вне допустимого диапазона. Введите между {min_date_str} и {max_date_str}.")
        except ValueError:
            print("Неверный формат. Пожалуйста, используйте формат ГГГГ-ММ (например, 2024-04).")
