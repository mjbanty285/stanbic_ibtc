## Stabic Ibtc

stanbic ibtc is a banking prototype, but currently built with html and css, 

## feature to be implemented
- improve ui to maintain consistency and mobile ui focus
- using tailwindcss, add tailwind play cdn
- using javascript to make the page interactive
- and use django to setup basic autentication using sqlite and convert html into django template, using extend and inheritance and sub compoennt


## reminder
focus on prototype, and all transaction such as sending money, buying data and more should stop at processing, meaning when user try to send money it should show loading/processing for 10s and show completed (not real transaction)

## avoid
- writing testing
- complex logic

## Running the prototype

```bash
python3 -m venv venv
source venv/bin/activate
pip install django
python manage.py migrate
python manage.py runserver
```

Visit http://127.0.0.1:8000/ — sign up via "Open an Account" to get a generated account number and password, then log in.
