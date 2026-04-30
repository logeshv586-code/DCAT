from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models import Base, User, Account, Dealership
from auth import hash_password

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create tables and seed with initial data if the db is fresh."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # only seed if no users exist yet
        if db.query(User).count() > 0:
            return

        # --- admin user ---
        admin = User(
            username="admin",
            password_hash=hash_password("admin123"),
            role="admin",
        )
        db.add(admin)
        db.flush()

        # --- accounts (brands) ---
        tata = Account(name="Tata", slug="tata")
        vw = Account(name="Volkswagen", slug="volkswagen")
        db.add_all([tata, vw])
        db.flush()

        # --- dealerships ---
        dealers = [
            Dealership(account_id=tata.id, name="Bellad Tata", folder_name="Bellad-tata"),
            Dealership(account_id=vw.id, name="VW Autobahn", folder_name="VW-Autobhan"),
            Dealership(account_id=vw.id, name="VW Hubli (Kumar)", folder_name="VW-Hubli"),
        ]
        db.add_all(dealers)
        db.commit()
        print("[init] Database seeded with admin user, 2 accounts, 3 dealerships.")
    except Exception as exc:
        db.rollback()
        print(f"[init] Seed failed: {exc}")
    finally:
        db.close()
