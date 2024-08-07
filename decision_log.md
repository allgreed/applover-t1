# Decisions

- I implement the "sześciocyfrowej liczby" as a number that has six digits, where digit can be `0`, so:
    - `000001` is valid
    - this is trivially reversible
- Using synthetic keys, because https://blog.ploeh.dk/2024/06/03/youll-regret-using-natural-keys/
- The case of not borrowing already borrowed book is not authorisation but rather data integrity, therefore I'm implementing it ("Na potrzeby zadania, pomijamy uwierzytelnianie i autoryzację użytkowników.")
- Quality attributes are not of major import *right now* as we don't even know if we're building the right product - the software needs to be evaluatable only
    - I don't bother with indexes, performance, etc.
- I consider postgres password to be acceptable to store in an environment variable at this point
