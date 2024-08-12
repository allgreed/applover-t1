from typing import Optional
from datetime import datetime

from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped

from .db import Base


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    serial_number: Mapped[str] = mapped_column(String(6), unique=True)
    title: Mapped[str]
    # note: one book can have many authors
    author: Mapped[str]

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

    def borrow_by(self, borrower_library_card_number: str):
        if not self.is_avaiable:
            raise DoubleBorrowError()

        self.lendings.append(BookLending(borrower_library_card_number=borrower_library_card_number, book_id=self.id))

    @property
    def _active_lending(self) -> Optional["BookLending"]:
        try:
            # optimization opportunity: there might be some N+1 going on here
            # the implementation is very naive
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

    id: Mapped[int] = mapped_column(primary_key=True)
    borrower_library_card_number: Mapped[str] = mapped_column(String(6))
    start: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"))
    book = relationship("Book", back_populates="lendings")

    @property
    def is_concluded(self) -> bool:
        return bool(self.end)
