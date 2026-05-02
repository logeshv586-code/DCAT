from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL
from models import Base, User, Account, Dealership
from auth import hash_password

# Set up the DB engine and session factory
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# Dependency to get a DB session for FastAPI requests
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize the database and seed it with default data on first run
def init_db():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if we already have users. If yes, skip seeding.
        if db.query(User).count() > 0:
            return

        # Create admin user first
        admin = User(
            username="admin",
            password_hash=hash_password("admin123"),
            role="admin",
        )
        db.add(admin)
        db.flush()  # Get the ID for the admin user

        # Create brand accounts
        tata = Account(name="Tata", slug="tata")
        vw = Account(name="Volkswagen", slug="volkswagen")
        db.add_all([tata, vw])
        db.flush()

        # Add dealerships linked to each brand
        dealers = [
            Dealership(account_id=tata.id, name="Bellad Tata", folder_name="Bellad-tata"),
            Dealership(account_id=vw.id, name="VW Autobahn", folder_name="VW-Autobhan"),
            Dealership(account_id=vw.id, name="VW Hubli (Kumar)", folder_name="VW-Hubli"),
        ]
        db.add_all(dealers)
        db.commit()

        print("[init] Database seeded with admin user, 2 accounts, 3 dealerships.")
    except Exception as e:
        db.rollback()
        print(f"[init] Oh no, seeding failed: {e}")  # TODO: Maybe log this properly later
    finally:
        db.close()

