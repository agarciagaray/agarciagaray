from pathlib import Path

from db import Account, Bank, Card, SessionLocal, init_db
from security import decrypt, encrypt, new_key_material


def test_crypto_roundtrip():
    km = new_key_material("Contraseña fuerte de prueba")
    token = encrypt("123456789", km.key)
    assert decrypt(token, km.key) == "123456789"


def test_database_roundtrip(tmp_path, monkeypatch):
    # La validación principal se ejecuta contra SQLite de prueba sin depender de MariaDB.
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import db
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    db.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    km = new_key_material("Contraseña fuerte de prueba")
    with Session.begin() as s:
        bank = Bank(name="Banco Test", owner_name="Persona Test", branch="Centro")
        s.add(bank); s.flush()
        s.add(Account(bank_id=bank.id, account_number_enc=encrypt("000123", km.key)))
    with Session() as s:
        account = s.query(Account).one()
        assert decrypt(account.account_number_enc, km.key) == "000123"
