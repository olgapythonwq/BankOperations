import logging
import os.path

import pandas as pd

from config import DATA_DIR, LOG_DIR
# from src.utils import from_xl_to_df, operations_file_path

export_path = os.path.join(DATA_DIR, "export.json")


log_file_path = os.path.join(LOG_DIR, "services.log")
file_logger = logging.getLogger("services")
file_handler = logging.FileHandler(log_file_path, encoding="utf-8", mode="w")
file_formatter = logging.Formatter("%(asctime)s - %(name)s – %(funcName)s – %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
file_logger.addHandler(file_handler)
file_logger.setLevel(logging.DEBUG)


def best_categories_for_cashback_to_json(data: pd.DataFrame, year: int, month: int) -> None:
    """Функция, анализирующая какие категории были наиболее выгодными для получения кешбэка"""
    # Отфильтруем по наличию в дате года и месяца и чтобы была заполнена колонка Кэшбэк
    filtered_df = data[(data['formatted_date'].dt.year == year) & (data['formatted_date'].dt.month == month)
                       & (data['Кэшбэк'].notna()) & (data['Кэшбэк'] != 0)]
    # Сумма по категориям
    sum_cashback = filtered_df.groupby('Категория')['Кэшбэк'].sum()
    # Запись в JSON
    sum_cashback.to_json(export_path, orient='index', force_ascii=False, indent=4)
    file_logger.info("Категории и суммы кэшбеков записаны в файл export.json.")


# if __name__ == '__main__':
    # print(best_categories_for_cashback_to_json(from_xl_to_df(operations_file_path), 2021, 4))
