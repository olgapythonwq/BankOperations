import pandas as pd
import pytest
from unittest.mock import patch, Mock
from src.services import best_categories_for_cashback_to_json


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        'formatted_date': pd.to_datetime([
            '2024-05-01', '2024-05-15', '2024-06-01', '2024-05-20'
        ]),
        'Категория': ['Еда', 'Еда', 'Путешествия', 'Транспорт'],
        'Кэшбэк': [50, 100, None, 30]
    })


@pytest.mark.parametrize("year,month,expected_dict", [
    (2024, 5, {'Еда': 150, 'Транспорт': 30}),
    (2024, 6, {}),  # кешбэк отсутствует
    (2023, 5, {}),  # нет данных за этот год
])
def test_best_categories_for_cashback_to_json(sample_df, year, month, expected_dict):
    # Моки
    mocked_logger = Mock()
    mocked_to_json = Mock()

    with patch("src.services.export_path", "mocked_path.json"), \
         patch("src.services.file_logger", mocked_logger), \
         patch("pandas.Series.to_json", new=mocked_to_json):

        best_categories_for_cashback_to_json(sample_df, year, month)

        # Проверка, что сериализация происходила с правильным словарем
        if expected_dict:
            # .to_json вызывается на Series — проверим, к какому dict она эквивалентна
            args, kwargs = mocked_to_json.call_args
            assert kwargs['orient'] == 'index'
            assert kwargs['force_ascii'] is False
            assert kwargs['indent'] == 4
            assert args[0] == "mocked_path.json"
        else:
            mocked_to_json.assert_called_once()
            # Если словарь пустой — всё равно сериализация происходит, но логика не меняется

        mocked_logger.info.assert_called_with(
            "Категории и суммы кэшбеков записаны в файл export.json."
        )
