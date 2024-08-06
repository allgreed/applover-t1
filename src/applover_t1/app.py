from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from .db import SessionLocal


app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1"))
    return {"Hello": result.all()[0][0]}

# TODO: `test all with docker-compsoe up`
