import logging
import os
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional

import pandas as pd
from dateutil.relativedelta import relativedelta

from config import LOG_DIR
from src.utils import DATA_DIR, from_xl_to_df, operations_file_path

log_file_path = os.path.join(LOG_DIR, "reports.log")
file_logger = logging.getLogger("services")
file_handler = logging.FileHandler(log_file_path, encoding="utf-8", mode="w")
file_formatter = logging.Formatter("%(asctime)s - %(name)s – %(funcName)s – %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
file_logger.addHandler(file_handler)
file_logger.setLevel(logging.DEBUG)


def save_report(filename: str) -> Callable:
    def decorator(function: Callable) -> Callable:
        @wraps(function)
        def wrapper(*args: tuple[Any], **kwargs: dict[Any, Any]) -> Any:
            result = function(*args, **kwargs)
            # Формируем полный путь к файлу
            file_path = os.path.join(DATA_DIR, filename)
            # Сохраняем DataFrame в Excel
            if isinstance(result, pd.DataFrame):
                result.to_excel(file_path, index=False)
                file_logger.info("Отчёт сохранён.")
                print(f"Отчёт сохранён в {filename}.")
            else:
                print("Отчёт пустой.")
            return result
        return wrapper
    return decorator


@save_report("report_per_category.xlsx")
def spending_by_category(transactions: pd.DataFrame,
                         category: str,
                         date: Optional[str] = None) -> pd.DataFrame:
    """Функция, возвращающая траты по заданной категории за последние три месяца"""
    # Если дата не указана — берём текущую
    if date:
        end = datetime.strptime(date, '%Y-%m-%d')
    else:
        end = datetime.now()
        file_logger.info("Т.к. дата не была передана, то отчет будет сформирован на основе последних трёх месяцев.")

    # Устанавливаем конец дня
    end = end.replace(hour=23, minute=59, second=59)

    # Вычитаем 3 месяца
    start = end - relativedelta(months=3)
    start = start.replace(hour=0, minute=0, second=0)

    print("Start:", start.strftime('%Y-%m-%d %H:%M:%S'))
    print("End:  ", end.strftime('%Y-%m-%d %H:%M:%S'))

    # Фильтрация
    mask = ((transactions['Категория'] == category)
            & (transactions['formatted_date'] >= start)
            & (transactions['formatted_date'] <= end))
    file_logger.info("Отчёт сформирован.")
    return transactions.loc[mask]


if __name__ == '__main__':
    spending_by_category(from_xl_to_df(operations_file_path), "Транспорт", "2020-01-23")
