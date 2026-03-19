from unittest.mock import patch

from src.tools.support_tools import SupportPlugin


class TestCheckSystemStatus:
    def test_returns_a_valid_status(self):
        plugin = SupportPlugin()

        result = plugin.check_system_status()

        expected = [
            "All systems operational",
            "Minor delays in some regions",
            "Maintenance scheduled",
        ]
        assert result in expected

    def test_returns_specific_status_when_index_controlled(self):
        plugin = SupportPlugin()

        with patch("src.tools.support_tools.randint", return_value=0):
            result = plugin.check_system_status()

        assert result == "All systems operational"


class TestResetPassword:
    def test_returns_confirmation_with_user_id(self):
        plugin = SupportPlugin()

        result = plugin.reset_password(user_id="USR-456")

        assert "USR-456" in result
        assert "reset" in result.lower()

    def test_mentions_temporary_password_sent(self):
        plugin = SupportPlugin()

        result = plugin.reset_password(user_id="USR-1")

        assert "temporary password" in result.lower()
        assert "email" in result.lower()


class TestCreateSupportTicket:
    def test_returns_ticket_id_and_details(self):
        plugin = SupportPlugin()

        with patch("src.tools.support_tools.randint", return_value=12345):
            result = plugin.create_support_ticket(
                user_id="USR-789", issue_summary="Cannot login"
            )

        assert "TKT-12345" in result
        assert "USR-789" in result
        assert "Cannot login" in result

    def test_ticket_id_format(self):
        plugin = SupportPlugin()

        result = plugin.create_support_ticket(
            user_id="USR-1", issue_summary="test"
        )

        assert "TKT-" in result


class TestGetTroubleshootingSteps:
    def test_returns_connectivity_steps(self):
        plugin = SupportPlugin()

        result = plugin.get_troubleshooting_steps(issue_type="connectivity")

        assert "internet connection" in result
        assert "router" in result

    def test_returns_login_steps(self):
        plugin = SupportPlugin()

        result = plugin.get_troubleshooting_steps(issue_type="login")

        assert "username" in result
        assert "password" in result

    def test_returns_performance_steps(self):
        plugin = SupportPlugin()

        result = plugin.get_troubleshooting_steps(issue_type="performance")

        assert "Close unused applications" in result

    def test_is_case_insensitive(self):
        plugin = SupportPlugin()

        result = plugin.get_troubleshooting_steps(issue_type="CONNECTIVITY")

        assert "internet connection" in result

    def test_returns_fallback_for_unknown_issue(self):
        plugin = SupportPlugin()

        result = plugin.get_troubleshooting_steps(issue_type="unknown_issue")

        assert "describe your issue" in result.lower()
