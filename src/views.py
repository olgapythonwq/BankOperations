import json
import logging
import os
from datetime import datetime

from config import LOG_DIR
from src.utils import (
    create_currency_list,
    create_tickers_list,
    filter_transactions_by_date,
    from_xl_to_df,
    get_currency_rates,
    get_info_cards,
    get_ticker_prices,
    get_top_transactions,
    operations_file_path,
    user_settings_file_path
)

# now = datetime.now()  # Получаем текущие дату и время
# current_time = now.time()  # Вычленяем только время
# current_time_formatted = now.strftime("%H:%M:%S")

log_file_path = os.path.join(LOG_DIR, "views.log")
file_logger = logging.getLogger("views")
file_handler = logging.FileHandler(log_file_path, encoding="utf-8", mode="w")
file_formatter = logging.Formatter("%(asctime)s - %(name)s – %(funcName)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
file_logger.addHandler(file_handler)
file_logger.setLevel(logging.DEBUG)


def greeting() -> str:
    """Функция, приветствующая пользователя по разному в зависимости от времени суток"""
    now = datetime.now()  # Получаем текущие дату и время
    if 6 <= now.hour < 12:
        greeting_phrase = "Доброе утро"
    elif 12 <= now.hour < 18:
        greeting_phrase = "Добрый день"
    elif 18 <= now.hour < 24:
        greeting_phrase = "Добрый вечер"
    else:
        greeting_phrase = "Доброй ночи"
    file_logger.info("Приветственная фраза сформирована")
    return greeting_phrase


def fill_front_page(date: str) -> dict:
    """Функция главной страницы, принимающая строку с датой и временем в формате YYYY-MM-DD HH:MM:SS и возвращающая
     ответ в виде словаря"""
    result = {"greeting": greeting(),
              "cards": get_info_cards(filter_transactions_by_date(from_xl_to_df(operations_file_path), date)),
              "top_transactions": get_top_transactions(from_xl_to_df(operations_file_path)),
              "currency_rates": get_currency_rates(create_currency_list(user_settings_file_path)),
              "stock_prices": get_ticker_prices(create_tickers_list(user_settings_file_path))}
    file_logger.info("JSON-ответ сформирован")
    return result


if __name__ == '__main__':
    # print(greeting())
    # print(get_front_page("2021-12-31 15:15:15"))
    pretty_result = json.dumps(fill_front_page("2021-12-31 15:15:15"), indent=4, ensure_ascii=False)
    print(pretty_result)
