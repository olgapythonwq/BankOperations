from unittest.mock import patch

import pandas as pd
import pytest
from datetime import datetime
from src.reports import spending_by_category, save_report


@pytest.fixture
def transactions_df():
    return pd.DataFrame({
        'Категория': ['Еда', 'Еда', 'Развлечения'],
        'formatted_date': [
            datetime(2025, 3, 1),
            datetime(2025, 2, 15),
            datetime(2024, 12, 20)
        ],
        'Сумма': [1000, 500, 300]
    })

@pytest.mark.parametrize("category, expected_count", [
    ("Еда", 2),
    ("Развлечения", 0),  # вне диапазона
])
def test_spending_filter(transactions_df, category, expected_count):
    result = spending_by_category(transactions_df, category, date="2025-04-01")
    assert len(result) == expected_count


def test_with_fixed_time(frozen_datetime, transactions_df):
    result = spending_by_category(transactions_df, "Еда")
    assert len(result) == 2


@patch("pandas.DataFrame.to_excel")
def test_save_report_decorator_calls_to_excel(mock_to_excel):
    df = pd.DataFrame({"a": [1, 2, 3]})
    filename = "fake_report.xlsx"

    @save_report(filename)
    def generate_report():
        return df

    result = generate_report()

    # Проверяем, что to_excel вызвался один раз
    mock_to_excel.assert_called_once()

    # Проверяем, что путь передан корректно
    args, kwargs = mock_to_excel.call_args
    assert filename in args[0] or filename in str(args[0])  # путь содержит имя файла
