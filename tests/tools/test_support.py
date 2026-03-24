from src.tools.support_tools import SupportPlugin


class TestCheckSystemStatus:
    def test_returns_operational_status(self):
        plugin = SupportPlugin()

        result = plugin.check_system_status()

        assert result == "All systems operational"

    def test_is_deterministic(self):
        plugin = SupportPlugin()

        assert plugin.check_system_status() == plugin.check_system_status()


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

        result = plugin.create_support_ticket(
            user_id="USR-789", issue_summary="Cannot login"
        )

        assert "TKT-" in result
        assert "USR-789" in result
        assert "Cannot login" in result

    def test_ticket_ids_are_sequential(self):
        plugin = SupportPlugin()

        result1 = plugin.create_support_ticket(user_id="USR-1", issue_summary="first")
        result2 = plugin.create_support_ticket(user_id="USR-2", issue_summary="second")

        assert result1 != result2
        assert "TKT-" in result1
        assert "TKT-" in result2


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
