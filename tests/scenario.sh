curl 'http://127.0.0.1:8000/books'  | jq

curl 'http://127.0.0.1:8000/books' -X POST  -H 'Content-Type: application/json' --data-raw $'{\n  "serial": 1,\n  "title": "a",\n  "author": "b"\n}' | jq
curl 'http://127.0.0.1:8000/books' -X POST   -H 'Content-Type: application/json' --data-raw $'{\n  "serial": 2,\n  "title": "c",\n  "author": "d"\n}' | jq
curl 'http://127.0.0.1:8000/books' -X POST  -H 'Content-Type: application/json' --data-raw $'{\n  "serial": 3,\n  "title": "e",\n  "author": "f"\n}' | jq

curl 'http://127.0.0.1:8000/books/1/lending' -X POST -H 'Content-Type: application/json' --data-raw $'{\n  "borrower_library_card_number": 123\n}' | jq
curl 'http://127.0.0.1:8000/books/1/lending' -X POST -H 'Content-Type: application/json' --data-raw $'{\n  "borrower_library_card_number": 123\n}' | jq
curl 'http://127.0.0.1:8000/books/2/lending' -X POST -H 'Content-Type: application/json'  --data-raw $'{\n  "borrower_library_card_number": 123\n}' | jq
curl 'http://127.0.0.1:8000/books/3/lending' -X POST -H 'Content-Type: application/json' --data-raw $'{\n  "borrower_library_card_number": 234\n}' | jq

curl 'http://127.0.0.1:8000/books/1/lending' -X DELETE
curl 'http://127.0.0.1:8000/books/1/lending' -X DELETE
curl 'http://127.0.0.1:8000/books/15/lending' -X DELETE

curl 'http://127.0.0.1:8000/books/2' -X DELETE
curl 'http://127.0.0.1:8000/books/69' -X DELETE

curl 'http://127.0.0.1:8000/books' | jq
