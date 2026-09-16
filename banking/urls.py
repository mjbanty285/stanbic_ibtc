from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("open/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("home/", views.dashboard, name="dashboard"),
    path("account/", views.account_page, name="account_page"),
]
