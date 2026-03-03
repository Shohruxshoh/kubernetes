from sqlalchemy import Column, Integer
from database import Base


class PostView(Base):
    __tablename__ = "post_views"

    # Bu yerda post_id ni asosiy kalit qilib olamiz, chunki 1 ta postga 1 ta qator kerak
    post_id = Column(Integer, primary_key=True, index=True)
    view_count = Column(Integer, default=0)
