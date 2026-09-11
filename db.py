from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

load_dotenv()
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'boveda.db'}")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class AppConfig(Base):
    __tablename__ = "app_config"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    salt_b64: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Bank(Base):
    __tablename__ = "banks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(160), nullable=False)
    branch: Mapped[str] = mapped_column(String(160), default="")
    is_virtual: Mapped[bool] = mapped_column(Boolean, default=False)
    logo_path: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    accounts: Mapped[list["Account"]] = relationship(back_populates="bank", cascade="all, delete-orphan")

class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bank_id: Mapped[int] = mapped_column(ForeignKey("banks.id"), nullable=False)
    account_number_enc: Mapped[str] = mapped_column(Text, nullable=False)
    breb_key_enc: Mapped[str | None] = mapped_column(Text)
    phone_key_enc: Mapped[str | None] = mapped_column(Text)
    withdrawal_pin_enc: Mapped[str | None] = mapped_column(Text)
    bank: Mapped[Bank] = relationship(back_populates="accounts")
    cards: Mapped[list["Card"]] = relationship(back_populates="account", cascade="all, delete-orphan")

class Card(Base):
    __tablename__ = "cards"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    card_type: Mapped[str] = mapped_column(String(40), default="Débito")
    number_enc: Mapped[str] = mapped_column(Text, nullable=False)
    expiry_enc: Mapped[str] = mapped_column(Text, nullable=False)
    cvc_enc: Mapped[str | None] = mapped_column(Text)
    cvc_variable: Mapped[bool] = mapped_column(Boolean, default=False)
    variable_hint_enc: Mapped[str | None] = mapped_column(Text)
    account: Mapped[Account] = relationship(back_populates="cards")


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_config(session: Session) -> AppConfig | None:
    return session.scalar(select(AppConfig).where(AppConfig.id == 1))
