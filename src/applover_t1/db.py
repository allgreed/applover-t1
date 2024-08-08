import contextlib
import os
import re
import sys
from dataclasses import dataclass

import psycopg2
from fastapi import status, HTTPException
from sqlalchemy import Column as Col
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker


# TODO: global cache?
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
Db_T = Session
def get_db() -> Db_T:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextlib.contextmanager
def handle_db_errors(all_handlers):
    try:
        yield
    except IntegrityError as e:
        if not isinstance(e.orig, psycopg2.errors.UniqueViolation):
            raise

        # we only handle Postgres UniqueViolations for now
        handlers = list(filter(lambda h: isinstance(h, UniqueConstraintViolation), all_handlers))

        if not handlers:
            raise

        exc = e.orig
        # I'd love to know a better way if there is one
        # also: careful with the regex, the second line has to have no ident
        REG = r"""ERROR:  duplicate key value violates unique constraint "books_serial_key"
DETAIL:  Key \((.+)\)=\((.+)\) already exists."""
        assert exc.pgerror, "There is a body to the UniqueViolation"
        match = re.match(REG, exc.pgerror)
        assert match
        key, value = match.groups()

        for h in handlers:
            # I can't think of a nice and easy way of reliably getting a full loc for an arbitrary request
            # therefore I'm leaving it to be done manually by user ordering
            # interesting case: field "a" being on multiple nested levels of a model
            # idea: maybe table name could be used to map between View entity and ORM entity?
            if h.loc[-1] == key:
                break
        else:
            raise

        # I've tried putting this into an Pydantic ValidationError
        # believe me, I tried - it'd take some more time to do it properly
        err = {
            "type": "unique_constraint",
            "loc": h.loc,
            "msg": "Input should be unique", "input": value,
        } 
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=err,
        )


@dataclass
class UniqueConstraintViolation:
    loc: list[str]


class Column(Col):
    """
    Becuase the default is "True"
    see: https://stackoverflow.com/a/68052174/9134286
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('nullable', False)
        super().__init__(*args, **kwargs)
Base = declarative_base()


def automigrate():
    Base.metadata.create_all(bind=engine)
