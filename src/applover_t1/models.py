from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from .db import Base, Column


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    # note: I don't think CheckConstraint is the right solution here and I wouldn't have done it in a production code
    # but a) I wanted to try it out and b) now you know that I know
    # also: I think it's an interesting challange how to keep this constraint in sync between db and the schemas
    serial = Column("serial", Integer, CheckConstraint(f"serial >= 0 AND serial < {'1' + '0' * 6}"), unique=True)
    title = Column(String)
    # note: one book can have many authors
    author = Column(String)

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
            result: BookLending = next(filter(lambda L: not L.is_concluded, self.lendings))
            # this type assert is needed becasue otherwise L is of type "BookLending | None" and errors on member access
            return result
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
