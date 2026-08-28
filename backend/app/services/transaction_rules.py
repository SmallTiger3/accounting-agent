from decimal import Decimal
from typing import Tuple


VALID_TRANSACTION_TYPES = {"income", "expense", "transfer"}


def validate_transaction_type(transaction_type: str) -> None:
    if transaction_type not in VALID_TRANSACTION_TYPES:
        raise ValueError(f"Unsupported transaction type: {transaction_type}")


def get_balance_deltas(
    amount: Decimal,
    transaction_type: str,
    is_source: bool = True,
) -> Tuple[Decimal, Decimal]:
    validate_transaction_type(transaction_type)
    if transaction_type == "income":
        return amount, Decimal("0")
    if transaction_type == "expense":
        return -amount, Decimal("0")
    if transaction_type == "transfer":
        return (-amount, Decimal("0")) if is_source else (Decimal("0"), amount)
