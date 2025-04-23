from pathlib import Path

import pandas as pd
import pytest

from src.utils import from_xl_to_df, filter_transactions_by_date, get_info_cards, get_top_transactions, \
    create_currency_list, get_currency_rate, get_currency_rates, create_tickers_list, get_ticker_prices, \
    get_ticker_price
from unittest.mock import mock_open, patch, Mock
import json



def test_from_xl_to_df():
    root = Path(__file__).resolve().parent.parent  # поднимаемся в корень проекта
    path_to_excel = root / "data" / "test_operations.xlsx"

    df = from_xl_to_df(str(path_to_excel))

    assert not df.empty
    assert 'formatted_date' in df.columns


@pytest.fixture
def sample_transactions():
    return pd.DataFrame({
        "formatted_date": pd.to_datetime([
            "2023-04-01 10:00:00",
            "2023-04-10 15:30:00",
            "2023-04-21 23:59:59",
            "2023-05-01 00:00:00"
        ])
    })
def test_filter_transactions_by_date_only_end_date(sample_transactions):
    result = filter_transactions_by_date(sample_transactions, end_date="2023-04-21 00:00:00")
    assert len(result) == 3  # все 3 из апреля


def test_filter_transactions_by_date_with_both_dates(sample_transactions):
    result = filter_transactions_by_date(
        sample_transactions,
        start_date="2023-04-10 00:00:00",
        end_date="2023-04-21 23:59:59"
    )
    assert len(result) == 2
    assert all(result['formatted_date'] >= pd.Timestamp("2023-04-10"))  # как pd.to_datetime
    assert all(result['formatted_date'] <= pd.Timestamp("2023-04-21 23:59:59"))


def test_filter_transactions_by_date_format_error(sample_transactions):
    with pytest.raises(ValueError, match="Формат даты должен быть"):
        filter_transactions_by_date(sample_transactions, end_date="21-04-2023 00:00:00")


def test_filter_transactions_by_date_border_inclusion(sample_transactions):
    result = filter_transactions_by_date(
        sample_transactions,
        start_date="2023-04-01 00:00:00",
        end_date="2023-04-21 23:59:59"
    )
    # Убеждаемся, что среди дат в колонке formatted_date есть точное значение 2024-04-21 23:59:59
    # .astype(str) преобразует каждое значение даты/времени в строку: результат Series строк
    # .values Преобразует Series в NumPy-массив
    assert "2023-04-21 23:59:59" in result["formatted_date"].astype(str).values


def test_get_info_cards():
    df = pd.DataFrame({
        "Номер карты": ["x1234", "x1234", "x5678", "x5678", "x5678"],
        "Статус": ["OK", "FAILED", "OK", "OK", "OK"],
        "Сумма платежа": [-100, -50, -200, 300, -100],  # Только 3 подходят
        "Сумма операции с округлением": [100, 50, 200, 300, 100],
        "Кэшбэк": [1.5, 0, 3.0, 0.0, 1.0]
    })

    result = get_info_cards(df)

    assert isinstance(result, list)
    assert len(result) == 2

    card_1234 = next(card for card in result if card["last_digits"] == "1234")
    assert card_1234["total_spent"] == 100
    assert card_1234["cashback"] == 1.5

    card_5678 = next(card for card in result if card["last_digits"] == "5678")
    assert card_5678["total_spent"] == 300  # 200 + 100
    assert card_5678["cashback"] == 4.0

    # with patch("src.utils.file_logger") as mock_logger:
    #     mock_logger.info.assert_called_once_with("Все основные данные по картам получены.")


def test_get_top_transactions():
    df = pd.DataFrame({
        "Статус": ["OK", "FAILED", "OK", "OK", "OK"],
        "Дата платежа": ["21.03.2019", "23.10.2018", "23.05.2018", "13.10.2019", "23.10.2018"],
        "Сумма операции с округлением": [100, 50, 200, 300, 150],
        "Категория": ["Фастфуд", "Сервис", "Красота", "Рестораны", "Транспорт"],
        "Описание": ["McDonald's", "Google", "OOO Balid", "Resto-Art", "Яндекс Такси"]
    })
    result = get_top_transactions(df, 3)

    assert isinstance(result, list)
    assert len(result) == 3

    assert result[0]["amount"] == 300
    assert result[2]["amount"] == 150

    # with patch("src.utils.file_logger") as mock_logger:
    #     mock_logger.info.assert_called_once()


def test_create_currency_list():
    json_for_test = json.dumps({"user_currencies": ["CHF", "EUR"]})

    with patch("src.utils.open", mock_open(read_data=json_for_test)), \
            patch("src.utils.file_logger") as mock_logger:
        result = create_currency_list("fake_path.json")

        # Проверяем результат
        assert result == ["CHF", "EUR"]
        assert isinstance(result, list)

        # Проверяем, что логгер был вызван
        mock_logger.info.assert_called_once_with("Список необходимых валют получен.")


@patch("src.utils.requests.get")
@patch("src.utils.os.getenv", return_value="fake_api_key")
def test_get_currency_rate_ok(mock_getenv, mock_get):  # mock_getenv подменяет os.getenv() внутри get_currency_rate
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"rates": {"RUB": 92.15}}

    mock_get.return_value = mock_response

    result = get_currency_rate("USD")
    assert result == 92.15


@patch("src.utils.requests.get")
@patch("src.utils.os.getenv", return_value="fake_api_key")
@patch("src.utils.file_logger")
def test_get_currency_rate_ko(mock_logger, mock_getenv, mock_get):
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.text = "Not found"
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="Ошибка при запросе курса USD: 404"):
        get_currency_rate("USD")

    mock_logger.warning.assert_called_once_with("Курс для USD не найден. 404")


@patch("src.utils.get_currency_rate")
@patch("src.utils.file_logger")
def test_get_currency_rates(mock_logger, mock_get_rate):
    mock_get_rate.side_effect = lambda currency: {"USD": 92.15, "EUR": 98.45}[currency]

    result = get_currency_rates(["USD", "EUR"])

    expected = [
        {"currency": "USD", "rate": 92.15},
        {"currency": "EUR", "rate": 98.45}
    ]

    assert result == expected
    assert mock_get_rate.call_count == 2
    mock_logger.info.assert_called_with("Курсы валют получены от API и записаны в список словарей.")


def test_create_tickers_list():
    json_for_test = json.dumps({"user_stocks": ["AAPL", "AMZN"]})

    with patch("src.utils.open", mock_open(read_data=json_for_test)), \
            patch("src.utils.file_logger") as mock_logger:
        result = create_tickers_list("fake_path.json")

        # Проверяем результат
        assert result == ["AAPL", "AMZN"]
        assert isinstance(result, list)

        # Проверяем, что логгер был вызван
        mock_logger.info.assert_called_once_with("Список необходимых тикеров получен.")


@patch("src.utils.requests.get")
@patch("src.utils.os.getenv", return_value="fake_api_key")
def test_get_ticker_price_ok(mock_getenv, mock_get):  # mock_getenv подменяет os.getenv() внутри get_currency_rate
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": [
            {"close": 196.98}
        ]
    }
    mock_get.return_value = mock_response

    result = get_ticker_price("AAPL")
    assert result == 196.98


@patch("src.utils.requests.get")
@patch("src.utils.os.getenv", return_value="fake_api_key")
def test_get_ticker_price_ko(mock_getenv, mock_get):
    # Мокаем ответ с ошибкой 500
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    mock_get.return_value = mock_response

    result = get_ticker_price("AAPL")

    # Проверяем, что функция вернула 0.0 в случае ошибки
    assert result == 0.0

    # Также проверим, что warning логгер был вызван с правильным сообщением
    mock_getenv.assert_called_once_with("API_KEY_2")
    mock_get.assert_called_once()
    mock_getenv.assert_called_once_with("API_KEY_2")  # Проверяем что подставляется правильный API_KEY


@patch("src.utils.requests.get")
@patch("src.utils.os.getenv", return_value="fake_api_key")
@patch("src.utils.file_logger")
def test_get_ticker_price_no_data(mock_logger, mock_getenv, mock_get):
    # Мокируем успешный ответ, но без данных
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": []}  # Пустой список данных

    mock_get.return_value = mock_response

    # Вызываем функцию
    result = get_ticker_price("AAPL")

    # Проверяем, что функция вернула 0.0, так как цена не найдена
    assert result == 0.0

    # Проверяем, что warning логгер был вызван с правильным сообщением
    mock_logger.warning.assert_called_once_with("Цена для AAPL не найдена.")


@patch("src.utils.get_ticker_price")
@patch("src.utils.file_logger")
def test_get_ticker_prices(mock_logger, mock_get_price):
    mock_get_price.side_effect = lambda price: {"AAPL": 196.98, "AMZN": 172.61}[price]

    result = get_ticker_prices(["AAPL", "AMZN"])

    expected = [
        {"stock": "AAPL", "price": 196.98},
        {"stock": "AMZN", "price": 172.61}
    ]

    assert result == expected
    assert mock_get_price.call_count == 2
    mock_logger.info.assert_called_with("Цены тикеров получены от API и записаны в список словарей.")
