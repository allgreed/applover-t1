import os
import re
import sys

import psycopg2
from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy import CheckConstraint, Integer, String, create_engine
from sqlalchemy import Column as Col
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker


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
    SQLALCHEMY_DATABASE_URL
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
