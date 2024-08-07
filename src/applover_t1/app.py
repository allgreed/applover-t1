from typing_extensions import Annotated

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from .db import get_db, automigrate, Book


app = FastAPI()
automigrate()


# TODO: where to keep this?
class BookSchema(BaseModel):
    serial: Annotated[int, Field(strict=True, gte=1, lte=10 ** 6 - 1)]
    title: str
    author: str

    # TODO: is this needed?
    # class Config:
        # orm_mode = True

# TODO: is there a sensible action on root?
@app.get("/")
def read_root():
    return {"Hello": "sup?"}


# TODO: I'm not super happy about the Session type being here
@app.post("/books")
def add_book(book: BookSchema, db: Session = Depends(get_db)) -> BookSchema:
    # TODO: rename, refactor
    db_user = Book(**book.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # TODO: bubble down db errors
    return db_user
    ...


# TODO: restart on postgres failure?
# TODO: test all with `docker-compsoe up`

