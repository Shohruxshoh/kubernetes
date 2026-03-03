from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

SQLALCHEMY_DATABASE_URL = os.getenv("POST_DB_URL", "postgresql://postgres:admin123@localhost:5432/post_db")

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_size=50,
                       # Bir vaqtning o'zida doimiy ochiq turadigan ulanishlar (stollar)
                       max_overflow=100,  # Mijoz ko'payib ketsa, vaqtincha ochiladigan qo'shimcha ulanishlar
                       pool_timeout=60  # Ulanish kutish vaqtini 30 soniyadan 60 soniyaga oshiramiz
                       )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
