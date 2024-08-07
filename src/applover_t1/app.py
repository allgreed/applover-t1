from typing_extensions import Annotated

from fastapi import FastAPI, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

from .db import get_db, automigrate, Book, handle_unique_constraint_violation


app = FastAPI()
automigrate()
@app.get("/")
def default():
    return "OK"


BookSerial = Annotated[int, Field(strict=True, ge=0, le=10 ** 6 - 1)]
class BookSchema(BaseModel):
    serial: BookSerial
    title: str
    author: str

    # TODO: is this needed?
    # class Config:
        # orm_mode = True


@app.get("/books")
def list_books(db = Depends(get_db)) -> list[BookSchema]:
    return db.query(Book).all()


@app.delete("/books/{book_serial}")
def delete_book(book_serial: BookSerial, db = Depends(get_db)) -> None:
    with db.begin():
        # optimization opportunity: this doesn't need to do a full table scan, since the serial is unique
        db.query(Book).filter(Book.serial == book_serial).delete()


@app.post("/books")
def add_book(b: BookSchema, db = Depends(get_db)) -> BookSchema:
    new_book = Book(**b.dict())
    try:
        with db.begin():
            db.add(new_book)
    except IntegrityError as e:
        handle_unique_constraint_violation(e, loc=["body"])

    return new_book


# TODO: what about the SQLalchemy warrning?
# TODO: restart on postgres failure?
# TODO: test all with `docker-compsoe up`
