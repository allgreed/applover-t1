import datetime
from typing import Optional
from typing_extensions import Annotated

from fastapi import FastAPI, Depends, status, Response
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

from .db import get_db, automigrate, Book, handle_unique_constraint_violation, BookLending


app = FastAPI()
automigrate()
@app.get("/")
def default():
    return "OK"


SixDigitId = Annotated[int, Field(strict=True, ge=0, le=10 ** 6 - 1)]
BookSerial = SixDigitId
class BookBase(BaseModel):
    serial: BookSerial
    title: str
    author: str

class BookCreate(BookBase):
    pass

class BookRead(BookBase):
    is_avaiable: bool


LibraryCardNumber = SixDigitId
class BookLendingBase(BaseModel):
    borrower_library_card_number: LibraryCardNumber

class BookLendingCreate(BookLendingBase):
    pass

class BookLendingRead(BookLendingBase):
    book: BookRead
    start: datetime.datetime
    end: Optional[datetime.datetime]


@app.get("/books")
def list_books(db = Depends(get_db)) -> list[BookRead]:
    return db.query(Book).all()


@app.delete("/books/{book_serial}")
def delete_book(book_serial: int, db = Depends(get_db)) -> None:
    with db.begin():
        # optimization opportunity: this doesn't need to do a full table scan, since the serial is unique
        db.query(Book).filter(Book.serial == book_serial).delete()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/books")
def add_book(b: BookCreate, db = Depends(get_db)) -> BookRead:
    new_book = Book(**b.dict())
    try:
        with db.begin():
            db.add(new_book)
    except IntegrityError as e:
        handle_unique_constraint_violation(e, loc=["body"])

    return new_book



# TODO: what's with the book serial actual type <
@app.post("/books/{book_serial}/lending")
def borrow_book(b: BookLendingCreate, book_serial: int, db = Depends(get_db)) -> BookLendingRead:
    print(type(book_serial))
    print("aaa")
    with db.begin():
        # wrapping whole thing in a transaction should be enough, but I'm still not super sure it's race condition free

        # TODO: is this duplication of the filter statement? Yes, there is!
        # TODO: what if there's no book?
        book = db.query(Book).filter(Book.serial == book_serial).first()
        # TODO: handle this as an error
        # assert book.is_avaiable

        new_lending = BookLending(**b.dict(), book_id=book.id)
        db.add(new_lending)

        return new_lending


@app.delete("/books/{book_serial}/lending")
def return_book(book_serial: int, db = Depends(get_db)):
    # there's a possible race condition if the return request gets send twice, the first request completes
    # the second one gets delayed and someone borrows that book before the second request reaches the sever
    # in that case the book would be marked as returned, even though it's not
    # mitigiation: include borrower library card number in the request
    # better mititgation: include BookLending uuid in the request
    with db.begin():
        book = db.query(Book).filter(Book.serial == book_serial).first()
        # TODO: pipe the abstraction into the model
        try:
            active_lending =  next(filter(lambda L: not L.is_book_returned, book.lendings))
        except StopIteration: # no active lending
            # TODO: deal with the duplication
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        from sqlalchemy import func
        active_lending.end = func.now()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# TODO: what about the SQLalchemy warrning?
# TODO: restart on postgres failure?
# TODO: test all with `docker-compsoe up`
# TODO: link decision log to README
