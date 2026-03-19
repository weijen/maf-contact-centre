from unittest.mock import patch
from datetime import datetime

from src.tools.receptionist_tools import ReceptionistTools


class TestGetCurrentTime:
    def test_returns_formatted_time(self):
        tools = ReceptionistTools()
        fake_now = datetime(2026, 3, 19, 14, 30, 0)

        with patch("src.tools.receptionist_tools.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = fake_now
            result = tools.get_current_time()

        assert "02:30 PM" in result

    def test_contains_current_time_prefix(self):
        tools = ReceptionistTools()
        fake_now = datetime(2026, 1, 1, 9, 0, 0)

        with patch("src.tools.receptionist_tools.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = fake_now
            result = tools.get_current_time()

        assert result.startswith("The current time is")


class TestGetOfficeHours:
    def test_returns_office_hours(self):
        tools = ReceptionistTools()

        result = tools.get_office_hours()

        assert "Monday" in result
        assert "Friday" in result
        assert "9 AM" in result
        assert "5 PM" in result

    def test_mentions_eastern_time(self):
        tools = ReceptionistTools()

        result = tools.get_office_hours()

        assert "Eastern Time" in result
