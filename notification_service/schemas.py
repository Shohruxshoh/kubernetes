from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    post_id: int
    message: str
    status: str

    class Config:
        from_attributes = True
