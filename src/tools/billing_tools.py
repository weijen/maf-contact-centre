from agent_framework import tool

from src.tools.mock_data import (
    ACCEPTED_PAYMENT_METHODS,
    ACCOUNTS,
    DEFAULT_ACCOUNT,
    PAYMENTS,
)


class BillingTools:
    """Plugin with functions available to the billing agent."""

    @tool()
    def get_account_balance(self, account_id: str = "default") -> str:
        """Get the account balance for a customer."""
        account = ACCOUNTS.get(account_id, DEFAULT_ACCOUNT)
        return f"The current balance for account {account_id} is ${account.balance:.2f}."

    @tool()
    def get_payment_methods(self) -> str:
        """Get available payment methods."""
        return ACCEPTED_PAYMENT_METHODS

    @tool()
    def check_payment_status(self, account_id: str, payment_id: str) -> str:
        """Check the status of a specific payment."""
        payment = PAYMENTS.get(payment_id)
        if payment:
            return f"Payment {payment_id} for account {account_id} is currently {payment.status}."
        return f"Payment {payment_id} for account {account_id} is currently pending."

    @tool()
    def process_payment(self, amount: float, method: str = "credit card") -> str:
        """Process a payment."""
        return f"Payment of ${amount:.2f} via {method} has been processed successfully."