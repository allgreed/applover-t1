import datetime
from typing_extensions import Annotated
from typing import Literal, Union

from fastapi import FastAPI, Depends, status, Response, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

from .db import get_db, automigrate, Book, handle_unique_constraint_violation, BookLending


app = FastAPI()
automigrate()
@app.get("/")
def default():
    return "OK"


SixDigitId = Annotated[int, Field(strict=True, ge=0, le=10 ** 6 - 1)]

LibraryCardNumber = SixDigitId
BookSerial = SixDigitId

class BookBase(BaseModel):
    serial: BookSerial
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
def list_books(db = Depends(get_db)) -> list[BookRead]:
    return db.query(Book).all()

# TODO: what with the type and does it belong here?
# def Book_by_serial(db: Session, serial: BookSerial):
def Book_by_serial(db, serial: BookSerial) -> Book:
    result = db.query(Book).filter(Book.serial == serial).first()

    if not result:
        raise HTTPException(status_code=404, detail=f"Book with serial {serial} was not found")
    else:
        return result


@app.delete("/books/{book_serial}")
def delete_book(book_serial: int, db = Depends(get_db)) -> None:
    with db.begin():
        # optimization opportunity: this doesn't need to do a full table scan, since the serial is unique
        Book_by_serial(db, book_serial).delete()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/books")
def add_book(b: BookCreate, db = Depends(get_db)) -> BookAviable:
    new_book = Book(**b.dict())
    try:
        with db.begin():
            db.add(new_book)
    except IntegrityError as e:
        handle_unique_constraint_violation(e, loc=["body"])

    return new_book



# TODO: what's with the book serial actual type <
@app.post("/books/{book_serial}/lending")
def borrow_book(b: Borrow, book_serial: int, db = Depends(get_db)) -> BookBorrowed:
    with db.begin():
        # wrapping whole thing in a transaction should be enough, but I'm still not super sure it's race condition free

        book = Book_by_serial(db, book_serial)

        # TODO: handle this as an error
        assert book.is_avaiable

        # TODO: isn't this too low level?
        new_lending = BookLending(**b.dict(), book_id=book.id)
        db.add(new_lending)

        return book


@app.delete("/books/{book_serial}/lending")
def return_book(book_serial: int, db = Depends(get_db)):
    # there's a possible race condition if the return request gets send twice, the first request completes
    # the second one gets delayed and someone borrows that book before the second request reaches the sever
    # in that case the book would be marked as returned, even though it's not
    # mitigiation: include borrower library card number in the request
    # better mititgation: include BookLending uuid in the request
    with db.begin():
        Book_by_serial(db, book_serial).return_()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# TODO: what about the SQLalchemy warrning?
