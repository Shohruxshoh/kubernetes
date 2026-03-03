import asyncio
import json
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from aiokafka import AIOKafkaProducer
from jose import JWTError, jwt
import redis.asyncio as aioredis  # Redis kutubxonasi
import models, schemas, database
from database import get_db

models.Base.metadata.create_all(bind=database.engine)

# --- KAFKA PRODUCER SOZLAMALARI ---
KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
producer = None


def json_serializer(data):
    return json.dumps(data).encode("utf-8")


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global producer, redis_client

    # Kafka ishga tushadi
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=json_serializer
    )
    await producer.start()

    # Redis ishga tushadi
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

    yield

    await producer.stop()
    await redis_client.close()

app = FastAPI(title="Post Service (Secured)", lifespan=lifespan)

# ==========================================
# XAVFSIZLIK (JWT TOKEN TEKSHIRISH) QISMI
# ==========================================
SECRET_KEY = os.getenv("SECRET_KEY", "super_maxfiy_kalit_soz_prod_uchun_boshqa_boladi")
ALGORITHM = "HS256"

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # HTTPBearer tokenni "credentials.credentials" ichida qaytaradi
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token yaroqsiz yoki ruxsat yo'q",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Tokenni ochib ko'ramiz
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception


# ==========================================
# API ENDPOINTLAR
# ==========================================

# E'tibor bering: current_user parametri qo'shildi! Bu tokenni talab qiladi.
@app.post("/posts/", response_model=schemas.PostResponse)
async def create_post(
        post: schemas.PostCreate,
        db: Session = Depends(get_db),
        current_user: str = Depends(get_current_user)  # <- TOKEN SHU YERDA TEKSHIRILADI
):
    new_post = models.Post(
        title=post.title,
        content=post.content,
        author_id=post.author_id
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    # Kafka'ga asinxron xabar yuboramiz
    event_data = {
        "event_type": "post_created",
        "post_id": new_post.id,
        "title": new_post.title,
        "author_id": new_post.author_id,
        "author_username": current_user  # Token orqali aniqlangan usernameni ham qo'shib yuboramiz
    }

    await producer.send_and_wait("post_events", value=event_data)

    return new_post


@app.get("/posts/{post_id}", response_model=schemas.PostResponse)
async def get_post(post_id: int, db: Session = Depends(get_db)):
    # 1. Avval Redis'dan (Keshdan) qidiramiz
    cached_post = await redis_client.get(f"post:{post_id}")

    if cached_post:
        # Agar keshda bo'lsa, matnni JSON qilib o'qiymiz
        post_data = json.loads(cached_post)
    else:
        # 2. Agar Keshda yo'q bo'lsa, Postgres bazadan olamiz
        post = db.query(models.Post).filter(models.Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post topilmadi")

        post_data = {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "author_id": post.author_id
        }

        # 3. Keyingi so'rovlar uchun Redis'ga 60 soniyaga saqlab qo'yamiz
        await redis_client.set(f"post:{post_id}", json.dumps(post_data), ex=70)

    # MUHIM: Post keshdan olingan bo'lsa ham, Kafka'ga baribir xabar yuboramiz!
    # Aks holda Views oshmay qoladi
    view_event_data = {
        "event_type": "post_viewed",
        "post_id": post_id
    }
    await producer.send_and_wait("post_events", value=view_event_data)

    return post_data