"""SQLAlchemy models.

No raw statement file is ever stored here (rule 4) - these tables only
ever receive already-parsed rows from app/parsers and app/categorize.

UUID primary keys throughout: sequential integer IDs in a finance app's
URLs (/accounts/123) make other users' resource IDs trivially guessable.

Money is integer paise everywhere (rule 1). `date` columns are plain
calendar dates with no timezone (that's what a statement actually prints);
`created_at` is timezone-aware UTC (rule 2) and generated in Python rather
than left to the database's `now()`, so it doesn't depend on session
timezone configuration.
"""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clerk_user_id: Mapped[str] = mapped_column(unique=True)
    preferred_llm_provider: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    accounts: Mapped[list["Account"]] = relationship(back_populates="user")


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str]  # 'bank' | 'credit_card'
    institution: Mapped[str]
    product: Mapped[str | None] = mapped_column(default=None)  # card product name; null for bank
    account_number_masked: Mapped[str]
    ifsc: Mapped[str | None] = mapped_column(default=None)  # bank only
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped["User"] = relationship(back_populates="accounts")
    statements: Mapped[list["Statement"]] = relationship(back_populates="account")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")


class Statement(Base):
    __tablename__ = "statements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"))
    period_from: Mapped[date]
    period_to: Mapped[date]
    opening_balance_paise: Mapped[int]
    closing_balance_paise: Mapped[int]
    reconciled: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    account: Mapped["Account"] = relationship(back_populates="statements")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="statement")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        # CLAUDE.md dedup rule: (account_id, date, amount, normalised_description).
        # Keyed on narration (raw text), not merchant - merchant is null for EMI
        # rows, so two same-day same-amount EMIs would otherwise collide.
        UniqueConstraint("account_id", "date", "amount_paise", "narration", name="uq_transaction_dedup"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"))
    statement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("statements.id"))
    date: Mapped[date]
    narration: Mapped[str]
    merchant: Mapped[str | None] = mapped_column(default=None)
    category: Mapped[str | None] = mapped_column(default=None)
    direction: Mapped[str]  # 'debit' | 'credit'
    amount_paise: Mapped[int]
    balance_after_paise: Mapped[int | None] = mapped_column(default=None)  # bank only
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    account: Mapped["Account"] = relationship(back_populates="transactions")
    statement: Mapped["Statement"] = relationship(back_populates="transactions")
