
from random import randint
from agent_framework import tool

class BillingTools:
    """Plugin with functions available to the billing agent."""

    @tool()
    def get_account_balance(self, account_id: str = "default") -> str:
        """Get the account balance for a customer."""
        # Simulated balance
        balance = randint(50, 500)  # nosec
        return f"The current balance for account {account_id} is ${balance:.2f}."

    @tool()
    def get_payment_methods(self) -> str:
        """Get available payment methods."""
        return "We accept credit cards (Visa, MasterCard, American Express), bank transfers, and PayPal."

    @tool()
    def check_payment_status(self, account_id: str, payment_id: str) -> str:
        """Check the status of a specific payment."""
        statuses = ["completed", "pending", "failed"]
        status = statuses[hash(payment_id) % len(statuses)]
        return f"Payment {payment_id} for account {account_id} is currently {status}."

    @tool()
    def process_payment(self, amount: float, method: str = "credit card") -> str:
        """Process a payment."""
        return f"Payment of ${amount:.2f} via {method} has been processed successfully."