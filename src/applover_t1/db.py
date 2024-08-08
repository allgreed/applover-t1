import os
import re
import sys
from typing import Optional

import psycopg2
from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy import CheckConstraint, Integer, String, create_engine, DateTime, func, ForeignKey
from sqlalchemy import Column as Col
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker, relationship


class Column(Col):
    """
    Becuase the default is "True"
    see: https://stackoverflow.com/a/68052174/9134286
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('nullable', False)
        super().__init__(*args, **kwargs)


def acquire_database_url() -> str:
    ENVVAR = "APP_PGSQL_CONNECTION_STRING"
    try:
        return os.environ[ENVVAR]
    except KeyError:
        print(f"error: Missing environment variable {ENVVAR}", file=sys.stderr)
        exit(1)


SQLALCHEMY_DATABASE_URL = acquire_database_url()
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    query_cache_size=0  # disabling query compilation cache
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def automigrate():
    Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# TODO: where to place this exactly?
def handle_unique_constraint_violation(exc, loc: list[str]):
    """
    Pydantic-like FastAPI-compatbile handler for UniqueViolation

    So: there's an abstraction leakage on the Sqlalchemy level IMO where the errors
    are not properly mapped, nor provide sensible intrsopection mechanism

    This is an attempt to bridge over that gap in one trivial case.
    This is a cry for help.
    """
    if not isinstance(exc.orig, psycopg2.errors.UniqueViolation):
        raise
    exc = exc.orig

    REG = r"""ERROR:  duplicate key value violates unique constraint "books_serial_key"
DETAIL:  Key \((.+)\)=\((.+)\) already exists."""
    assert exc.pgerror, "There is a body to the UniqueViolation"
    match = re.match(REG, exc.pgerror)
    assert match
    key, value = match.groups()

    err = {"detail": [ {
        "type": "unique_constraint",
        # I can't think of a nice and easy way of reliably getting a full loc for an arbitrary request
        # therefore I'm leaving it to be done manually
        "loc": loc + [ key ],
        "msg": "Input should be unique", "input": value,
    } ] }

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=err,
    )
    # TODO: return ValidationError!


class Book(Base):
    __tablename__ = "books"

    # TODO: is this some kind of legacy notation?
    id = Column(Integer, primary_key=True)
    # note: I don't think CheckConstraint is the right solution here and I wouldn't have done it in a production code
    # but a) I wanted to try it out and b) now you know that I know
    # also: I think it's an interesting challange how to keep this constraint in sync between db and the schemas
    serial = Column("serial", Integer, CheckConstraint(f"serial >= 0 AND serial < {'1' + '0' * 6}"), unique=True)
    title = Column(String)
    # note: one book can have many authors
    author = Column(String)

    # I've tried typing it as list[BookLending] which I belive it is
    # or actually a mapping
    # TODO: have a look at this
    # lendings: list["BookLending"] = relationship(
    lendings = relationship(
        "BookLending",
        back_populates="book",
        cascade="all, delete",
    )

    @property
    def is_avaiable(self) -> bool:
        return not bool(self._active_lending)

    @property
    def borrower_library_card_number(self) -> Optional[int]:
        assert self._active_lending, "This is only called on a borrowed book"
        return self._active_lending.borrower_library_card_number

    @property
    def borrowed_on(self):
        assert self._active_lending, "This is only called on a borrowed book"
        return self._active_lending.start

    # becasue Python is *very* fussy with keywords
    def return_(self):
        if self._active_lending:
            self._active_lending.end = func.now()

    def borrow_by(self, borrower_library_card_number: int):
        if not self.is_avaiable:
            raise DoubleBorrowError()

        self.lendings.append(BookLending(borrower_library_card_number=borrower_library_card_number, book_id=self.id))

    @property
    def _active_lending(self) -> Optional["BookLending"]:
        try:
            # optimization opportunity: there might be some N+1 going on here
            # the implementation is very naive

            # this is apparently causing SQLAlchemy to question it's compilation cache cohesion o.0
            # see https://sqlalche.me/e/20/cprf
            return next(filter(lambda L: not L.is_concluded, self.lendings))
        except StopIteration: # no active lending
            return None


class DoubleBorrowError(Exception):
    pass


# this was consulted with a native-speaker-programmer, it's better than "BookLoan"
class BookLending(Base):
    __tablename__ = "book_lendings"

    id = Column(Integer, primary_key=True)

    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"))
    book = relationship("Book", back_populates="lendings")

    borrower_library_card_number = Column(Integer)
    start = Column(DateTime(timezone=True), server_default=func.now())
    end = Column(DateTime(timezone=True), nullable=True)

    @property
    def is_concluded(self) -> bool:
        return bool(self.end)
