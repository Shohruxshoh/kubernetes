from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Docker orqali ulanish uchun muhit o'zgaruvchisi (Environment Variable)
# Agar topilmasa, lokal holatda ulanadi
SQLALCHEMY_DATABASE_URL = os.getenv(
    "AUTH_DB_URL",
    "postgresql://postgres:admin123@localhost:5432/auth_db"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL,
                       pool_size=50,
                       max_overflow=100, pool_timeout=60)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Bazaga ulanishni ochish va yopish uchun yordamchi funksiya
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
