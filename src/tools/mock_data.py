"""Stable mock data for tool functions.

Tools use this module instead of random values so that every call with the same
arguments returns the same result — making demos, tests, and development
predictable.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MockUser:
    user_id: str
    name: str
    email: str


@dataclass(frozen=True)
class MockAccount:
    account_id: str
    user_id: str
    balance: float
    currency: str = "USD"


@dataclass(frozen=True)
class MockPayment:
    payment_id: str
    account_id: str
    amount: float
    status: str
    method: str


@dataclass(frozen=True)
class MockTicket:
    ticket_id: str
    user_id: str
    issue_summary: str
    status: str


# ── Users ────────────────────────────────────────────────────────────────────

USERS: dict[str, MockUser] = {
    "USR-001": MockUser(user_id="USR-001", name="Alice Chen", email="alice.chen@example.com"),
    "USR-002": MockUser(user_id="USR-002", name="Bob Martinez", email="bob.martinez@example.com"),
    "USR-003": MockUser(user_id="USR-003", name="Carol Wang", email="carol.wang@example.com"),
    "USR-004": MockUser(user_id="USR-004", name="David Kim", email="david.kim@example.com"),
    "USR-005": MockUser(user_id="USR-005", name="Eve Johnson", email="eve.johnson@example.com"),
}

DEFAULT_USER = USERS["USR-001"]

# ── Accounts ─────────────────────────────────────────────────────────────────

ACCOUNTS: dict[str, MockAccount] = {
    "ACC-1001": MockAccount(account_id="ACC-1001", user_id="USR-001", balance=245.50),
    "ACC-1002": MockAccount(account_id="ACC-1002", user_id="USR-002", balance=1_320.00),
    "ACC-1003": MockAccount(account_id="ACC-1003", user_id="USR-003", balance=78.25),
    "ACC-1004": MockAccount(account_id="ACC-1004", user_id="USR-004", balance=0.00),
    "ACC-1005": MockAccount(account_id="ACC-1005", user_id="USR-005", balance=530.99),
}

DEFAULT_ACCOUNT = ACCOUNTS["ACC-1001"]

# ── Payments ─────────────────────────────────────────────────────────────────

PAYMENTS: dict[str, MockPayment] = {
    "PAY-2001": MockPayment(
        payment_id="PAY-2001", account_id="ACC-1001", amount=49.99, status="completed", method="credit card",
    ),
    "PAY-2002": MockPayment(
        payment_id="PAY-2002", account_id="ACC-1002", amount=150.00, status="pending", method="bank transfer",
    ),
    "PAY-2003": MockPayment(
        payment_id="PAY-2003", account_id="ACC-1003", amount=25.00, status="failed", method="PayPal",
    ),
    "PAY-2004": MockPayment(
        payment_id="PAY-2004", account_id="ACC-1004", amount=300.00, status="completed", method="credit card",
    ),
    "PAY-2005": MockPayment(
        payment_id="PAY-2005", account_id="ACC-1005", amount=89.50, status="pending", method="credit card",
    ),
}

# ── Support tickets ──────────────────────────────────────────────────────────

TICKETS: dict[str, MockTicket] = {
    "TKT-30001": MockTicket(
        ticket_id="TKT-30001", user_id="USR-001", issue_summary="Cannot login to account", status="open",
    ),
    "TKT-30002": MockTicket(
        ticket_id="TKT-30002", user_id="USR-002", issue_summary="Slow page load times", status="in_progress",
    ),
    "TKT-30003": MockTicket(
        ticket_id="TKT-30003", user_id="USR-003", issue_summary="Payment not reflected", status="open",
    ),
    "TKT-30004": MockTicket(
        ticket_id="TKT-30004", user_id="USR-004", issue_summary="Feature request: dark mode", status="closed",
    ),
    "TKT-30005": MockTicket(
        ticket_id="TKT-30005", user_id="USR-005", issue_summary="Email notifications not received", status="open",
    ),
}

# Auto-incrementing ticket counter for new tickets
_next_ticket_number = 30006


def next_ticket_id() -> str:
    """Return a stable, incrementing ticket ID for newly created tickets."""
    global _next_ticket_number  # noqa: PLW0603
    tid = f"TKT-{_next_ticket_number}"
    _next_ticket_number += 1
    return tid


# ── System status ────────────────────────────────────────────────────────────

SYSTEM_STATUS = "All systems operational"

# ── Troubleshooting guides ───────────────────────────────────────────────────

TROUBLESHOOTING_STEPS: dict[str, str] = {
    "connectivity": "1. Check your internet connection. 2. Restart your router. 3. Clear browser cache.",
    "login": "1. Verify your username and password. 2. Check caps lock. 3. Try password reset.",
    "performance": "1. Close unused applications. 2. Clear temporary files. 3. Restart your device.",
}

TROUBLESHOOTING_FALLBACK = "Please describe your issue in more detail."

# ── Payment methods info ─────────────────────────────────────────────────────

ACCEPTED_PAYMENT_METHODS = (
    "We accept credit cards (Visa, MasterCard, American Express), bank transfers, and PayPal."
)
