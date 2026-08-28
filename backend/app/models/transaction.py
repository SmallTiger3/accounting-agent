from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Numeric, Date, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.session import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    transfer_account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)  # income, expense, transfer
    description: Mapped[str] = mapped_column(Text, nullable=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    tags: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array of tags
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    account = relationship("Account", back_populates="transactions", foreign_keys=[account_id])
    transfer_account = relationship(
        "Account", back_populates="transfer_transactions", foreign_keys=[transfer_account_id]
    )
    category = relationship("Category", back_populates="transactions")
