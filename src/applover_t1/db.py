import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


def acquire_database_url():
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
