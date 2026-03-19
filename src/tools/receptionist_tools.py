import datetime

from agent_framework import tool


class ReceptionistTools:
    """Plugin with functions available to the receptionist agent."""

    @tool()
    def get_current_time(self) -> str:
        """Get the current time."""
        return f"The current time is {datetime.datetime.now().strftime('%I:%M %p')}."

    @tool()
    def get_office_hours(self) -> str:
        """Get the office hours."""
        return "Our office hours are Monday through Friday, 9 AM to 5 PM Eastern Time."
