import time
import datetime
from typing_extensions import Annotated
from typing import Literal, Union

from fastapi import FastAPI, Depends, status, Response, HTTPException, Path
from pydantic import BaseModel, Field

from .models import Book, DoubleBorrowError
from .db import Database, Db_T , handle_db_errors, UniqueConstraintViolation


app = FastAPI()
@app.get("/")
def default():
    return "OK"


@app.on_event("startup")
def startup():
    # when doing podman-compose up AND the image is built THEN there's a window where
    # postgres passes the healthcheck yet doesn't accept connections yet
    # it's late so I issue the only command I can think of now
    time.sleep(1)

    Database.connect()
    Database.automigrate()


SixDigitStrConstraintStub={"pattern": r"[0-9]{6}"}
SixDigitIdField = Annotated[str, Field(strict=True, **SixDigitStrConstraintStub)]

LibraryCardNumber = SixDigitIdField
BookSerialNumber = SixDigitIdField

class BookBase(BaseModel):
    serial_number: BookSerialNumber
    title: str
    author: str

class BookCreate(BookBase):
    pass

class BookAviable(BookBase):
    is_avaiable: Literal[True]

class BookBorrowed(BookBase):
    is_avaiable: Literal[False]
    borrower_library_card_number: LibraryCardNumber
    borrowed_on: datetime.datetime

BookRead = Union[BookAviable, BookBorrowed]

class Borrow(BaseModel):
    borrower_library_card_number: LibraryCardNumber


@app.get("/books")
def list_books(db = Depends(Database.get_db)) -> list[BookRead]:
    return db.query(Book).all()


@app.delete("/books/{book_serial_number}")
def delete_book(book_serial_number: BookSerialNumber, db = Depends(Database.get_db)) -> None:
    with db.begin():
        # optimization opportunity: this doesn't need to do a full table scan, since the serial number is unique
        # nor does it need actually fetching the book in order to delete it
        db.delete(Book_by_serial_number(db, book_serial_number))

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/books")
def add_book(b: BookCreate, db = Depends(Database.get_db)) -> BookAviable:
    new_book = Book(**b.dict())
    with handle_db_errors([
            UniqueConstraintViolation(loc=["body", "serial_number"]),
        ]):
        with db.begin():
            db.add(new_book)

    return new_book


@app.post("/books/{book_serial_number}/lending")
def borrow_book(b: Borrow, book_serial_number: BookSerialNumber, db = Depends(Database.get_db)) -> BookBorrowed:
    with db.begin():
        # wrapping whole thing in a transaction should be enough, but I'm still not super sure it's race condition free
        book = Book_by_serial_number(db, book_serial_number)

        try:
            book.borrow_by(b.borrower_library_card_number)
        except DoubleBorrowError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Requested book is already borrowed")

        return book


@app.delete("/books/{book_serial_number}/lending")
def return_book(book_serial_number: BookSerialNumber, db = Depends(Database.get_db)):
    # there's a possible race condition if the return request gets send twice, the first request completes
    # the second one gets delayed and someone borrows that book before the second request reaches the server
    # in that case the book would be marked as returned, even though it's not
    # mitigiation: include borrower library card number in the request
    # better mititgation: include BookLending uuid in the request
    with db.begin():
        Book_by_serial_number(db, book_serial_number).return_()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


def Book_by_serial_number(db: Db_T, serial: BookSerialNumber) -> Book:
    result = db.query(Book).filter(Book.serial_number == serial).first()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Book with serial number {serial} was not found")

    return result
