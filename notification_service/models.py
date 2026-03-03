from sqlalchemy import Column, Integer, String, Text
from database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String, default="sent")  # sent, failed
