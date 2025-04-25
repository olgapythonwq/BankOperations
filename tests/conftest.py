from datetime import datetime
from tempfile import NamedTemporaryFile
from unittest.mock import patch

import pytest
from freezegun import freeze_time
import pandas as pd


@pytest.fixture
def freezer():
    with freeze_time() as frozen:
        yield frozen

@pytest.fixture
def temp_excel_file():
    df = pd.DataFrame({
        "Дата операции": ["30.12.2021 10:50:17", "31.12.2021 17:50:17","30.12.2020 07:50:17", "30.12.2019 15:50:17"],
        "Сумма операции с округлением": [1000, 2000, 3000, 4000],

    })

    with NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        df.to_excel(tmp.name, index=False)
        yield tmp.name

@pytest.fixture
def frozen_datetime():
    with patch("src.reports.datetime") as mock_dt:
        fake_now = datetime(2025, 4, 1, 12, 0, 0)
        mock_dt.now.return_value = fake_now
        mock_dt.strptime = datetime.strptime
        mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        yield mock_dt
