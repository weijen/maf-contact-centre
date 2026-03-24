from src.tools.billing_tools import BillingTools
from src.tools.mock_data import ACCOUNTS, DEFAULT_ACCOUNT


class TestGetAccountBalance:
    def test_returns_balance_for_known_account(self):
        tools = BillingTools()

        result = tools.get_account_balance(account_id="ACC-1001")

        assert result == "The current balance for account ACC-1001 is $245.50."

    def test_returns_default_balance_for_unknown_account(self):
        tools = BillingTools()

        result = tools.get_account_balance(account_id="ACC-UNKNOWN")

        assert f"${DEFAULT_ACCOUNT.balance:.2f}" in result

    def test_uses_default_account_id(self):
        tools = BillingTools()

        result = tools.get_account_balance()

        assert "account default" in result

    def test_balance_is_deterministic(self):
        tools = BillingTools()

        result1 = tools.get_account_balance(account_id="ACC-1003")
        result2 = tools.get_account_balance(account_id="ACC-1003")

        assert result1 == result2
        assert f"${ACCOUNTS['ACC-1003'].balance:.2f}" in result1


class TestGetPaymentMethods:
    def test_returns_accepted_methods(self):
        tools = BillingTools()

        result = tools.get_payment_methods()

        assert "Visa" in result
        assert "MasterCard" in result
        assert "PayPal" in result
        assert "bank transfers" in result


class TestCheckPaymentStatus:
    def test_returns_status_for_known_payment(self):
        tools = BillingTools()

        result = tools.check_payment_status(account_id="ACC-1001", payment_id="PAY-2001")

        assert "PAY-2001" in result
        assert "ACC-1001" in result
        assert "completed" in result

    def test_returns_pending_for_unknown_payment(self):
        tools = BillingTools()

        result = tools.check_payment_status(account_id="ACC-1", payment_id="PAY-UNKNOWN")

        assert "pending" in result

    def test_status_is_deterministic_for_same_payment_id(self):
        tools = BillingTools()

        result1 = tools.check_payment_status(account_id="ACC-1001", payment_id="PAY-2001")
        result2 = tools.check_payment_status(account_id="ACC-1001", payment_id="PAY-2001")

        assert result1 == result2


class TestProcessPayment:
    def test_processes_payment_with_default_method(self):
        tools = BillingTools()

        result = tools.process_payment(amount=99.99)

        assert "$99.99" in result
        assert "credit card" in result
        assert "processed successfully" in result

    def test_processes_payment_with_custom_method(self):
        tools = BillingTools()

        result = tools.process_payment(amount=50.0, method="PayPal")

        assert "$50.00" in result
        assert "PayPal" in result

    def test_formats_amount_with_two_decimals(self):
        tools = BillingTools()

        result = tools.process_payment(amount=10)

        assert "$10.00" in result
