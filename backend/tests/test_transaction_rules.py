from decimal import Decimal

import pytest

from app.services.transaction_rules import get_balance_deltas, validate_transaction_type


def test_income_increases_source_account():
    assert get_balance_deltas(Decimal("10.50"), "income") == (Decimal("10.50"), Decimal("0"))


def test_expense_decreases_source_account():
    assert get_balance_deltas(Decimal("10.50"), "expense") == (Decimal("-10.50"), Decimal("0"))


def test_transfer_decreases_source_account_and_increases_destination_account():
    assert get_balance_deltas(Decimal("10.50"), "transfer") == (Decimal("-10.50"), Decimal("0"))
    assert get_balance_deltas(Decimal("10.50"), "transfer", is_source=False) == (
        Decimal("0"), Decimal("10.50")
    )


def test_unknown_transaction_type_is_rejected():
    with pytest.raises(ValueError):
        get_balance_deltas(Decimal("1"), "unknown")


def test_transaction_type_validation_rejects_unknown_values():
    validate_transaction_type("income")
    validate_transaction_type("expense")
    validate_transaction_type("transfer")
    with pytest.raises(ValueError):
        validate_transaction_type("refund")
