import asyncio
import json
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from aiokafka import AIOKafkaConsumer

import models, schemas, database
from database import get_db, SessionLocal

# Jadvallarni yaratish
models.Base.metadata.create_all(bind=database.engine)

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


# --- KAFKA CONSUMER ---
async def consume_messages():
    consumer = AIOKafkaConsumer(
        "post_events",
        bootstrap_servers=KAFKA_BROKER,
        group_id="notification_service_group",  # VIEW SERVICE'DAN FARQLI GURUH!
        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
    )

    await consumer.start()
    try:
        async for msg in consumer:
            data = msg.value

            # Faqat "post_created" hodisasiga reaksiya bildiramiz
            if data.get("event_type") == "post_created":
                post_id = data.get("post_id")
                title = data.get("title")
                author_id = data.get("author_id")

                # Bu yerda amalda Email yuborish (SMTP) mantiqi bo'ladi.
                # Hozircha biz bazaga "jo'natildi" deb yozib qo'yamiz.
                notif_msg = f"Foydalanuvchi {author_id} yangi post yozdi: '{title}'"
                print(f"[XABAR YUBORILDI] {notif_msg}")  # Terminalda ko'rish uchun

                db = SessionLocal()
                try:
                    new_notif = models.Notification(
                        post_id=post_id,
                        message=notif_msg,
                        status="sent"
                    )
                    db.add(new_notif)
                    db.commit()
                finally:
                    db.close()

    finally:
        await consumer.stop()


# --- FASTAPI LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(consume_messages())
    yield
    task.cancel()


app = FastAPI(title="Notification Service", lifespan=lifespan)


# --- API ENDPOINT ---
# Oxirgi bildirishnomalarni ko'rish uchun
@app.get("/notifications/", response_model=list[schemas.NotificationResponse])
def get_notifications(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    notifs = db.query(models.Notification).order_by(models.Notification.id.desc()).offset(skip).limit(limit).all()
    return notifs
