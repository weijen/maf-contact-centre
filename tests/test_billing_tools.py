from unittest.mock import patch

from src.tools.billing_tools import BillingTools


class TestGetAccountBalance:
    def test_returns_balance_for_given_account(self):
        tools = BillingTools()

        with patch("src.tools.billing_tools.randint", return_value=250):
            result = tools.get_account_balance(account_id="ACC-123")

        assert result == "The current balance for account ACC-123 is $250.00."

    def test_uses_default_account_id(self):
        tools = BillingTools()

        with patch("src.tools.billing_tools.randint", return_value=100):
            result = tools.get_account_balance()

        assert result == "The current balance for account default is $100.00."

    def test_balance_is_formatted_with_two_decimals(self):
        tools = BillingTools()

        with patch("src.tools.billing_tools.randint", return_value=50):
            result = tools.get_account_balance(account_id="X")

        assert "$50.00" in result


class TestGetPaymentMethods:
    def test_returns_accepted_methods(self):
        tools = BillingTools()

        result = tools.get_payment_methods()

        assert "Visa" in result
        assert "MasterCard" in result
        assert "PayPal" in result
        assert "bank transfers" in result


class TestCheckPaymentStatus:
    def test_returns_status_for_payment(self):
        tools = BillingTools()

        result = tools.check_payment_status(account_id="ACC-1", payment_id="PAY-42")

        assert "PAY-42" in result
        assert "ACC-1" in result
        assert any(s in result for s in ["completed", "pending", "failed"])

    def test_status_is_deterministic_for_same_payment_id(self):
        tools = BillingTools()

        result1 = tools.check_payment_status(account_id="ACC-1", payment_id="PAY-1")
        result2 = tools.check_payment_status(account_id="ACC-1", payment_id="PAY-1")

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
