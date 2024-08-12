curl 'http://127.0.0.1:8000/books'  | jq

curl 'http://127.0.0.1:8000/books' -X POST  -H 'Content-Type: application/json' --data-raw $'{\n  "serial_number": "000001",\n  "title": "a",\n  "author": "b"\n}' | jq
curl 'http://127.0.0.1:8000/books' -X POST   -H 'Content-Type: application/json' --data-raw $'{\n  "serial_number": "000002",\n  "title": "c",\n  "author": "d"\n}' | jq
curl 'http://127.0.0.1:8000/books' -X POST  -H 'Content-Type: application/json' --data-raw $'{\n  "serial_number": "000003",\n  "title": "e",\n  "author": "f"\n}' | jq

curl 'http://127.0.0.1:8000/books/000001/lending' -X POST -H 'Content-Type: application/json' --data-raw $'{\n  "borrower_library_card_number": "000123"\n}' | jq
curl 'http://127.0.0.1:8000/books/000001/lending' -X POST -H 'Content-Type: application/json' --data-raw $'{\n  "borrower_library_card_number": "000123"\n}' | jq
curl 'http://127.0.0.1:8000/books/000002/lending' -X POST -H 'Content-Type: application/json'  --data-raw $'{\n  "borrower_library_card_number": "000123"\n}' | jq
curl 'http://127.0.0.1:8000/books/000003/lending' -X POST -H 'Content-Type: application/json' --data-raw $'{\n  "borrower_library_card_number": "000234"\n}' | jq

curl 'http://127.0.0.1:8000/books/000001/lending' -X DELETE
curl 'http://127.0.0.1:8000/books/000001/lending' -X DELETE
curl 'http://127.0.0.1:8000/books/000015/lending' -X DELETE

curl 'http://127.0.0.1:8000/books/000002' -X DELETE
curl 'http://127.0.0.1:8000/books/000069' -X DELETE

curl 'http://127.0.0.1:8000/books' | jq
