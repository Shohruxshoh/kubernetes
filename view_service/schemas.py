from pydantic import BaseModel


class ViewResponse(BaseModel):
    post_id: int
    view_count: int

    class Config:
        from_attributes = True
