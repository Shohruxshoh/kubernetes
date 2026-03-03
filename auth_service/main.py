import os
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import bcrypt  # <--- PASSLIB O'RNIGA BCRYPT QO'SHILDI
from jose import jwt
from datetime import datetime, timedelta

import models, schemas, database
from database import get_db

# Baza jadvallarini yaratish
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Professional Auth Service")


# --- XAVFSIZLIK SOZLAMALARI ---
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "super_maxfiy_kalit_soz_prod_uchun_boshqa_boladi"
)
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv(
    "ACCESS_TOKEN_EXPIRE_MINUTES", 30)
# PWD_CONTEXT QATORI BUTUNLAY OLIB TASHLANDI

# --- YANGILANGAN YORDAMCHI FUNKSIYALAR ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Parollarni solishtirish uchun ularni bayt (byte) formatiga o'tkazish kerak
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

def get_password_hash(password: str) -> str:
    # Yangi parolni shifrlash
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_bytes.decode('utf-8') # Bazaga matn qilib saqlash uchun

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- API ENDPOINTLAR ---

@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Bazada bunday foydalanuvchi bor-yo'qligini tekshirish
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username band")

    # Yangi foydalanuvchini bazaga saqlash
    hashed_password = get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login", response_model=schemas.Token)
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username yoki parol noto'g'ri"
        )

    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}
