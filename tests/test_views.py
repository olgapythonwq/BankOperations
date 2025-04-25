import pytest

from src.views import greeting
from unittest.mock import patch

from src.views import fill_front_page


@pytest.mark.parametrize("current_date, expected_result",
                        [("2021-01-01T11:59", "Доброе утро"),
                         ("2021-01-01T15:59", "Добрый день"),
                         ("2021-01-01T18:59", "Добрый вечер"),
                         ("2021-01-01T03:59", "Доброй ночи")])
def test_greeting(current_date, expected_result, freezer):
    freezer.move_to(current_date)
    result = greeting()
    assert result == expected_result


# Замокаем вызовы всех функций внутри функции-агрегатора
@patch("src.views.file_logger")
@patch("src.views.get_ticker_prices", return_value=["AAPL", "TSLA"])
@patch("src.views.create_tickers_list", return_value=["AAPL", "TSLA"])
@patch("src.views.get_currency_rates", return_value=[{"currency": "USD", "rate": 92.0}])
@patch("src.views.create_currency_list", return_value=["USD"])
@patch("src.views.get_top_transactions", return_value=["TX1", "TX2"])
@patch("src.views.get_info_cards", return_value=[{"last_digits": "1234"}])
@patch("src.views.filter_transactions_by_date", return_value="filtered_df")
@patch("src.views.from_xl_to_df", return_value="mock_df")
@patch("src.views.greeting", return_value="Привет!")
def test_fill_front_page(
    mock_greet, mock_xl_to_df, mock_filter_by_date, mock_cards, mock_top,
    mock_currency_list, mock_rates, mock_tickers, mock_prices, mock_logger
):
    result = fill_front_page("2023-04-01 00:00:01")

    assert result == {
        "greeting": "Привет!",
        "cards": [{"last_digits": "1234"}],
        "top_transactions": ["TX1", "TX2"],
        "currency_rates": [{"currency": "USD", "rate": 92.0}],
        "stock_prices": ["AAPL", "TSLA"]
    }

    mock_logger.info.assert_called_once_with("JSON-ответ сформирован")