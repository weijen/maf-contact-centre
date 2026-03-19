from random import randint
from agent_framework import tool


class SupportPlugin:
    """Plugin with functions available to the support agent."""

    @tool()
    def check_system_status(self) -> str:
        """Check the current system status."""
        statuses = ["All systems operational", "Minor delays in some regions", "Maintenance scheduled"]
        return statuses[randint(0, len(statuses) - 1)]  # nosec

    @tool()
    def reset_password(self, user_id: str) -> str:
        """Reset the password for a customer account."""
        return f"Password for user {user_id} has been reset. A temporary password has been sent to the registered email."

    @tool()
    def create_support_ticket(self, user_id: str, issue_summary: str) -> str:
        """Create a support ticket for the customer."""
        ticket_id = f"TKT-{randint(10000, 99999)}"  # nosec
        return f"Support ticket {ticket_id} has been created for user {user_id}: {issue_summary}"

    @tool()
    def get_troubleshooting_steps(self, issue_type: str) -> str:
        """Get troubleshooting steps for common issues."""
        steps = {
            "connectivity": "1. Check your internet connection. 2. Restart your router. 3. Clear browser cache.",
            "login": "1. Verify your username and password. 2. Check caps lock. 3. Try password reset.",
            "performance": "1. Close unused applications. 2. Clear temporary files. 3. Restart your device.",
        }
        return steps.get(issue_type.lower(), "Please describe your issue in more detail.")
