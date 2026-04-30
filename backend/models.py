from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), default="admin")
    created_at = Column(DateTime, default=datetime.utcnow)

    creatives = relationship("GeneratedCreative", back_populates="user")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(50), unique=True, nullable=False)

    dealerships = relationship("Dealership", back_populates="account")


class Dealership(Base):
    __tablename__ = "dealerships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    name = Column(String(150), nullable=False)
    folder_name = Column(String(100), nullable=False)  # actual folder under the brand

    account = relationship("Account", back_populates="dealerships")
    creatives = relationship("GeneratedCreative", back_populates="dealership")


class GeneratedCreative(Base):
    __tablename__ = "generated_creatives"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dealership_id = Column(Integer, ForeignKey("dealerships.id"), nullable=False)
    bg_filename = Column(String(255))
    output_filename = Column(String(255))
    format_label = Column(String(30))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="creatives")
    dealership = relationship("Dealership", back_populates="creatives")
