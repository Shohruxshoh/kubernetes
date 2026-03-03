from pydantic import BaseModel


class PostCreate(BaseModel):
    title: str
    content: str
    author_id: int


class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    author_id: int

    class Config:
        from_attributes = True
