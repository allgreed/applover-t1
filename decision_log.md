# Decisions

- Using synthetic keys, because https://blog.ploeh.dk/2024/06/03/youll-regret-using-natural-keys/
- The case of not borrowing already borrowed book is not authorisation but rather data integrity, therefore I'm implementing it ("Na potrzeby zadania, pomijamy uwierzytelnianie i autoryzację użytkowników.")
- Quality attributes are not of major import *right now* as we don't even know if we're building the right product - the software needs to be evaluatable only
    - I don't bother with indexes, performance, etc.
- I consider postgres password to be acceptable to store in an environment variable at this point
- There's no semantics to an BookLending with a future end date
    -> this should be implemented as a return commitment and then checked against real return date
- I'm not enriely sure what are the semantics of deleting a book -> the book being missing?
    anyway: deleting a book also deletes all records of said book lending
- I'm not bothered by potential weird race conditions, yet I comment on them
- Sometimes I went a bit down the rabbit hole, since I believe that unpaid take-home assignments should be fun. That was fun!
- I'm sacrificing Docker reproducibility and image size for conveniance and delivery time
