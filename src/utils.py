import json
import logging
import os
from typing import Optional

import pandas as pd
import requests
from dotenv import load_dotenv
from pandas import DataFrame

from config import DATA_DIR, LOG_DIR, ROOT_DIR

operations_file_path = os.path.join(DATA_DIR, 'operations.xlsx')
user_settings_file_path = os.path.join(DATA_DIR, 'user_settings.json')


log_file_path = os.path.join(LOG_DIR, "utils.log")
file_logger = logging.getLogger("utils")
file_handler = logging.FileHandler(log_file_path, encoding="utf-8", mode="w")
file_formatter = logging.Formatter("%(asctime)s - %(name)s – %(funcName)s – %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
file_logger.addHandler(file_handler)
file_logger.setLevel(logging.DEBUG)


def from_xl_to_df(path_to_file: str) -> DataFrame:
    """Функция, принимающая путь до EXCEL файла и возвращающая объект DataFrame с данными об операциях"""
    transactions = pd.read_excel(path_to_file)
    # Добавим колонку с отформатированной датой
    transactions['formatted_date'] = pd.to_datetime(transactions["Дата операции"], format='%d.%m.%Y %H:%M:%S')
    return transactions


def filter_transactions_by_date(transactions: DataFrame, end_date: str, start_date: Optional[str] = None) -> DataFrame:
    """Функция, фильтрующая транзакции по дате. Формат дат: YYYY-MM-DD HH:MM:SS"""
    try:
        # Распознаём даты по формату dd/mm/yyyy
        end = pd.to_datetime(end_date, format='%Y-%m-%d %H:%M:%S')
        if start_date is None:
            start = end.replace(day=1)
        else:
            start = pd.to_datetime(start_date, format='%Y-%m-%d %H:%M:%S')
    except ValueError:
        raise ValueError("❌ Формат даты должен быть 'YYYY-MM-DD HH:MM:SS', например: 2021-12-31 15:15:15")
    # Устанавливаем время на границы дня
    start = start.replace(hour=0, minute=0, second=0)
    end = end.replace(hour=23, minute=59, second=59)

    filtered_operations = transactions.loc[(transactions['formatted_date'] >= start)
                                           & (transactions['formatted_date'] <= end)]
    return filtered_operations


def get_info_cards(transactions: DataFrame) -> list[dict]:
    """Функция, принимающая объект DataFrame с данными об операциях и возвращающая данные по картам"""
    cards_info = []
    transactions_ok = transactions[(transactions['Статус'] == 'OK') & (transactions['Сумма платежа'] < 0)]
    transactions_grouped_by_cards = transactions_ok[
        ["Номер карты", "Кэшбэк", "Сумма операции с округлением"]].groupby("Номер карты", as_index=False).sum()

    for index, row in transactions_grouped_by_cards.iterrows():
        cards_info.append({"last_digits": row['Номер карты'][1:],
                           "total_spent": round(row['Сумма операции с округлением'], 2),
                           "cashback": row["Кэшбэк"]})
    file_logger.info("Все основные данные по картам получены.")
    return cards_info


def get_top_transactions(transactions: DataFrame, top: int = 5) -> list[dict]:
    """Функция, принимающая объект DataFrame с данными об операциях и возвращающая топ-5 транзакций"""
    top_transactions = []
    transactions_ok = transactions[transactions['Статус'] == 'OK']
    top_transactions_ok = transactions_ok.sort_values('Сумма операции с округлением', ascending=False).head(top)
    for index, row in top_transactions_ok.iterrows():
        top_transactions.append({"date": row["Дата платежа"],
                                 "amount": row['Сумма операции с округлением'],
                                 "category": row["Категория"],
                                 "description": row["Описание"]})
    file_logger.info(f"Топ-{top} транзакций по сумме платежа успешно отфильтрованы.")
    return top_transactions


def create_currency_list(path: str) -> list[str]:
    """Функция, принимающая путь до json файла и возвращающая список валют"""
    # Загружаем валюты из файла
    with open(path, 'r') as f:
        data = json.load(f)
        user_currencies: list[str] = data['user_currencies']  # ["USD", "EUR"]
    file_logger.info("Список необходимых валют получен.")
    return user_currencies


def get_currency_rates(currencies: list) -> list[dict]:
    """Функция, принимающая список валют и возвращающая курсы валют от API"""
    currency_rates = []
    for currency in currencies:
        currency_rates.append({"currency": currency,
                               "rate": round(get_currency_rate(currency), 2)})
    file_logger.info("Курсы валют получены от API и записаны в список словарей.")
    return currency_rates


def get_currency_rate(currency: str) -> float:
    """Функция, принимающая валюту, получающая её курс от API"""
    load_dotenv(os.path.join(ROOT_DIR, '.env'))

    API_KEY = os.getenv('API_KEY')
    headers = {"apikey": API_KEY}
    # Запросим RUB к каждой валюте
    url = f'https://api.apilayer.com/exchangerates_data/latest?symbols=RUB&base={currency}'
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        rate: float = response.json()['rates']['RUB']
        file_logger.info(f"Курс валюты {currency} получен от API.")
        return rate
    else:
        file_logger.warning(f"Курс для {currency} не найден. {response.status_code}")
        print(f"Ошибка при запросе для {currency}: {response.status_code}")
        print(response.text)
        raise ValueError(f"Ошибка при запросе курса {currency}: {response.status_code}")


def create_tickers_list(path: str) -> list[str]:
    """Функция, принимающая путь до json файла и возвращающая список тикеров"""
    # Загружаем тикеры из файла
    with open(path, 'r') as f:
        data = json.load(f)
        user_tickers: list[str] = data['user_stocks']  # ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]
    file_logger.info("Список необходимых тикеров получен.")
    return user_tickers


def get_ticker_prices(tickers: list) -> list[dict]:
    """Функция, принимающая список тикеров и возвращающая цены тикеров от API"""
    ticker_prices = []
    for ticker in tickers:
        ticker_prices.append({"stock": ticker,
                              "price": round(get_ticker_price(ticker), 2)})
    file_logger.info("Цены тикеров получены от API и записаны в список словарей.")
    return ticker_prices


def get_ticker_price(ticker: str, price_type: str = "close") -> float:
    """Функция, принимающая тикер, получающая его цену от API"""
    load_dotenv(os.path.join(ROOT_DIR, '.env'))

    API_KEY = os.getenv('API_KEY_2')
    querystring = {'access_key': API_KEY,
                   "symbols": ticker,
                   "limit": 1}
    url = 'https://api.marketstack.com/v1/eod'
    response = requests.get(url, params=querystring)

    if response.status_code == 200:
        data = response.json()
        if data['data']:
            file_logger.info(f"Цена тикера {ticker} получена от API.")
            return float(data['data'][0].get(price_type, 0.0))  # Цена закрытия последней сессии
        else:
            file_logger.warning(f"Цена для {ticker} не найдена.")
            print(f"Нет данных для тикера {ticker}")
            return 0.0
    else:
        file_logger.warning(f"Ошибка при запросе: {response.status_code}.")
        print(f"Ошибка при запросе для {ticker}: {response.status_code}")
        print(response.text)
        return 0.0


# def get_full_ticker_data(ticker: str) -> dict:
#     """Получает полный ответ по тикеру от API."""
#     load_dotenv(os.path.join(ROOT_DIR, '.env'))
#     API_KEY = os.getenv('API_KEY_2')
#
#     url = 'https://api.marketstack.com/v1/eod'
#     params = {
#         'access_key': API_KEY,
#         'symbols': ticker,
#         'limit': 1  # чтобы вывести последний день
#     }
#
#     response = requests.get(url, params=params)
#     if response.status_code == 200:
#         data = response.json()
#         return data  # возвращаем весь словарь
#     else:
#         print(f"Ошибка при запросе для {ticker}: {response.status_code}")
#         print(response.text)
#         return {}


if __name__ == '__main__':
    # operations_data = from_xl_to_df(operations_file_path)
    # print(operations_data)
    print(filter_transactions_by_date(from_xl_to_df(
        operations_file_path), "2021-12-31 15:15:15", "2021-12-01 15:15:15"))
    # print(filter_transactions_by_date(from_xl_to_df(operations_file_path), "2021-12-31 15:15:15"))
    # print(get_info_cards(from_xl_to_df(operations_file_path)))
    # print(get_top_transactions(from_xl_to_df(operations_file_path)))
    # print(create_currency_list(user_settings_file_path))
    # print(get_currency_rates(create_currency_list(user_settings_file_path)))
    # print(json.dumps(get_full_ticker_data("AAPL"), indent=4))
    # full_data = get_ticker_price("AAPL")
    # print(json.dumps(full_data, indent=4))
    # print(get_ticker_prices(create_tickers_list(user_settings_file_path)))
