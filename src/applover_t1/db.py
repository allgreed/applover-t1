import os
import sys

from sqlalchemy import create_engine, Column as Col, Integer, String, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session


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
