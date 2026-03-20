from agent_framework import tool

from src.tools.mock_data import (
    SYSTEM_STATUS,
    TROUBLESHOOTING_FALLBACK,
    TROUBLESHOOTING_STEPS,
    next_ticket_id,
)


class SupportPlugin:
    """Plugin with functions available to the support agent."""

    @tool()
    def check_system_status(self) -> str:
        """Check the current system status."""
        return SYSTEM_STATUS

    @tool()
    def reset_password(self, user_id: str) -> str:
        """Reset the password for a customer account."""
        return f"Password for user {user_id} has been reset. A temporary password has been sent to the registered email."

    @tool()
    def create_support_ticket(self, user_id: str, issue_summary: str) -> str:
        """Create a support ticket for the customer."""
        ticket_id = next_ticket_id()
        return f"Support ticket {ticket_id} has been created for user {user_id}: {issue_summary}"

    @tool()
    def get_troubleshooting_steps(self, issue_type: str) -> str:
        """Get troubleshooting steps for common issues."""
        return TROUBLESHOOTING_STEPS.get(issue_type.lower(), TROUBLESHOOTING_FALLBACK)
