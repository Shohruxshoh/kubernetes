import asyncio
import json
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from aiokafka import AIOKafkaConsumer

import models, schemas, database
from database import get_db, SessionLocal

# Jadvallarni yaratish
models.Base.metadata.create_all(bind=database.engine)

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


# --- KAFKA CONSUMER (Orqa fonda ishlovchi jarayon) ---
async def consume_messages():
    consumer = AIOKafkaConsumer(
        "post_events",  # Post Service xabar tashlaydigan kanal (topic)
        bootstrap_servers=KAFKA_BROKER,
        group_id="view_service_group",  # Kafka qaysi xabar o'qilganini shu guruh orqali eslab qoladi
        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
    )

    await consumer.start()
    try:
        # Xabarlarni cheksiz kutish sikli
        async for msg in consumer:
            data = msg.value

            # Agar xabar turi "post_viewed" bo'lsa
            if data.get("event_type") == "post_viewed":
                post_id = data.get("post_id")

                # Baza bilan ishlash uchun alohida sessiya ochamiz
                db = SessionLocal()
                try:
                    view_record = db.query(models.PostView).filter(models.PostView.post_id == post_id).first()

                    if not view_record:
                        # Agar post birinchi marta ko'rilayotgan bo'lsa, yangi qator yaratamiz
                        view_record = models.PostView(post_id=post_id, view_count=1)
                        db.add(view_record)
                    else:
                        # Oldin ko'rilgan bo'lsa, sonini 1 taga oshiramiz
                        view_record.view_count += 1

                    db.commit()
                finally:
                    db.close()

    finally:
        await consumer.stop()


# --- FASTAPI LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dastur yonganda consumerni orqa fonda (background task) ishga tushiramiz
    task = asyncio.create_task(consume_messages())
    yield
    # Dastur o'chganda taskni to'xtatamiz
    task.cancel()


app = FastAPI(title="View Service", lifespan=lifespan)


# --- API ENDPOINT ---
# Foydalanuvchiga yoki Frontend'ga postning necha marta ko'rilganini qaytarish uchun
@app.get("/views/{post_id}", response_model=schemas.ViewResponse)
def get_post_views(post_id: int, db: Session = Depends(get_db)):
    view_record = db.query(models.PostView).filter(models.PostView.post_id == post_id).first()

    if not view_record:
        # Hali hech kim ko'rmagan bo'lsa, 0 qaytaramiz
        return schemas.ViewResponse(post_id=post_id, view_count=0)

    return view_record
