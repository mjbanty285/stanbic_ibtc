from django.shortcuts import render

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from .models import Account
from .utils import generate_account_number, generate_password


def landing(request):
    return render(request, "banking/landing.html")


def signup(request):
    if request.method == "POST":
        full_name = request.POST.get("fullname", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        bvn = request.POST.get("bvn", "").strip()
        account_type = request.POST.get("account_type", "current")

        password = generate_password()
        user = User.objects.create_user(username=email, email=email, password=password)

        account_number = generate_account_number()
        while Account.objects.filter(account_number=account_number).exists():
            account_number = generate_account_number()

        account = Account.objects.create(
            user=user,
            account_number=account_number,
            full_name=full_name,
            phone=phone,
            bvn=bvn,
            account_type=account_type,
        )

        return render(request, "banking/signup_success.html", {
            "email": email,
            "password": password,
            "account_number": account.account_number,
        })

    return render(request, "banking/open.html")


def login_view(request):
    error = None
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=email, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect("dashboard")
        error = "Invalid email or password."
    return render(request, "banking/login.html", {"error": error})


@login_required
def logout_view(request):
    auth_logout(request)
    return render(request, "banking/logout.html")


@login_required
def dashboard(request):
    return render(request, "banking/index.html", {"account": request.user.account})


@login_required
def account_page(request):
    return render(request, "banking/account.html", {"account": request.user.account})


@login_required
def view_accounts(request):
    return render(request, "banking/view_accounts.html", {"account": request.user.account})


@login_required
def transfer(request):
    return render(request, "banking/transfer.html", {"account": request.user.account})


SAVED_BENEFICIARIES = [
    {"id": 1, "name": "John Doe", "bank": "Stanbic IBTC"},
    {"id": 2, "name": "Jane Smith", "bank": "GTBank"},
    {"id": 3, "name": "Aliko Dangote", "bank": "Access Bank"},
]


@login_required
def beneficiary_transfer(request):
    return render(request, "banking/beneficiary.html", {
        "account": request.user.account,
        "beneficiaries": SAVED_BENEFICIARIES,
    })


@login_required
def bulk_transfer(request):
    return render(request, "banking/bulk.html", {
        "account": request.user.account,
        "beneficiaries": SAVED_BENEFICIARIES,
    })


@login_required
def airtime(request):
    return render(request, "banking/airtime.html", {"account": request.user.account})


@login_required
def electricity(request):
    return render(request, "banking/electricity.html", {"account": request.user.account})


@login_required
def loan(request):
    return render(request, "banking/loan.html", {"account": request.user.account})


ELECTRICITY_PROVIDERS = [
    "Abuja Electricity Distribution Company",
    "Benin Electricity Distribution Company",
    "Eko Electricity Distribution Company",
    "Enugu Electricity Distribution Company",
    "Ibadan Electricity Distribution Company",
    "Ikeja Electricity Distribution Company",
    "Jos Electricity Distribution Company",
    "Kaduna Electricity Distribution Company",
    "Kano Electricity Distribution Company",
    "Port Harcourt Electricity Distribution Company",
]


@login_required
def payments(request):
    return render(request, "banking/payments.html", {
        "account": request.user.account,
        "providers": ELECTRICITY_PROVIDERS,
    })


@login_required
def approvals(request):
    return render(request, "banking/approvals.html", {"account": request.user.account})


@login_required
def profile(request):
    return render(request, "banking/profile.html", {"account": request.user.account})


@login_required
def view_profile(request):
    return render(request, "banking/view_profile.html", {"account": request.user.account})


@login_required
def transaction_receipt(request):
    return render(request, "banking/transaction.html", {"account": request.user.account})


@login_required
@require_POST
def update_details(request):
    account = request.user.account
    full_name = request.POST.get("full_name", "").strip()
    phone = request.POST.get("phone", "").strip()
    bvn = request.POST.get("bvn", "").strip()
    email = request.POST.get("email", "").strip()

    if not full_name or not phone or not bvn or not email:
        messages.error(request, "All fields are required.")
        return redirect("profile")

    account.full_name = full_name
    account.phone = phone
    account.bvn = bvn
    account.save()

    request.user.email = email
    request.user.save()

    messages.success(request, "Your details have been updated.")
    return redirect("profile")


@login_required
@require_POST
def change_password(request):
    current_password = request.POST.get("current_password", "")
    new_password = request.POST.get("new_password", "")
    confirm_password = request.POST.get("confirm_password", "")

    if not request.user.check_password(current_password):
        messages.error(request, "Current password is incorrect.")
        return redirect("profile")

    if not new_password or new_password != confirm_password:
        messages.error(request, "New password and confirmation do not match.")
        return redirect("profile")

    request.user.set_password(new_password)
    request.user.save()
    update_session_auth_hash(request, request.user)

    messages.success(request, "Your password has been changed.")
    return redirect("profile")


@login_required
@require_POST
def set_pin(request):
    pin = request.POST.get("pin", "")
    confirm_pin = request.POST.get("confirm_pin", "")

    if not (pin.isdigit() and len(pin) == 4):
        messages.error(request, "PIN must be exactly 4 digits.")
        return redirect("profile")

    if pin != confirm_pin:
        messages.error(request, "PIN and confirmation do not match.")
        return redirect("profile")

    account = request.user.account
    account.transaction_pin = make_password(pin)
    account.save()

    messages.success(request, "Your transaction PIN has been set.")
    return redirect("profile")
