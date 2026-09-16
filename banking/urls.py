from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("open/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("home/", views.dashboard, name="dashboard"),
    path("account/", views.account_page, name="account_page"),
    path("view-accounts/", views.view_accounts, name="view_accounts"),
    path("transfer/", views.transfer, name="transfer"),
    path("beneficiary/", views.beneficiary_transfer, name="beneficiary_transfer"),
    path("bulk-transfer/", views.bulk_transfer, name="bulk_transfer"),
    path("airtime/", views.airtime, name="airtime"),
    path("electricity/", views.electricity, name="electricity"),
    path("loan/", views.loan, name="loan"),
    path("payments/", views.payments, name="payments"),
    path("approvals/", views.approvals, name="approvals"),
]
