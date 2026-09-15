import random
import secrets
import string


def generate_account_number():
    return "".join(random.choices(string.digits, k=10))


def generate_password(length=10):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))
