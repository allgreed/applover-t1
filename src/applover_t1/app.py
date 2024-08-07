from typing_extensions import Annotated

from fastapi import FastAPI, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .db import get_db, automigrate, Book


app = FastAPI()
automigrate()
@app.get("/")
def default():
    return "OK"


# TODO: move it to db
# TODO: apply where approperiate
import re
from sqlalchemy.exc import IntegrityError
import psycopg2
@app.exception_handler(IntegrityError)
def unique_constraint_violation_handler(request, exc):
    if not isinstance(exc.orig, psycopg2.errors.UniqueViolation):
        raise
    exc = exc.orig

    REG = r"""ERROR:  duplicate key value violates unique constraint "books_serial_key"
DETAIL:  Key \((.+)\)=\((.+)\) already exists."""
    key, value = re.match(REG, exc.pgerror).groups()

    # TODO: mimic the style of pydantic - use key and value!
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Integrity error occurred. Possibly a unique constraint violation."}
    )


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
    with db.begin():
        db.add(new_book)

    # TODO: bubble down db errors
    return new_book


# TODO: what about the SQLalchemy warrning?
# TODO: restart on postgres failure?
# TODO: test all with `docker-compsoe up`
