# Stanbic IBTC Prototype: Django + Tailwind + JS Conversion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the 18 static HTML prototype pages into a single Django project with SQLite-backed auth/accounts, a shared Tailwind (Play CDN) design system via template inheritance, and JS-driven interactivity including a client-side-only 10s fake "processing → completed" flow for every money-moving action.

**Architecture:** One Django project (`stanbic_ibtc`) with one app (`banking`). `django.contrib.auth.User` (username = email) plus one extra model, `Account` (balance, account number, profile fields), created at signup. All 18 pages become templates extending a shared `base.html` (public pages) or `dashboard_base.html` (logged-in pages, adds header/bottom-nav/side-menu/processing-overlay partials). Beneficiary lists and transaction history are static Python constants, not DB models. One shared `app.js` handles side-menu, balance show/hide, clipboard copy, form validation, and the fake-processing overlay; page-specific widgets (tabs, network picker, account dropdown, loan modal) get small inline scripts per template, mirroring the original code's per-page script pattern.

**Tech Stack:** Python 3.12, Django (latest stable via pip), SQLite (default), Tailwind Play CDN (`https://cdn.tailwindcss.com`), vanilla JS (no build step, no npm).

**No automated tests are written in this plan** — the README explicitly says to avoid writing tests for this prototype. Verification is manual (`runserver` + browser/curl checks) at the end of each task.

---

## Design System Cheatsheet (reference for every template task below)

- Brand color: Tailwind config extends `brand` (`#0033a0`), `brand-dark` (`#002266`), `brand-light` (`#e6edf8`), `accent` (`#00a3e0`). Use `bg-brand`, `text-brand`, `border-brand`, etc.
- Page shell (logged-in pages): `max-w-md mx-auto bg-gray-100 min-h-screen relative pb-20`
- Header: `bg-gradient-to-b from-brand to-brand-dark text-white px-4 pt-4 pb-5`
- Select-bar: `bg-white mx-4 mt-3 rounded-lg px-3.5 py-2.5 flex justify-between items-center text-sm font-medium shadow-sm`
- Card: `bg-white rounded-xl shadow-sm p-4 mb-4`
- Section title: `text-sm font-semibold text-gray-700 mb-3`
- Primary button: `w-full bg-brand text-white font-semibold rounded-lg py-3.5 text-center`
- Outline button: `w-full border border-brand text-brand font-semibold rounded-lg py-3.5 text-center`
- Label: `block text-sm font-medium text-gray-600 mb-1.5`
- Input/select: `w-full border border-gray-300 rounded-lg px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand`
- Bottom nav: `fixed bottom-0 left-0 right-0 max-w-md mx-auto bg-brand text-white flex items-center justify-around h-16 z-30`
- Nav item: `flex flex-col items-center gap-0.5 text-[10px]` + (`opacity-100 font-bold` if active else `opacity-75`)

---

### Task 1: Bootstrap the Django project

**Files:**
- Create: `venv/` (virtualenv, gitignored)
- Create: `stanbic_ibtc/` (Django project via `startproject`)
- Create: `banking/` (Django app via `startapp`)
- Create: `.gitignore`

- [ ] **Step 1: Create and activate a virtualenv, install Django**

```bash
cd /home/ultimate/Desktop/majesty/stabic_ibtc
python3 -m venv venv
source venv/bin/activate
pip install django
```

- [ ] **Step 2: Scaffold the project and app**

```bash
django-admin startproject stanbic_ibtc .
python manage.py startapp banking
```

- [ ] **Step 3: Add `.gitignore`**

```
venv/
__pycache__/
*.pyc
db.sqlite3
```

- [ ] **Step 4: Verify the bare project runs**

```bash
python manage.py migrate
python manage.py runserver 0:8000 &
sleep 2
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/
kill %1
```
Expected: prints `200` (Django's default welcome page).

- [ ] **Step 5: Commit**

```bash
git add stanbic_ibtc banking manage.py .gitignore
git commit -m "Bootstrap Django project and banking app"
```

---

### Task 2: Configure settings

**Files:**
- Modify: `stanbic_ibtc/settings.py`

- [ ] **Step 1: Register the app and humanize, set auth redirects**

In `stanbic_ibtc/settings.py`, in `INSTALLED_APPS`, add `"django.contrib.humanize"` and `"banking"` after the default entries:

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "banking",
]
```

At the bottom of the file, add:

```python
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "landing"
```

- [ ] **Step 2: Verify settings load without error**

```bash
python manage.py check
```
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 3: Commit**

```bash
git add stanbic_ibtc/settings.py
git commit -m "Configure installed apps and auth redirect settings"
```

---

### Task 3: Account model, migration, admin

**Files:**
- Modify: `banking/models.py`
- Modify: `banking/admin.py`
- Create: `banking/migrations/0001_initial.py` (generated)

- [ ] **Step 1: Write the Account model**

Replace the contents of `banking/models.py`:

```python
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models


class Account(models.Model):
    ACCOUNT_TYPES = [
        ("savings", "Savings Account"),
        ("current", "Current Account"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="account")
    account_number = models.CharField(max_length=10, unique=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    bvn = models.CharField(max_length=11)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES, default="current")
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("1000000000.00"))

    def __str__(self):
        return f"{self.full_name} ({self.account_number})"
```

- [ ] **Step 2: Register it in admin**

Replace the contents of `banking/admin.py`:

```python
from django.contrib import admin

from .models import Account

admin.site.register(Account)
```

- [ ] **Step 3: Generate and run the migration**

```bash
python manage.py makemigrations banking
python manage.py migrate
```
Expected: a new `banking/migrations/0001_initial.py` is created and applies cleanly.

- [ ] **Step 4: Commit**

```bash
git add banking/models.py banking/admin.py banking/migrations
git commit -m "Add Account model, migration, and admin registration"
```

---

### Task 4: Signup helper utilities

**Files:**
- Create: `banking/utils.py`

- [ ] **Step 1: Write the random account number and password generators**

```python
import random
import secrets
import string


def generate_account_number():
    return "".join(random.choices(string.digits, k=10))


def generate_password(length=10):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))
```

- [ ] **Step 2: Verify it imports and produces the right shapes**

```bash
python manage.py shell -c "from banking.utils import generate_account_number, generate_password; n = generate_account_number(); p = generate_password(); print(len(n), n.isdigit(), len(p))"
```
Expected: `10 True 10`

- [ ] **Step 3: Commit**

```bash
git add banking/utils.py
git commit -m "Add account number and password generator utilities"
```

---

### Task 5: Base templates, shared partials, and core JS

**Files:**
- Create: `banking/templates/banking/base.html`
- Create: `banking/templates/banking/dashboard_base.html`
- Create: `banking/templates/banking/_header.html`
- Create: `banking/templates/banking/_bottomnav.html`
- Create: `banking/templates/banking/_sidemenu.html`
- Create: `banking/templates/banking/_processing_overlay.html`
- Create: `banking/static/banking/js/app.js`

- [ ] **Step 1: Write `base.html`**

```html
{% load static %}<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Stanbic IBTC{% endblock %}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            brand: { DEFAULT: '#0033a0', dark: '#002266', light: '#e6edf8' },
            accent: '#00a3e0'
          }
        }
      }
    }
  </script>
  <script src="{% static 'banking/js/app.js' %}" defer></script>
</head>
<body class="bg-gray-100 text-gray-800 min-h-screen">
  {% block body %}{% endblock %}
</body>
</html>
```

- [ ] **Step 2: Write `dashboard_base.html`**

```html
{% extends "banking/base.html" %}
{% block body %}
<div class="max-w-md mx-auto bg-gray-100 min-h-screen relative pb-20">
  {% include "banking/_sidemenu.html" %}
  {% include "banking/_header.html" %}
  <main class="px-4 pt-4">
    {% block content %}{% endblock %}
  </main>
  {% include "banking/_bottomnav.html" %}
  {% include "banking/_processing_overlay.html" %}
</div>
{% block extra_js %}{% endblock %}
{% endblock %}
```

- [ ] **Step 3: Write `_header.html`**

```html
<header class="bg-gradient-to-b from-brand to-brand-dark text-white px-4 pt-4 pb-5">
  <h1 class="text-base font-semibold">{{ request.user.account.full_name|default:"Guest" }}</h1>
  <p class="text-xs opacity-90 mt-0.5">Welcome back!</p>
</header>
```

- [ ] **Step 4: Write `_bottomnav.html`**

```html
<nav class="fixed bottom-0 left-0 right-0 max-w-md mx-auto bg-brand text-white flex items-center justify-around h-16 z-30">
  <a href="{% url 'dashboard' %}" class="flex flex-col items-center gap-0.5 text-[10px] {% if request.resolver_match.url_name == 'dashboard' %}opacity-100 font-bold{% else %}opacity-75{% endif %}">
    <span class="text-lg leading-none">🏠</span>Home
  </a>
  <a href="{% url 'airtime' %}" class="flex flex-col items-center gap-0.5 text-[10px] {% if request.resolver_match.url_name == 'airtime' %}opacity-100 font-bold{% else %}opacity-75{% endif %}">
    <span class="text-lg leading-none">📱</span>Airtime
  </a>
  <a href="{% url 'transfer' %}" class="flex flex-col items-center gap-0.5 text-[10px] {% if request.resolver_match.url_name == 'transfer' %}opacity-100 font-bold{% else %}opacity-75{% endif %}">
    <span class="text-lg leading-none">↔️</span>Transfer
  </a>
  <a href="{% url 'loan' %}" class="flex flex-col items-center gap-0.5 text-[10px] {% if request.resolver_match.url_name == 'loan' %}opacity-100 font-bold{% else %}opacity-75{% endif %}">
    <span class="text-lg leading-none">💳</span>Loans
  </a>
  <button onclick="toggleMenu()" type="button" class="flex flex-col items-center gap-0.5 text-[10px] opacity-75">
    <span class="text-lg leading-none">☰</span>Menu
  </button>
</nav>
```

- [ ] **Step 5: Write `_sidemenu.html`**

```html
<div id="menuOverlay" onclick="toggleMenu()" class="fixed inset-0 bg-black/40 hidden z-40"></div>
<div id="sideMenu" class="fixed top-0 right-0 h-full w-64 max-w-[80%] bg-white translate-x-full transition-transform duration-300 z-50 pt-14 pb-5 overflow-y-auto">
  <a href="{% url 'dashboard' %}" class="flex items-center gap-3 px-6 py-3.5 text-sm text-gray-700 border-b border-gray-100">🏠 Home</a>
  <a href="{% url 'airtime' %}" class="flex items-center gap-3 px-6 py-3.5 text-sm text-gray-700 border-b border-gray-100">📱 Airtime & Data</a>
  <a href="{% url 'transfer' %}" class="flex items-center gap-3 px-6 py-3.5 text-sm text-gray-700 border-b border-gray-100">↔️ Transfer</a>
  <a href="{% url 'loan' %}" class="flex items-center gap-3 px-6 py-3.5 text-sm text-gray-700 border-b border-gray-100">💳 Loans</a>
  <a href="{% url 'payments' %}" class="flex items-center gap-3 px-6 py-3.5 text-sm text-gray-700 border-b border-gray-100">💰 Payments</a>
  <a href="{% url 'approvals' %}" class="flex items-center gap-3 px-6 py-3.5 text-sm text-gray-700 border-b border-gray-100">✅ Approvals</a>
  <a href="{% url 'account_page' %}" class="flex items-center gap-3 px-6 py-3.5 text-sm text-gray-700 border-b border-gray-100">⚙️ Account</a>
  <a href="{% url 'profile' %}" class="flex items-center gap-3 px-6 py-3.5 text-sm text-gray-700 border-b border-gray-100">👤 Profile</a>
  <a href="{% url 'logout' %}" class="flex items-center gap-3 px-6 py-3.5 text-sm text-red-600">🚪 Logout</a>
</div>
```

- [ ] **Step 6: Write `_processing_overlay.html`**

```html
<div id="processingOverlay" class="fixed inset-0 bg-black/50 hidden items-center justify-center z-50 px-6">
  <div id="processingState" class="bg-white rounded-2xl p-8 text-center w-72">
    <div class="mx-auto mb-4 h-12 w-12 rounded-full border-4 border-brand/20 border-t-brand animate-spin"></div>
    <p class="font-semibold text-gray-700">Processing…</p>
    <p class="text-xs text-gray-400 mt-1">Please wait, do not close this page</p>
  </div>
  <div id="successState" class="hidden bg-white rounded-2xl p-8 text-center w-72">
    <div class="mx-auto mb-4 h-14 w-14 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-2xl">✓</div>
    <p class="font-semibold text-gray-800 mb-1">Completed</p>
    <p class="text-xs text-gray-500 mb-4">Your request has been processed successfully.</p>
    <button id="processingDoneBtn" type="button" data-redirect="{% url 'dashboard' %}" class="w-full bg-brand text-white rounded-lg py-2.5 font-semibold">Done</button>
  </div>
</div>
```

- [ ] **Step 7: Write `banking/static/banking/js/app.js`**

```javascript
function toggleMenu() {
  document.getElementById('sideMenu').classList.toggle('translate-x-full');
  document.getElementById('menuOverlay').classList.toggle('hidden');
}

function initBalanceToggles() {
  document.querySelectorAll('[data-balance-toggle]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const target = document.getElementById(btn.dataset.balanceToggle);
      if (!target) return;
      const hidden = target.dataset.hidden === 'true';
      target.textContent = hidden ? target.dataset.value : '••••••••••';
      target.dataset.hidden = hidden ? 'false' : 'true';
    });
  });
}

function initCopyButtons() {
  document.querySelectorAll('[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      navigator.clipboard.writeText(btn.dataset.copy);
      const original = btn.textContent;
      btn.textContent = 'Copied!';
      setTimeout(function () { btn.textContent = original; }, 1500);
    });
  });
}

function initFakeTransactionForms() {
  const overlay = document.getElementById('processingOverlay');
  const processing = document.getElementById('processingState');
  const success = document.getElementById('successState');
  const doneBtn = document.getElementById('processingDoneBtn');

  document.querySelectorAll('form[data-fake-transaction]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();

      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }

      const amountField = form.querySelector('[data-amount-field]');
      if (amountField) {
        const amount = parseFloat(amountField.value);
        const balance = parseFloat(form.dataset.balance || 'Infinity');
        if (isNaN(amount) || amount <= 0) {
          alert('Please enter a valid amount.');
          return;
        }
        if (amount > balance) {
          alert('Amount exceeds your available balance.');
          return;
        }
      }

      if (!overlay) return;
      overlay.classList.remove('hidden');
      overlay.classList.add('flex');
      processing.classList.remove('hidden');
      success.classList.add('hidden');

      setTimeout(function () {
        processing.classList.add('hidden');
        success.classList.remove('hidden');
      }, 10000);
    });
  });

  if (doneBtn) {
    doneBtn.addEventListener('click', function () {
      window.location.href = doneBtn.dataset.redirect;
    });
  }
}

document.addEventListener('DOMContentLoaded', function () {
  initBalanceToggles();
  initCopyButtons();
  initFakeTransactionForms();
});
```

- [ ] **Step 8: Verify templates load (via Django's template check)**

```bash
python manage.py check
```
Expected: no template syntax errors reported (URL-tag errors for not-yet-defined names like `dashboard` are expected and will resolve once Task 6+ add those routes — to confirm base/dashboard_base parse cleanly in isolation, this check is revisited at the end of Task 9 once `dashboard`, `airtime`, `transfer`, `loan` all exist).

- [ ] **Step 9: Commit**

```bash
git add banking/templates banking/static
git commit -m "Add base templates, dashboard chrome partials, and core app.js"
```

---

### Task 6: Landing page

**Files:**
- Create: `banking/templates/banking/landing.html`
- Modify: `banking/views.py`
- Create: `banking/urls.py`
- Modify: `stanbic_ibtc/urls.py`

- [ ] **Step 1: Add the landing view**

Write `banking/views.py`:

```python
from django.shortcuts import render


def landing(request):
    return render(request, "banking/landing.html")
```

- [ ] **Step 2: Create the app's URL conf**

Create `banking/urls.py`:

```python
from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
]
```

- [ ] **Step 3: Wire it into the project**

Replace `stanbic_ibtc/urls.py`:

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("banking.urls")),
]
```

- [ ] **Step 4: Write the landing template**

Based on `bankings.html`'s content (top bar, nav, hero, services grid, footer), rebuilt with Tailwind and the brand color, extending `base.html` directly (no dashboard chrome):

```html
{% extends "banking/base.html" %}
{% block title %}Stanbic IBTC - Internet Banking{% endblock %}
{% block body %}
<div class="bg-brand-dark text-white text-xs px-6 py-2 flex justify-between">
  <span>Stanbic IBTC Holdings | IT CAN BE.</span>
  <span class="hidden sm:flex gap-5"><a href="#">About Us</a><a href="#">Contact</a><a href="#">Investor Relations</a></span>
</div>
<nav class="bg-white px-6 py-4 flex justify-between items-center shadow sticky top-0 z-10">
  <span class="text-brand font-bold text-xl flex items-center gap-2">
    <span class="w-8 h-8 bg-brand rounded"></span>Stanbic IBTC
  </span>
  <ul class="hidden md:flex gap-6 text-sm font-semibold text-gray-700">
    <li>Personal</li><li>Business</li><li>Corporate</li><li>Wealth</li><li>Insurance</li>
  </ul>
  <a href="{% url 'login' %}" class="bg-accent text-white px-5 py-2 rounded font-bold text-sm">Internet Banking</a>
</nav>
<header class="bg-gradient-to-br from-brand/90 to-brand-dark/90 text-white px-6 py-20">
  <div class="max-w-lg">
    <h1 class="text-3xl md:text-4xl font-bold mb-4 leading-tight">Towards your dreams, we move.</h1>
    <p class="text-lg mb-6">Experience seamless automated banking designed to fit your unique personal and business lifestyles.</p>
    <div class="flex gap-4">
      <a href="{% url 'signup' %}" class="bg-accent px-6 py-3 rounded font-bold">Open an Account</a>
      <a href="{% url 'login' %}" class="bg-white text-brand px-6 py-3 rounded font-bold">Sign In</a>
    </div>
  </div>
</header>
<section class="px-6 py-16 text-center">
  <h2 class="text-2xl font-bold text-brand mb-10">Our Banking Solutions</h2>
  <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 max-w-5xl mx-auto">
    <div class="bg-white rounded-lg shadow p-8 border-b-4 border-transparent hover:border-brand transition">
      <div class="text-4xl text-accent mb-3">💳</div><h3 class="font-semibold text-brand-dark mb-2">Cards</h3>
      <p class="text-sm text-gray-600">Explore credit, debit, and prepaid solutions tailored for global reach.</p>
    </div>
    <div class="bg-white rounded-lg shadow p-8 border-b-4 border-transparent hover:border-brand transition">
      <div class="text-4xl text-accent mb-3">📈</div><h3 class="font-semibold text-brand-dark mb-2">Investments</h3>
      <p class="text-sm text-gray-600">Grow your financial portfolio with mutual funds and asset management.</p>
    </div>
    <div class="bg-white rounded-lg shadow p-8 border-b-4 border-transparent hover:border-brand transition">
      <div class="text-4xl text-accent mb-3">💰</div><h3 class="font-semibold text-brand-dark mb-2">Loans</h3>
      <p class="text-sm text-gray-600">Access fast, flexible funding options to scale your aspirations.</p>
    </div>
    <div class="bg-white rounded-lg shadow p-8 border-b-4 border-transparent hover:border-brand transition">
      <div class="text-4xl text-accent mb-3">📱</div><h3 class="font-semibold text-brand-dark mb-2">Digital Banking</h3>
      <p class="text-sm text-gray-600">Bank securely anytime, anywhere via our improved SuperApp.</p>
    </div>
  </div>
</section>
<footer class="bg-brand-dark text-gray-300 px-6 pt-10 pb-6 text-sm">
  <div class="grid gap-8 sm:grid-cols-3 border-b border-white/10 pb-8 mb-4 max-w-5xl mx-auto">
    <div><h4 class="text-accent font-semibold mb-3">Personal Banking</h4><ul class="space-y-2"><li>Savings Accounts</li><li>Current Accounts</li><li>Personal Loans</li></ul></div>
    <div><h4 class="text-accent font-semibold mb-3">Business Solutions</h4><ul class="space-y-2"><li>SME Banking</li></ul></div>
    <div><h4 class="text-accent font-semibold mb-3">Contact</h4><ul class="space-y-2"><li>Licensed by the Central Bank of Nigeria</li></ul></div>
  </div>
  <p class="text-center text-xs text-gray-400">© Stanbic IBTC Bank — Prototype build</p>
</footer>
{% endblock %}
```

- [ ] **Step 5: Verify**

```bash
python manage.py runserver 0:8000 &
sleep 2
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/
kill %1
```
Expected: `200`

- [ ] **Step 6: Commit**

```bash
git add banking/views.py banking/urls.py stanbic_ibtc/urls.py banking/templates/banking/landing.html
git commit -m "Add public landing page"
```

---

### Task 7: Signup flow

**Files:**
- Create: `banking/templates/banking/open.html`
- Create: `banking/templates/banking/signup_success.html`
- Modify: `banking/views.py`
- Modify: `banking/urls.py`

- [ ] **Step 1: Add the signup view**

Append to `banking/views.py`:

```python
from django.contrib.auth.models import User

from .models import Account
from .utils import generate_account_number, generate_password


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
```

(`render` is already imported at the top from Task 6's `landing` view.)

- [ ] **Step 2: Add the URL**

In `banking/urls.py`, add the route after `path("", views.landing, name="landing"),`:

```python
    path("open/", views.signup, name="signup"),
```

- [ ] **Step 3: Write `open.html`**

Rebuilds `open.html`'s fields (full name, phone, email, BVN, account type) with Tailwind, extending `base.html` directly:

```html
{% extends "banking/base.html" %}
{% block title %}Open an Account - Stanbic IBTC{% endblock %}
{% block body %}
<div class="min-h-screen flex items-center justify-center p-5">
  <div class="bg-white w-full max-w-md rounded-lg shadow-lg overflow-hidden border-t-4 border-brand">
    <div class="bg-brand text-white text-center py-5">
      <h1 class="text-lg font-bold">Stanbic IBTC Bank</h1>
      <p class="text-sm opacity-90">Instant Account Opening</p>
    </div>
    <form method="POST" class="p-6 space-y-4">
      {% csrf_token %}
      <div>
        <label class="block text-sm font-bold text-brand mb-1.5">Full Name (As on BVN)</label>
        <input type="text" name="fullname" required class="w-full border border-gray-300 rounded px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand" placeholder="Enter your full name">
      </div>
      <div>
        <label class="block text-sm font-bold text-brand mb-1.5">Phone Number</label>
        <input type="tel" name="phone" required class="w-full border border-gray-300 rounded px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand" placeholder="08012345678">
      </div>
      <div>
        <label class="block text-sm font-bold text-brand mb-1.5">Email Address</label>
        <input type="email" name="email" required class="w-full border border-gray-300 rounded px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand" placeholder="name@example.com">
      </div>
      <div>
        <label class="block text-sm font-bold text-brand mb-1.5">Bank Verification Number (BVN)</label>
        <input type="text" name="bvn" maxlength="11" required class="w-full border border-gray-300 rounded px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand" placeholder="11-digit BVN">
      </div>
      <div>
        <label class="block text-sm font-bold text-brand mb-1.5">Account Type</label>
        <select name="account_type" required class="w-full border border-gray-300 rounded px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
          <option value="">Select Account Type</option>
          <option value="savings">Savings Account</option>
          <option value="current">Current Account</option>
        </select>
      </div>
      <button type="submit" class="w-full bg-accent text-white font-bold rounded py-3">Submit Application</button>
      <p class="text-center text-xs text-gray-500">By clicking submit, you agree to the terms and conditions.</p>
    </form>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 4: Write `signup_success.html`**

```html
{% extends "banking/base.html" %}
{% block title %}Account Created - Stanbic IBTC{% endblock %}
{% block body %}
<div class="min-h-screen flex items-center justify-center p-5">
  <div class="bg-white w-full max-w-md rounded-lg shadow-lg overflow-hidden border-t-4 border-brand text-center p-8">
    <div class="mx-auto mb-4 h-14 w-14 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-2xl">✓</div>
    <h1 class="text-lg font-bold text-brand mb-2">Account Created</h1>
    <p class="text-sm text-gray-600 mb-6">Save these login details — they are shown only once.</p>
    <div class="bg-gray-50 rounded-lg p-4 text-left space-y-2 text-sm mb-6">
      <p><span class="text-gray-500">Account Number:</span> <span class="font-semibold">{{ account_number }}</span></p>
      <p><span class="text-gray-500">Login Email:</span> <span class="font-semibold">{{ email }}</span></p>
      <p><span class="text-gray-500">Password:</span> <span class="font-semibold">{{ password }}</span></p>
    </div>
    <a href="{% url 'login' %}" class="w-full inline-block bg-brand text-white font-semibold rounded-lg py-3.5">Continue to Login</a>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 5: Verify signup creates a user and account**

```bash
python manage.py runserver 0:8000 &
sleep 2
curl -s -c /tmp/cookies.txt http://127.0.0.1:8000/open/ -o /dev/null
TOKEN=$(grep csrftoken /tmp/cookies.txt | awk '{print $7}')
curl -s -b /tmp/cookies.txt -c /tmp/cookies.txt \
  -d "csrfmiddlewaretoken=$TOKEN&fullname=Test+User&phone=08010000000&email=test1@example.com&bvn=12345678901&account_type=savings" \
  -o /tmp/signup_response.html -w "%{http_code}\n" \
  http://127.0.0.1:8000/open/
grep -q "Account Created" /tmp/signup_response.html && echo "SUCCESS PAGE OK"
kill %1
python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.filter(username='test1@example.com').exists())"
```
Expected: HTTP `200`, `SUCCESS PAGE OK`, and `True`.

- [ ] **Step 6: Commit**

```bash
git add banking/views.py banking/urls.py banking/templates/banking/open.html banking/templates/banking/signup_success.html
git commit -m "Add signup flow with auto-generated account number and password"
```

---

### Task 8: Login and logout

**Files:**
- Create: `banking/templates/banking/login.html`
- Create: `banking/templates/banking/logout.html`
- Modify: `banking/views.py`
- Modify: `banking/urls.py`

- [ ] **Step 1: Add login/logout views**

Append to `banking/views.py`:

```python
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


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
```

- [ ] **Step 2: Add the URLs**

In `banking/urls.py`, add after the `signup` line:

```python
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
```

- [ ] **Step 3: Write `login.html`**

```html
{% extends "banking/base.html" %}
{% block title %}Sign In - Stanbic IBTC{% endblock %}
{% block body %}
<div class="min-h-screen flex items-center justify-center p-5">
  <div class="bg-white w-full max-w-md rounded-lg shadow-lg p-8 border-t-4 border-brand">
    <div class="text-center mb-8">
      <h2 class="text-2xl font-bold text-brand">Stanbic <span class="text-accent">IBTC</span></h2>
      <p class="text-xs text-gray-500 mt-1">Internet Banking Login</p>
    </div>
    {% if error %}
      <p class="bg-red-50 text-red-600 text-sm rounded-lg px-4 py-3 mb-4">{{ error }}</p>
    {% endif %}
    <form method="POST" class="space-y-4">
      {% csrf_token %}
      <div>
        <label class="block text-sm font-semibold text-gray-600 mb-1.5">Email</label>
        <input type="email" name="email" required class="w-full border border-gray-300 rounded px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand" placeholder="Enter your email">
      </div>
      <div>
        <label class="block text-sm font-semibold text-gray-600 mb-1.5">Password</label>
        <input type="password" name="password" required class="w-full border border-gray-300 rounded px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand" placeholder="Enter your password">
      </div>
      <button type="submit" class="w-full bg-brand text-white font-semibold rounded py-3">Sign In</button>
    </form>
    <p class="text-center text-xs text-gray-500 mt-6">New to Internet Banking? <a href="{% url 'signup' %}" class="text-brand font-semibold">Create account</a></p>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 4: Write `logout.html`**

```html
{% extends "banking/base.html" %}
{% block title %}Logged Out - Stanbic IBTC{% endblock %}
{% block body %}
<div class="min-h-screen flex items-center justify-center p-5">
  <div class="bg-white w-full max-w-md rounded-lg shadow-lg p-8 text-center border-t-4 border-brand">
    <div class="mx-auto mb-5 h-14 w-14 rounded-full bg-brand-light text-brand flex items-center justify-center text-2xl font-bold">✓</div>
    <h1 class="text-lg font-bold mb-2">Securely Logged Out</h1>
    <p class="text-sm text-gray-500 mb-6">Thank you for banking with us online. Your session has been safely closed.</p>
    <a href="{% url 'login' %}" class="w-full inline-block bg-brand text-white font-semibold rounded py-3">Log Back In</a>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 5: Verify login works end-to-end for the user created in Task 7**

```bash
python manage.py runserver 0:8000 &
sleep 2
curl -s -c /tmp/cookies2.txt http://127.0.0.1:8000/login/ -o /dev/null
TOKEN=$(grep csrftoken /tmp/cookies2.txt | awk '{print $7}')
python manage.py shell -c "
from django.contrib.auth.models import User
u = User.objects.get(username='test1@example.com')
u.set_password('knownpass123')
u.save()
"
curl -s -b /tmp/cookies2.txt -c /tmp/cookies2.txt \
  -d "csrfmiddlewaretoken=$TOKEN&email=test1@example.com&password=knownpass123" \
  -o /tmp/login_response.html -w "%{http_code}\n" -L \
  http://127.0.0.1:8000/login/
kill %1
```
Expected: `200` and (once `dashboard` exists in Task 9) the response body should eventually contain dashboard content — for now, confirm no `500` and no "Invalid email or password" in the response.

- [ ] **Step 6: Commit**

```bash
git add banking/views.py banking/urls.py banking/templates/banking/login.html banking/templates/banking/logout.html
git commit -m "Add login and logout views and templates"
```

---

### Task 9: Dashboard home

**Files:**
- Create: `banking/templates/banking/index.html`
- Modify: `banking/views.py`
- Modify: `banking/urls.py`

- [ ] **Step 1: Add the dashboard view**

Append to `banking/views.py`:

```python
@login_required
def dashboard(request):
    return render(request, "banking/index.html", {"account": request.user.account})
```

- [ ] **Step 2: Add the URL**

In `banking/urls.py`, add after `logout`:

```python
    path("home/", views.dashboard, name="dashboard"),
```

- [ ] **Step 3: Write `index.html`**

Rebuilds `index.html`'s loan banner, account card (with balance eye-toggle and copy), and quick links — fixing the original bug where the "transaction Receipt" quick link pointed at `bulk.html` instead of the receipt page:

```html
{% extends "banking/dashboard_base.html" %}
{% load humanize %}
{% block title %}Stanbic IBTC - Home{% endblock %}
{% block content %}
<div class="flex justify-between items-center mb-4">
  <a href="{% url 'view_accounts' %}" class="text-xs font-semibold text-brand border border-brand rounded-full px-4 py-2">VIEW ACCOUNTS</a>
</div>

<div class="bg-gradient-to-br from-brand-light to-blue-50 rounded-xl p-4 mb-4 relative overflow-hidden">
  <p class="text-sm text-gray-700">You can access <strong class="text-brand">EZ Cash Loan</strong> amount up to:</p>
  <strong class="text-lg text-brand block mt-1">₦0</strong>
  <a href="{% url 'loan' %}" class="text-sm font-semibold text-brand mt-1 inline-block">ACCESS YOUR LOAN ▸</a>
</div>

<div class="bg-white rounded-xl shadow-sm p-5 mb-5">
  <div class="flex justify-between items-start mb-3">
    <div class="text-sm font-semibold text-gray-800">{{ account.full_name }}</div>
    <div class="text-xs text-gray-500 bg-gray-100 rounded-full px-2 py-0.5">1/1</div>
  </div>
  <div class="text-sm text-gray-500 mb-3 flex items-center gap-2">
    {{ account.account_number }}-{{ account.get_account_type_display|upper }}
    <button data-copy="{{ account.account_number }}" type="button" class="text-brand text-xs font-semibold">Copy</button>
  </div>
  <div class="flex items-center gap-2.5 mb-1">
    <span id="balanceValue" data-value="₦{{ account.balance|intcomma }}" data-hidden="false" class="text-2xl font-bold text-gray-900">₦{{ account.balance|intcomma }}</span>
    <button data-balance-toggle="balanceValue" type="button" class="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center text-xs">👁</button>
  </div>
  <p class="text-xs text-gray-500 mb-4">Available balance<br>Effective balance ₦{{ account.balance|intcomma }}</p>
  <a href="{% url 'account_page' %}" class="w-full bg-brand text-white font-semibold rounded-lg py-3.5 text-center block">VIEW STATEMENTS</a>
</div>

<div class="text-sm font-semibold text-gray-700 mb-3">QUICK LINKS</div>
<div class="grid grid-cols-4 gap-3 mb-5">
  <a href="{% url 'bulk_transfer' %}" class="flex flex-col items-center gap-2 text-center">
    <span class="w-12 h-12 rounded-2xl bg-blue-600 text-white flex items-center justify-center text-xl">📄</span>
    <span class="text-[11px] text-gray-700 leading-tight">Bulk Transfer</span>
  </a>
  <a href="{% url 'electricity' %}" class="flex flex-col items-center gap-2 text-center">
    <span class="w-12 h-12 rounded-2xl bg-cyan-500 text-white flex items-center justify-center text-xl">⚡</span>
    <span class="text-[11px] text-gray-700 leading-tight">Electricity & TV</span>
  </a>
  <a href="{% url 'beneficiary_transfer' %}" class="flex flex-col items-center gap-2 text-center">
    <span class="w-12 h-12 rounded-2xl bg-orange-500 text-white flex items-center justify-center text-xl">👥</span>
    <span class="text-[11px] text-gray-700 leading-tight">Beneficiary Transfer</span>
  </a>
  <a href="{% url 'transaction_receipt' %}" class="flex flex-col items-center gap-2 text-center">
    <span class="w-12 h-12 rounded-2xl bg-pink-500 text-white flex items-center justify-center text-xl">🧾</span>
    <span class="text-[11px] text-gray-700 leading-tight">Transaction Receipt</span>
  </a>
</div>

<div class="bg-brand rounded-xl p-4 flex items-center gap-3.5 text-white">
  <div class="w-14 h-14 rounded-lg bg-brand-dark flex items-center justify-center text-2xl shrink-0">👨‍💼</div>
  <div>
    <h3 class="text-sm font-bold mb-1 leading-snug">HANDLE ALL YOUR BUSINESS NEEDS WITH ONE PLATFORM</h3>
    <p class="text-xs opacity-85">Access Enterprise Online 3.0 – real-time access and control of how you manage your business finances.</p>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 4: Verify the whole auth+dashboard chain**

```bash
python manage.py check
python manage.py runserver 0:8000 &
sleep 2
curl -s -b /tmp/cookies2.txt http://127.0.0.1:8000/home/ -o /tmp/dashboard.html -w "%{http_code}\n"
grep -q "QUICK LINKS" /tmp/dashboard.html && echo "DASHBOARD OK"
kill %1
```
Expected: `200`, `DASHBOARD OK`, and `python manage.py check` reports no issues (confirms Task 5's base/dashboard_base templates and their `{% url %}` tags all resolve now that `dashboard`, `airtime`, `transfer`, `loan` exist — `airtime` and `loan` are added in Tasks 15 and 17, so this check may still show url resolution errors for those two until those tasks land; re-run `python manage.py check` again after Task 17 to confirm zero issues).

- [ ] **Step 5: Commit**

```bash
git add banking/views.py banking/urls.py banking/templates/banking/index.html
git commit -m "Add dashboard home page"
```

---

### Task 10: Account page (statements view)

**Files:**
- Create: `banking/templates/banking/account.html`
- Modify: `banking/views.py`
- Modify: `banking/urls.py`

- [ ] **Step 1: Add the view**

Append to `banking/views.py`:

```python
@login_required
def account_page(request):
    return render(request, "banking/account.html", {"account": request.user.account})
```

- [ ] **Step 2: Add the URL**

In `banking/urls.py`, add after `dashboard`:

```python
    path("account/", views.account_page, name="account_page"),
```

- [ ] **Step 3: Write `account.html`**

Rebuilds `account.html`'s account-switch dropdown, summary totals, and empty-transactions state:

```html
{% extends "banking/dashboard_base.html" %}
{% load humanize %}
{% block title %}Account - Stanbic IBTC{% endblock %}
{% block content %}
<div class="bg-white rounded-lg px-4 py-3.5 flex justify-between items-center shadow-sm mb-4 cursor-pointer" onclick="document.getElementById('accountDropdown').classList.toggle('hidden')">
  <span class="font-semibold text-sm">Account</span>
  <span class="text-xs text-gray-500">▼ Select</span>
</div>
<div id="accountDropdown" class="hidden bg-white rounded-lg shadow-lg mb-4 overflow-hidden">
  <button type="button" class="w-full text-left px-4 py-3.5 border-b border-gray-100 hover:bg-gray-50">{{ account.account_number }}-{{ account.get_account_type_display|upper }}</button>
</div>

<div class="bg-white rounded-xl shadow-sm p-4 mb-4">
  <div class="flex justify-between">
    <div>
      <div class="text-base font-bold">{{ account.account_number }}-{{ account.get_account_type_display|upper }}</div>
      <div class="text-sm text-gray-500 mt-1.5">{{ account.full_name }}</div>
    </div>
    <div class="text-xs text-gray-400">1/1</div>
  </div>
</div>

<div class="bg-white rounded-xl shadow-sm p-4 mb-4">
  <h2 class="text-base font-semibold mb-2">Account Summary</h2>
  <p class="text-sm text-gray-500 mb-4">Showing results for the last 30 days</p>
  <div class="flex gap-10 mb-4">
    <div>
      <div class="text-xs text-gray-500 mb-1">Total Credit</div>
      <div class="text-lg font-bold text-green-600">₦{{ account.balance|intcomma }}</div>
    </div>
    <div>
      <div class="text-xs text-gray-500 mb-1">Total Debit</div>
      <div class="text-lg font-bold text-orange-600">₦0</div>
    </div>
  </div>
</div>

<h2 class="text-center text-xl font-bold my-6">No Transaction Found</h2>
<p class="text-center text-xs text-gray-500 leading-relaxed">This is a frontend prototype demo with sample account data only.<br>Not connected to any real bank.</p>
{% endblock %}
```

- [ ] **Step 4: Verify**

```bash
python manage.py runserver 0:8000 &
sleep 2
curl -s -b /tmp/cookies2.txt http://127.0.0.1:8000/account/ -o /tmp/account.html -w "%{http_code}\n"
grep -q "Account Summary" /tmp/account.html && echo "ACCOUNT PAGE OK"
kill %1
```
Expected: `200`, `ACCOUNT PAGE OK`.

- [ ] **Step 5: Commit**

```bash
git add banking/views.py banking/urls.py banking/templates/banking/account.html
git commit -m "Add account statements page"
```

---

### Task 11: View accounts page

**Files:**
- Create: `banking/templates/banking/view_accounts.html`
- Modify: `banking/views.py`
- Modify: `banking/urls.py`

- [ ] **Step 1: Add the view**

Append to `banking/views.py`:

```python
@login_required
def view_accounts(request):
    return render(request, "banking/view_accounts.html", {"account": request.user.account})
```

- [ ] **Step 2: Add the URL**

In `banking/urls.py`, add after `account_page`:

```python
    path("view-accounts/", views.view_accounts, name="view_accounts"),
```

- [ ] **Step 3: Write `view_accounts.html`**

Rebuilds `view.html`'s balance card and recent-transactions table (static demo row, per spec):

```html
{% extends "banking/dashboard_base.html" %}
{% load humanize %}
{% block title %}View Account - Stanbic IBTC{% endblock %}
{% block content %}
<div class="bg-white rounded-xl shadow-sm p-5 mb-4 border-l-4 border-brand">
  <div class="text-xs uppercase tracking-wide text-gray-500 mb-1">{{ account.get_account_type_display }}</div>
  <div class="text-sm text-gray-600 mb-4">Account Number: {{ account.account_number }}</div>
  <div class="text-xs text-gray-500">Available Balance</div>
  <div class="text-3xl font-bold text-brand mt-1">₦{{ account.balance|intcomma }}</div>
</div>

<div class="bg-white rounded-xl shadow-sm p-5">
  <h2 class="text-base font-semibold text-brand border-b-2 border-brand-light pb-2.5 mb-4">Recent Transactions</h2>
  <div class="overflow-x-auto">
    <table class="w-full text-sm">
      <thead>
        <tr class="text-left text-brand bg-brand-light">
          <th class="p-2.5">Date</th>
          <th class="p-2.5">Description</th>
          <th class="p-2.5 text-right">Amount</th>
        </tr>
      </thead>
      <tbody>
        <tr class="border-b border-gray-100">
          <td class="p-2.5">24 Aug 2026</td>
          <td class="p-2.5">Mobile App Transfer to Access Bank</td>
          <td class="p-2.5 text-right text-green-600 font-semibold">+₦{{ account.balance|intcomma }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 4: Verify**

```bash
python manage.py runserver 0:8000 &
sleep 2
curl -s -b /tmp/cookies2.txt http://127.0.0.1:8000/view-accounts/ -o /tmp/view.html -w "%{http_code}\n"
grep -q "Recent Transactions" /tmp/view.html && echo "VIEW ACCOUNTS OK"
kill %1
```
Expected: `200`, `VIEW ACCOUNTS OK`.

- [ ] **Step 5: Commit**

```bash
git add banking/views.py banking/urls.py banking/templates/banking/view_accounts.html
git commit -m "Add view accounts page"
```

---

### Task 12: Transfer page (first fake-transaction form)

**Files:**
- Create: `banking/templates/banking/transfer.html`
- Modify: `banking/views.py`
- Modify: `banking/urls.py`

- [ ] **Step 1: Add the view**

Append to `banking/views.py`:

```python
@login_required
def transfer(request):
    return render(request, "banking/transfer.html", {"account": request.user.account})
```

- [ ] **Step 2: Add the URL**

In `banking/urls.py`, add after `view_accounts`:

```python
    path("transfer/", views.transfer, name="transfer"),
```

- [ ] **Step 3: Write `transfer.html`**

Rebuilds `transfer.html`'s transfer-type picker and form, wired to the shared fake-processing overlay via `data-fake-transaction` and `data-amount-field`:

```html
{% extends "banking/dashboard_base.html" %}
{% load humanize %}
{% block title %}Domestic Transfer - Stanbic IBTC{% endblock %}
{% block content %}
<div class="bg-white rounded-xl shadow-sm p-4 mb-4">
  <h2 class="text-lg font-bold mb-1">Domestic Transfer</h2>
  <p class="text-sm text-gray-500 mb-5">Select a transfer type</p>

  <div class="grid grid-cols-3 gap-4 mb-6" id="typeGrid">
    <button type="button" data-type="other" class="type-btn flex flex-col items-center gap-1.5 text-center">
      <span class="w-[52px] h-[52px] rounded-full bg-brand text-white flex items-center justify-center text-xl ring-4 ring-blue-400">🏦</span>
      <span class="text-xs text-gray-700">Other Banks</span>
    </button>
    <button type="button" data-type="beneficiary" class="type-btn flex flex-col items-center gap-1.5 text-center">
      <span class="w-[52px] h-[52px] rounded-full bg-brand text-white flex items-center justify-center text-xl">👤</span>
      <span class="text-xs text-gray-700">Beneficiary</span>
    </button>
    <button type="button" data-type="stanbic" class="type-btn flex flex-col items-center gap-1.5 text-center">
      <span class="w-[52px] h-[52px] rounded-full bg-brand text-white flex items-center justify-center text-xl">⇄</span>
      <span class="text-xs text-gray-700">Stanbic IBTC Account</span>
    </button>
  </div>

  <p class="text-sm text-gray-600 mb-4">Available Limit: <strong class="text-brand">₦250,000,000</strong><br>Per Transaction Limit: <strong class="text-brand">₦250,000,000</strong></p>

  <form data-fake-transaction data-balance="{{ account.balance }}" class="space-y-4">
    <div>
      <label class="block text-sm font-medium text-gray-600 mb-1.5">Select Account to Debit *</label>
      <select required class="w-full border border-gray-300 rounded-lg px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
        <option value="{{ account.account_number }}">{{ account.account_number }}-{{ account.get_account_type_display|upper }}</option>
      </select>
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-600 mb-1.5">Amount *</label>
      <input type="number" data-amount-field min="1" step="0.01" required placeholder="0.00" class="w-full border border-gray-300 rounded-lg px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-600 mb-1.5">Recipient Account *</label>
      <input type="text" required placeholder="Account number" class="w-full border border-gray-300 rounded-lg px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-600 mb-1.5">Recipient Bank *</label>
      <select required class="w-full border border-gray-300 rounded-lg px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
        <option value="">Select bank</option>
        <option>Access Bank</option><option>First Bank</option><option>GTBank</option><option>UBA</option><option>Zenith Bank</option>
      </select>
    </div>
    <button type="submit" class="w-full bg-brand text-white font-semibold rounded-lg py-3.5 mt-2">Continue</button>
  </form>
</div>
<p class="bg-amber-50 text-amber-700 text-xs rounded-lg p-3">This is a prototype only. No real transfer occurs.</p>
{% block extra_js %}
<script>
  document.querySelectorAll('#typeGrid .type-btn span:first-child').forEach(function (circle) {
    circle.parentElement.addEventListener('click', function () {
      document.querySelectorAll('#typeGrid span:first-child').forEach(function (c) { c.classList.remove('ring-4'); });
      circle.classList.add('ring-4');
    });
  });
</script>
{% endblock %}
{% endblock %}
```

- [ ] **Step 4: Verify the page renders and the fake-processing overlay elements are present**

```bash
python manage.py runserver 0:8000 &
sleep 2
curl -s -b /tmp/cookies2.txt http://127.0.0.1:8000/transfer/ -o /tmp/transfer.html -w "%{http_code}\n"
grep -q "data-fake-transaction" /tmp/transfer.html && echo "TRANSFER FORM WIRED"
grep -q "processingOverlay" /tmp/transfer.html && echo "OVERLAY PRESENT"
kill %1
```
Expected: `200`, `TRANSFER FORM WIRED`, `OVERLAY PRESENT`. (Manually open `/transfer/` in a browser once, fill the form, submit, and confirm the 10s processing → completed flow visually.)

- [ ] **Step 5: Commit**

```bash
git add banking/views.py banking/urls.py banking/templates/banking/transfer.html
git commit -m "Add domestic transfer page with fake processing flow"
```

---

### Task 13: Beneficiary transfer

**Files:**
- Create: `banking/templates/banking/beneficiary.html`
- Modify: `banking/views.py`
- Modify: `banking/urls.py`

- [ ] **Step 1: Add the static beneficiary list and view**

Append to `banking/views.py`:

```python
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
```

- [ ] **Step 2: Add the URL**

In `banking/urls.py`, add after `transfer`:

```python
    path("beneficiary/", views.beneficiary_transfer, name="beneficiary_transfer"),
```

- [ ] **Step 3: Write `beneficiary.html`**

```html
{% extends "banking/dashboard_base.html" %}
{% load humanize %}
{% block title %}Beneficiary Transfer - Stanbic IBTC{% endblock %}
{% block content %}
<div class="bg-white rounded-xl shadow-sm overflow-hidden mb-4">
  <div class="bg-gradient-to-br from-brand-dark to-brand text-white text-center px-6 py-6">
    <h1 class="text-lg font-semibold">Beneficiary Transfer</h1>
    <p class="text-xs opacity-90 mt-1">Move funds securely to saved or new accounts</p>
  </div>
  <form data-fake-transaction data-balance="{{ account.balance }}" class="p-5 space-y-4">
    <div>
      <label class="block text-sm font-medium text-gray-600 mb-1.5">From Account</label>
      <select required class="w-full border border-gray-300 rounded-lg px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
        <option value="{{ account.account_number }}">{{ account.account_number }}-{{ account.get_account_type_display|upper }} (₦{{ account.balance|intcomma }})</option>
      </select>
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-600 mb-1.5">Beneficiary Type</label>
      <select id="beneficiary-type" onchange="toggleBeneficiaryForm()" class="w-full border border-gray-300 rounded-lg px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
        <option value="saved">Saved Beneficiary</option>
        <option value="new">New Beneficiary</option>
      </select>
    </div>
    <div id="saved-beneficiary-group">
      <label class="block text-sm font-medium text-gray-600 mb-1.5">Select Beneficiary</label>
      <select class="w-full border border-gray-300 rounded-lg px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
        <option value="">Choose a beneficiary</option>
        {% for b in beneficiaries %}
          <option value="{{ b.id }}">{{ b.name }} - {{ b.bank }}</option>
        {% endfor %}
      </select>
    </div>
    <div id="new-beneficiary-fields" class="hidden space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-600 mb-1.5">Destination Bank</label>
        <select class="w-full border border-gray-300 rounded-lg px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
          <option value="">Select Bank</option><option>Stanbic IBTC Bank</option><option>Access Bank</option><option>Guaranty Trust Bank</option><option>Zenith Bank</option>
        </select>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-600 mb-1.5">Account Number</label>
        <input type="text" id="new-account-number" oninput="simulateNameLookup()" maxlength="10" placeholder="Enter 10-digit number" class="w-full border border-gray-300 rounded-lg px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
        <div id="account-lookup-name" class="hidden bg-brand-light border border-dashed border-accent text-brand text-xs rounded p-3 mt-2">Target Name: <strong>CHIDI OPARA BENJAMIN</strong></div>
      </div>
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-600 mb-1.5">Amount</label>
      <div class="relative">
        <span class="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500 font-bold">₦</span>
        <input type="number" data-amount-field min="100" required placeholder="0.00" class="w-full border border-gray-300 rounded-lg pl-9 pr-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
      </div>
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-600 mb-1.5">Narration / Remarks</label>
      <textarea rows="2" placeholder="Optional transfer memo" class="w-full border border-gray-300 rounded-lg px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand"></textarea>
    </div>
    <button type="submit" class="w-full bg-brand text-white font-semibold rounded-lg py-3.5">Continue</button>
  </form>
  <p class="text-center text-xs text-gray-500 px-5 pb-5 border-t border-gray-100 pt-4">Stanbic IBTC Bank Blue Rewards. Secure Banking Layer Active.</p>
</div>
{% block extra_js %}
<script>
  function toggleBeneficiaryForm() {
    const type = document.getElementById('beneficiary-type').value;
    document.getElementById('saved-beneficiary-group').classList.toggle('hidden', type === 'new');
    document.getElementById('new-beneficiary-fields').classList.toggle('hidden', type !== 'new');
  }
  function simulateNameLookup() {
    const accNum = document.getElementById('new-account-number').value;
    document.getElementById('account-lookup-name').classList.toggle('hidden', accNum.length !== 10);
  }
</script>
{% endblock %}
{% endblock %}
```

- [ ] **Step 4: Verify**

```bash
python manage.py runserver 0:8000 &
sleep 2
curl -s -b /tmp/cookies2.txt http://127.0.0.1:8000/beneficiary/ -o /tmp/beneficiary.html -w "%{http_code}\n"
grep -q "John Doe - Stanbic IBTC" /tmp/beneficiary.html && echo "BENEFICIARY LIST RENDERED"
kill %1
```
Expected: `200`, `BENEFICIARY LIST RENDERED`.

- [ ] **Step 5: Commit**

```bash
git add banking/views.py banking/urls.py banking/templates/banking/beneficiary.html
git commit -m "Add beneficiary transfer page with static beneficiary list"
```

---

### Task 14: Bulk transfer

**Files:**
- Create: `banking/templates/banking/bulk.html`
- Modify: `banking/views.py`
- Modify: `banking/urls.py`

- [ ] **Step 1: Add the view**

Append to `banking/views.py`:

```python
@login_required
def bulk_transfer(request):
    return render(request, "banking/bulk.html", {
        "account": request.user.account,
        "beneficiaries": SAVED_BENEFICIARIES,
    })
```

- [ ] **Step 2: Add the URL**

In `banking/urls.py`, add after `beneficiary_transfer`:

```python
    path("bulk-transfer/", views.bulk_transfer, name="bulk_transfer"),
```

- [ ] **Step 3: Write `bulk.html`**

```html
{% extends "banking/dashboard_base.html" %}
{% load humanize %}
{% block title %}Bulk Transfer - Stanbic IBTC{% endblock %}
{% block content %}
<h1 class="text-lg font-bold text-brand mb-4">Bulk Transfer Management</h1>

<div class="grid grid-cols-2 gap-3 mb-4">
  <div class="bg-white rounded-lg shadow-sm p-4 border-l-4 border-brand">
    <h3 class="text-xs uppercase text-gray-500 mb-1.5">Source Account</h3>
    <p class="text-base font-bold">{{ account.account_number }}</p>
  </div>
  <div class="bg-white rounded-lg shadow-sm p-4 border-l-4 border-brand">
    <h3 class="text-xs uppercase text-gray-500 mb-1.5">Available Balance</h3>
    <p class="text-base font-bold">₦{{ account.balance|intcomma }}</p>
  </div>
  <div class="bg-white rounded-lg shadow-sm p-4 border-l-4 border-brand">
    <h3 class="text-xs uppercase text-gray-500 mb-1.5">Beneficiaries</h3>
    <p class="text-base font-bold">{{ beneficiaries|length }} Available</p>
  </div>
  <div class="bg-white rounded-lg shadow-sm p-4 border-l-4 border-brand">
    <h3 class="text-xs uppercase text-gray-500 mb-1.5">Total Transfer Amount</h3>
    <p class="text-base font-bold">₦0.00</p>
  </div>
</div>

<div class="bg-white rounded-lg shadow-sm p-5 mb-4">
  <h2 class="text-sm font-semibold text-brand border-b border-gray-200 pb-2 mb-4">Option 1: Upload Bulk File</h2>
  <div onclick="document.getElementById('excelFile').click()" class="border-2 border-dashed border-brand bg-brand-light rounded-lg p-8 text-center cursor-pointer mb-3">
    <p class="text-brand font-medium text-sm">Click here to browse your CSV / Excel schedule</p>
    <input type="file" id="excelFile" class="hidden" accept=".csv,.xlsx,.xls">
  </div>
  <a href="#" class="text-xs font-semibold text-brand">📥 Download Bulk Transfer Template (.CSV)</a>
</div>

<form data-fake-transaction data-balance="{{ account.balance }}" class="bg-white rounded-lg shadow-sm p-5 mb-4">
  <h2 class="text-sm font-semibold text-brand border-b border-gray-200 pb-2 mb-4">Option 2: Manual Beneficiary Entry</h2>
  <div class="overflow-x-auto mb-4">
    <table class="w-full text-xs">
      <thead>
        <tr class="bg-brand-light text-brand text-left">
          <th class="p-2">Bank</th><th class="p-2">Account No.</th><th class="p-2">Name</th><th class="p-2">Amount</th>
        </tr>
      </thead>
      <tbody>
        {% for b in beneficiaries %}
        <tr class="border-b border-gray-100">
          <td class="p-2">{{ b.bank }}</td>
          <td class="p-2"><input type="text" placeholder="10 digits" maxlength="10" class="w-full border border-gray-300 rounded px-2 py-1.5"></td>
          <td class="p-2"><input type="text" value="{{ b.name }}" disabled class="w-full border border-gray-300 rounded px-2 py-1.5 bg-gray-50"></td>
          <td class="p-2"><input type="number" data-amount-field placeholder="0.00" class="w-full border border-gray-300 rounded px-2 py-1.5"></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  <div class="flex justify-end gap-3">
    <button type="button" class="px-5 py-2.5 rounded bg-gray-200 text-sm font-semibold">Save Draft</button>
    <button type="submit" class="px-5 py-2.5 rounded bg-brand text-white text-sm font-semibold">Submit for Approval</button>
  </div>
</form>
{% endblock %}
```

- [ ] **Step 4: Verify**

```bash
python manage.py runserver 0:8000 &
sleep 2
curl -s -b /tmp/cookies2.txt http://127.0.0.1:8000/bulk-transfer/ -o /tmp/bulk.html -w "%{http_code}\n"
grep -q "Manual Beneficiary Entry" /tmp/bulk.html && echo "BULK PAGE OK"
kill %1
```
Expected: `200`, `BULK PAGE OK`.

- [ ] **Step 5: Commit**

```bash
git add banking/views.py banking/urls.py banking/templates/banking/bulk.html
git commit -m "Add bulk transfer page"
```

---

### Task 15: Airtime & Data

**Files:**
- Create: `banking/templates/banking/airtime.html`
- Modify: `banking/views.py`
- Modify: `banking/urls.py`

- [ ] **Step 1: Add the view**

Append to `banking/views.py`:

```python
@login_required
def airtime(request):
    return render(request, "banking/airtime.html", {"account": request.user.account})
```

- [ ] **Step 2: Add the URL**

In `banking/urls.py`, add after `bulk_transfer`:

```python
    path("airtime/", views.airtime, name="airtime"),
```

- [ ] **Step 3: Write `airtime.html`**

```html
{% extends "banking/dashboard_base.html" %}
{% load humanize %}
{% block title %}Airtime and Data - Stanbic IBTC{% endblock %}
{% block content %}
<h2 class="text-lg font-bold mb-1">Buy Airtime / Data</h2>
<p class="text-sm text-gray-500 mb-4">Recharge any Nigerian network instantly</p>

<div class="flex bg-brand-light rounded-xl p-1 mb-5">
  <button type="button" id="tab-airtime" onclick="switchTab('airtime')" class="flex-1 py-2.5 rounded-lg text-sm font-semibold bg-white text-brand shadow-sm">Airtime</button>
  <button type="button" id="tab-data" onclick="switchTab('data')" class="flex-1 py-2.5 rounded-lg text-sm font-semibold text-gray-500">Data</button>
</div>

<p class="text-sm font-semibold mb-2.5">Select Network</p>
<div class="grid grid-cols-4 gap-2.5 mb-5" id="networks">
  <button type="button" onclick="selectNetwork(this)" class="network selected border-2 border-brand bg-brand-light rounded-xl py-3 text-center">
    <span class="block w-9 h-9 mx-auto mb-1.5 rounded-full bg-yellow-400 text-black text-[10px] font-extrabold flex items-center justify-center">MTN</span>
    <span class="text-[11px] font-semibold">MTN</span>
  </button>
  <button type="button" onclick="selectNetwork(this)" class="network border-2 border-gray-200 rounded-xl py-3 text-center">
    <span class="block w-9 h-9 mx-auto mb-1.5 rounded-full bg-red-600 text-white text-[10px] font-extrabold flex items-center justify-center">A</span>
    <span class="text-[11px] font-semibold">Airtel</span>
  </button>
  <button type="button" onclick="selectNetwork(this)" class="network border-2 border-gray-200 rounded-xl py-3 text-center">
    <span class="block w-9 h-9 mx-auto mb-1.5 rounded-full bg-green-600 text-white text-[10px] font-extrabold flex items-center justify-center">Glo</span>
    <span class="text-[11px] font-semibold">Glo</span>
  </button>
  <button type="button" onclick="selectNetwork(this)" class="network border-2 border-gray-200 rounded-xl py-3 text-center">
    <span class="block w-9 h-9 mx-auto mb-1.5 rounded-full bg-green-800 text-white text-[10px] font-extrabold flex items-center justify-center">9</span>
    <span class="text-[11px] font-semibold">9mobile</span>
  </button>
</div>

<form data-fake-transaction data-balance="{{ account.balance }}" class="space-y-4">
  <div>
    <label class="block text-sm font-semibold mb-1.5">Phone Number <span class="text-red-600">*</span></label>
    <input type="tel" required maxlength="14" placeholder="0803 000 0000" class="w-full border border-gray-300 rounded-lg px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
  </div>
  <div id="amount-group">
    <label class="block text-sm font-semibold mb-1.5">Amount (₦) <span class="text-red-600">*</span></label>
    <input type="number" id="amount" data-amount-field min="50" required placeholder="500" class="w-full border border-gray-300 rounded-lg px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
    <div class="grid grid-cols-4 gap-2 mt-2">
      <button type="button" onclick="setAmount(this, 100)" class="amt-btn border border-gray-300 rounded-lg py-2 text-xs font-semibold">₦100</button>
      <button type="button" onclick="setAmount(this, 200)" class="amt-btn selected bg-brand text-white border border-brand rounded-lg py-2 text-xs font-semibold">₦200</button>
      <button type="button" onclick="setAmount(this, 500)" class="amt-btn border border-gray-300 rounded-lg py-2 text-xs font-semibold">₦500</button>
      <button type="button" onclick="setAmount(this, 1000)" class="amt-btn border border-gray-300 rounded-lg py-2 text-xs font-semibold">₦1,000</button>
    </div>
  </div>
  <div id="bundle-group" class="hidden">
    <label class="block text-sm font-semibold mb-1.5">Data Bundle <span class="text-red-600">*</span></label>
    <select class="w-full border border-gray-300 rounded-lg px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
      <option value="">Select a bundle</option>
      <option>100MB — ₦100 (1 day)</option><option>500MB — ₦200 (7 days)</option><option>1.5GB — ₦500 (30 days)</option><option>3GB — ₦1,000 (30 days)</option>
    </select>
  </div>
  <div>
    <label class="block text-sm font-semibold mb-1.5">Account to Debit <span class="text-red-600">*</span></label>
    <select class="w-full border border-gray-300 rounded-lg px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
      <option>{{ account.account_number }}-{{ account.get_account_type_display|upper }}</option>
    </select>
  </div>
  <div class="flex gap-2.5 mt-6">
    <button type="button" onclick="window.location.href='{% url 'dashboard' %}'" class="flex-1 border-2 border-red-600 text-red-600 rounded-lg py-3.5 font-bold text-sm">CANCEL</button>
    <button type="submit" class="flex-1 bg-brand text-white rounded-lg py-3.5 font-bold text-sm">NEXT</button>
  </div>
</form>
{% block extra_js %}
<script>
  function selectNetwork(el) {
    document.querySelectorAll('#networks .network').forEach(n => n.classList.remove('selected', 'border-brand', 'bg-brand-light'));
    document.querySelectorAll('#networks .network').forEach(n => n.classList.add('border-gray-200'));
    el.classList.remove('border-gray-200');
    el.classList.add('selected', 'border-brand', 'bg-brand-light');
  }
  function setAmount(el, val) {
    document.querySelectorAll('.amt-btn').forEach(b => { b.classList.remove('selected', 'bg-brand', 'text-white', 'border-brand'); b.classList.add('border-gray-300'); });
    el.classList.remove('border-gray-300');
    el.classList.add('selected', 'bg-brand', 'text-white', 'border-brand');
    document.getElementById('amount').value = val;
  }
  function switchTab(type) {
    document.getElementById('tab-airtime').className = 'flex-1 py-2.5 rounded-lg text-sm font-semibold ' + (type === 'airtime' ? 'bg-white text-brand shadow-sm' : 'text-gray-500');
    document.getElementById('tab-data').className = 'flex-1 py-2.5 rounded-lg text-sm font-semibold ' + (type === 'data' ? 'bg-white text-brand shadow-sm' : 'text-gray-500');
    document.getElementById('amount-group').classList.toggle('hidden', type === 'data');
    document.getElementById('bundle-group').classList.toggle('hidden', type !== 'data');
  }
</script>
{% endblock %}
{% endblock %}
```

- [ ] **Step 4: Verify**

```bash
python manage.py runserver 0:8000 &
sleep 2
curl -s -b /tmp/cookies2.txt http://127.0.0.1:8000/airtime/ -o /tmp/airtime.html -w "%{http_code}\n"
grep -q "Buy Airtime" /tmp/airtime.html && echo "AIRTIME PAGE OK"
kill %1
```
Expected: `200`, `AIRTIME PAGE OK`.

- [ ] **Step 5: Commit**

```bash
git add banking/views.py banking/urls.py banking/templates/banking/airtime.html
git commit -m "Add airtime and data purchase page"
```

---

### Task 16: Electricity & TV bill payment

**Files:**
- Create: `banking/templates/banking/electricity.html`
- Modify: `banking/views.py`
- Modify: `banking/urls.py`

- [ ] **Step 1: Add the view**

Append to `banking/views.py`:

```python
@login_required
def electricity(request):
    return render(request, "banking/electricity.html", {"account": request.user.account})
```

- [ ] **Step 2: Add the URL**

In `banking/urls.py`, add after `airtime`:

```python
    path("electricity/", views.electricity, name="electricity"),
```

- [ ] **Step 3: Write `electricity.html`**

```html
{% extends "banking/dashboard_base.html" %}
{% block title %}Bill Payment - Stanbic IBTC{% endblock %}
{% block content %}
<div class="bg-white rounded-xl shadow-sm overflow-hidden">
  <div class="bg-brand text-white text-center py-5">
    <h1 class="text-lg font-semibold">Stanbic IBTC Payments</h1>
  </div>
  <div class="flex bg-brand-light">
    <button type="button" id="tab-electricity" onclick="switchBillTab('electricity')" class="flex-1 py-3.5 text-sm font-bold text-brand bg-white border-b-[3px] border-brand">Electricity</button>
    <button type="button" id="tab-tv" onclick="switchBillTab('tv')" class="flex-1 py-3.5 text-sm font-bold text-brand">TV Subscription</button>
  </div>
  <div class="p-6">
    <form id="electricity-form" data-fake-transaction data-balance="{{ account.balance }}" class="space-y-4">
      <div>
        <label class="block text-sm font-semibold mb-2">Select DisCo (Provider)</label>
        <select required class="w-full border border-gray-300 rounded px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
          <option value="">-- Choose Provider --</option>
          <option value="ekedc">EKEDC (Eko)</option><option value="ikedc">IKEDC (Ikeja)</option><option value="aedc">AEDC (Abuja)</option><option value="ibedc">IBEDC (Ibadan)</option>
        </select>
      </div>
      <div>
        <label class="block text-sm font-semibold mb-2">Meter Type</label>
        <select class="w-full border border-gray-300 rounded px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
          <option value="prepaid">Prepaid</option><option value="postpaid">Postpaid</option>
        </select>
      </div>
      <div>
        <label class="block text-sm font-semibold mb-2">Meter / Account Number</label>
        <input type="number" required placeholder="Enter meter number" class="w-full border border-gray-300 rounded px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
      </div>
      <div>
        <label class="block text-sm font-semibold mb-2">Amount (NGN)</label>
        <input type="number" data-amount-field min="100" required placeholder="0.00" class="w-full border border-gray-300 rounded px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
      </div>
      <button type="submit" class="w-full bg-brand text-white font-bold rounded py-3.5">Pay Bill</button>
    </form>
    <form id="tv-form" data-fake-transaction data-balance="{{ account.balance }}" class="hidden space-y-4">
      <div>
        <label class="block text-sm font-semibold mb-2">Select Provider</label>
        <select required class="w-full border border-gray-300 rounded px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
          <option value="">-- Choose Provider --</option>
          <option value="dstv">DSTV</option><option value="gotv">GOtv</option><option value="startimes">StarTimes</option>
        </select>
      </div>
      <div>
        <label class="block text-sm font-semibold mb-2">Select Package</label>
        <select required class="w-full border border-gray-300 rounded px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
          <option value="">-- Choose Package --</option>
          <option value="premium">Premium</option><option value="compact">Compact</option><option value="max">Max / Plus</option>
        </select>
      </div>
      <div>
        <label class="block text-sm font-semibold mb-2">Smartcard / UIC Number</label>
        <input type="number" required placeholder="Enter smartcard number" class="w-full border border-gray-300 rounded px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
      </div>
      <div>
        <label class="block text-sm font-semibold mb-2">Amount (NGN)</label>
        <input type="number" data-amount-field min="100" required placeholder="0.00" class="w-full border border-gray-300 rounded px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand">
      </div>
      <button type="submit" class="w-full bg-brand text-white font-bold rounded py-3.5">Pay Bill</button>
    </form>
  </div>
</div>
{% block extra_js %}
<script>
  function switchBillTab(type) {
    document.getElementById('tab-electricity').className = 'flex-1 py-3.5 text-sm font-bold text-brand ' + (type === 'electricity' ? 'bg-white border-b-[3px] border-brand' : '');
    document.getElementById('tab-tv').className = 'flex-1 py-3.5 text-sm font-bold text-brand ' + (type === 'tv' ? 'bg-white border-b-[3px] border-brand' : '');
    document.getElementById('electricity-form').classList.toggle('hidden', type !== 'electricity');
    document.getElementById('tv-form').classList.toggle('hidden', type !== 'tv');
  }
</script>
{% endblock %}
{% endblock %}
```

Note: two `data-fake-transaction` forms on one page both hook into the single shared `#processingOverlay` — `app.js`'s `initFakeTransactionForms` attaches a submit listener per matching form, and both drive the same overlay, which is correct since only one form is ever visible/submitted at a time.

- [ ] **Step 4: Verify**

```bash
python manage.py runserver 0:8000 &
sleep 2
curl -s -b /tmp/cookies2.txt http://127.0.0.1:8000/electricity/ -o /tmp/electricity.html -w "%{http_code}\n"
grep -q "Pay Bill" /tmp/electricity.html && echo "ELECTRICITY PAGE OK"
kill %1
```
Expected: `200`, `ELECTRICITY PAGE OK`.

- [ ] **Step 5: Commit**

```bash
git add banking/views.py banking/urls.py banking/templates/banking/electricity.html
git commit -m "Add electricity and TV bill payment page"
```

---

### Task 17: Loan page

**Files:**
- Create: `banking/templates/banking/loan.html`
- Modify: `banking/views.py`
- Modify: `banking/urls.py`

- [ ] **Step 1: Add the view**

Append to `banking/views.py`:

```python
@login_required
def loan(request):
    return render(request, "banking/loan.html", {"account": request.user.account})
```

- [ ] **Step 2: Add the URL**

In `banking/urls.py`, add after `electricity`:

```python
    path("loan/", views.loan, name="loan"),
```

- [ ] **Step 3: Write `loan.html`**

```html
{% extends "banking/dashboard_base.html" %}
{% block title %}Loans - Stanbic IBTC{% endblock %}
{% block content %}
<div class="bg-white rounded-xl shadow-sm overflow-hidden">
  <div class="px-4 pt-4 pb-2 text-base font-bold">EZCash</div>
  <button type="button" onclick="openLoanModal()" class="w-full text-left px-4 py-4 border-t border-gray-100">
    <div class="flex justify-between items-center"><span class="text-sm font-medium">EZCash Loan</span><span class="text-gray-400">›</span></div>
    <small class="text-xs text-gray-500 block mt-1">Apply for a quick cash loan</small>
  </button>
  <button type="button" class="w-full text-left px-4 py-4 border-t border-gray-100">
    <div class="flex justify-between items-center"><span class="text-sm font-medium">EZCash Repayment</span><span class="text-gray-400">›</span></div>
    <small class="text-xs text-gray-500 block mt-1">Pay back an existing EZCash loan</small>
  </button>
  <button type="button" class="w-full text-left px-4 py-4 border-t border-gray-100">
    <div class="flex justify-between items-center"><span class="text-sm font-medium">EZCash History</span><span class="text-gray-400">›</span></div>
    <small class="text-xs text-gray-500 block mt-1">View previous loan requests</small>
  </button>
</div>

<div id="loanOverlay" onclick="this.classList.add('hidden')" class="fixed inset-0 bg-black/45 hidden items-center justify-center p-6 z-50">
  <div onclick="event.stopPropagation()" class="bg-white w-full max-w-xs rounded-2xl p-7 text-center">
    <div class="w-9 h-9 mx-auto mb-3.5 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold">i</div>
    <p class="text-base font-semibold mb-5">You are not eligible for EzCash loan</p>
    <button type="button" onclick="document.getElementById('loanOverlay').classList.add('hidden')" class="w-full bg-brand text-white rounded-lg py-3 font-bold">Close</button>
  </div>
</div>
{% block extra_js %}
<script>
  function openLoanModal() {
    const el = document.getElementById('loanOverlay');
    el.classList.remove('hidden');
    el.classList.add('flex');
  }
</script>
{% endblock %}
{% endblock %}
```

- [ ] **Step 4: Verify (also re-run the full `check` from Task 9, since `airtime` and `loan` now both exist)**

```bash
python manage.py check
python manage.py runserver 0:8000 &
sleep 2
curl -s -b /tmp/cookies2.txt http://127.0.0.1:8000/loan/ -o /tmp/loan.html -w "%{http_code}\n"
grep -q "EZCash Loan" /tmp/loan.html && echo "LOAN PAGE OK"
kill %1
```
Expected: `System check identified no issues (0 silenced).`, `200`, `LOAN PAGE OK`.

- [ ] **Step 5: Commit**

```bash
git add banking/views.py banking/urls.py banking/templates/banking/loan.html
git commit -m "Add loan page with eligibility modal"
```

---

### Task 18: Payments page (DisCo directory)

**Files:**
- Create: `banking/templates/banking/payments.html`
- Modify: `banking/views.py`
- Modify: `banking/urls.py`

- [ ] **Step 1: Add the static provider list and view**

Append to `banking/views.py`:

```python
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
```

- [ ] **Step 2: Add the URL**

In `banking/urls.py`, add after `loan`:

```python
    path("payments/", views.payments, name="payments"),
```

- [ ] **Step 3: Write `payments.html`**

```html
{% extends "banking/dashboard_base.html" %}
{% block title %}Payments - Stanbic IBTC{% endblock %}
{% block content %}
<div class="bg-white mx-0 rounded-lg px-3.5 py-2.5 flex justify-between items-center shadow-sm mb-4 text-sm font-medium">
  Electricity <span class="text-gray-400 text-xs">▼ Select a module</span>
</div>
<div class="bg-white rounded-xl shadow-sm overflow-hidden">
  <div class="p-3">
    <input type="search" placeholder="search" class="w-full border border-gray-300 rounded-lg px-3.5 py-2.5 text-sm">
  </div>
  {% for provider in providers %}
    <button type="button" class="w-full flex justify-between px-4 py-3.5 text-xs font-semibold border-t border-gray-100 text-left">{{ provider|upper }} <span class="text-gray-400">›</span></button>
  {% endfor %}
</div>
{% endblock %}
```

- [ ] **Step 4: Verify**

```bash
python manage.py runserver 0:8000 &
sleep 2
curl -s -b /tmp/cookies2.txt http://127.0.0.1:8000/payments/ -o /tmp/payments.html -w "%{http_code}\n"
grep -q "IKEJA ELECTRICITY" /tmp/payments.html && echo "PAYMENTS PAGE OK"
kill %1
```
Expected: `200`, `PAYMENTS PAGE OK`.

- [ ] **Step 5: Commit**

```bash
git add banking/views.py banking/urls.py banking/templates/banking/payments.html
git commit -m "Add payments (DisCo directory) page"
```

---

### Task 19: Approvals page

**Files:**
- Create: `banking/templates/banking/approvals.html`
- Modify: `banking/views.py`
- Modify: `banking/urls.py`

- [ ] **Step 1: Add the view**

Append to `banking/views.py`:

```python
@login_required
def approvals(request):
    return render(request, "banking/approvals.html", {"account": request.user.account})
```

- [ ] **Step 2: Add the URL**

In `banking/urls.py`, add after `payments`:

```python
    path("approvals/", views.approvals, name="approvals"),
```

- [ ] **Step 3: Write `approvals.html`**

```html
{% extends "banking/dashboard_base.html" %}
{% block title %}Approvals - Stanbic IBTC{% endblock %}
{% block content %}
<div class="bg-white mx-0 rounded-lg px-3.5 py-2.5 flex justify-between items-center shadow-sm mb-4 text-sm font-medium">
  Pending <span class="text-gray-400 text-xs">▼ Select A Module</span>
</div>
<div class="bg-white rounded-xl shadow-sm p-4">
  <button type="button" class="w-full border border-gray-300 rounded-lg px-3.5 py-2.5 text-sm text-left mb-2.5">All ▼ Select Transaction</button>
  <input type="search" placeholder="Type to search" class="w-full border border-gray-300 rounded-lg px-3.5 py-2.5 text-sm mb-2.5">
  <button type="button" class="border-2 border-brand text-brand rounded-lg px-3.5 py-2 text-sm font-bold">↻ REFRESH</button>
  <div class="mt-3.5 bg-brand text-white rounded-md grid grid-cols-[1fr_90px] px-3 py-2.5 text-sm font-bold">
    <span>Request Details</span><span>Action</span>
  </div>
  <p class="text-center text-gray-500 py-7 text-sm">0 of 0</p>
  <div class="flex justify-between items-center mt-4 text-sm">
    <span>Items per page:
      <select class="border border-gray-300 rounded px-2 py-1 ml-1">
        <option>25</option><option selected>50</option><option>100</option><option>200</option>
      </select>
    </span>
    <span class="text-gray-400">&lt; &gt;</span>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 4: Verify**

```bash
python manage.py runserver 0:8000 &
sleep 2
curl -s -b /tmp/cookies2.txt http://127.0.0.1:8000/approvals/ -o /tmp/approvals.html -w "%{http_code}\n"
grep -q "Request Details" /tmp/approvals.html && echo "APPROVALS PAGE OK"
kill %1
```
Expected: `200`, `APPROVALS PAGE OK`.

- [ ] **Step 5: Commit**

```bash
git add banking/views.py banking/urls.py banking/templates/banking/approvals.html
git commit -m "Add approvals page"
```

---

### Task 20: Profile management

**Files:**
- Create: `banking/templates/banking/profile.html`
- Modify: `banking/views.py`
- Modify: `banking/urls.py`

- [ ] **Step 1: Add the view**

Append to `banking/views.py`:

```python
@login_required
def profile(request):
    return render(request, "banking/profile.html", {"account": request.user.account})
```

- [ ] **Step 2: Add the URL**

In `banking/urls.py`, add after `approvals`:

```python
    path("profile/", views.profile, name="profile"),
```

- [ ] **Step 3: Write `profile.html`**

The original page had a stray duplicate nav accidentally pasted inside its select-bar; this rebuild drops that duplication since the shared bottom-nav/side-menu already cover navigation:

```html
{% extends "banking/dashboard_base.html" %}
{% block title %}Profile Management - Stanbic IBTC{% endblock %}
{% block content %}
<div class="bg-white mx-0 rounded-lg px-3.5 py-2.5 flex justify-between items-center shadow-sm mb-4 text-sm font-medium">
  Profile Management <span class="text-gray-400 text-xs">▼ Select</span>
</div>
<div class="bg-white rounded-xl shadow-sm p-4">
  <h2 class="text-base font-semibold mb-3">Profile Management</h2>
  <a href="{% url 'view_profile' %}" class="block bg-gray-50 border border-gray-200 rounded-lg px-4 py-3.5 mb-2.5 text-sm">View Profile</a>
  <button type="button" class="w-full text-left bg-gray-50 border border-gray-200 rounded-lg px-4 py-3.5 mb-2.5 text-sm">Update Contact Details</button>
  <button type="button" class="w-full text-left bg-gray-50 border border-gray-200 rounded-lg px-4 py-3.5 mb-2.5 text-sm">Change Password</button>
  <button type="button" class="w-full text-left bg-gray-50 border border-gray-200 rounded-lg px-4 py-3.5 mb-2.5 text-sm">Transaction PIN</button>
  <button type="button" class="w-full text-left bg-gray-50 border border-gray-200 rounded-lg px-4 py-3.5 text-sm">Linked Devices</button>
</div>
{% endblock %}
```

- [ ] **Step 4: Verify**

```bash
python manage.py runserver 0:8000 &
sleep 2
curl -s -b /tmp/cookies2.txt http://127.0.0.1:8000/profile/ -o /tmp/profile.html -w "%{http_code}\n"
grep -q "View Profile" /tmp/profile.html && echo "PROFILE PAGE OK"
kill %1
```
Expected: `200`, `PROFILE PAGE OK`.

- [ ] **Step 5: Commit**

```bash
git add banking/views.py banking/urls.py banking/templates/banking/profile.html
git commit -m "Add profile management page"
```

---

### Task 21: View profile

**Files:**
- Create: `banking/templates/banking/view_profile.html`
- Modify: `banking/views.py`
- Modify: `banking/urls.py`

- [ ] **Step 1: Add the view**

Append to `banking/views.py`:

```python
@login_required
def view_profile(request):
    return render(request, "banking/view_profile.html", {"account": request.user.account})
```

- [ ] **Step 2: Add the URL**

In `banking/urls.py`, add after `profile`:

```python
    path("profile/view/", views.view_profile, name="view_profile"),
```

- [ ] **Step 3: Write `view_profile.html`**

Shows the real signed-up user's data instead of the original's hardcoded demo person:

```html
{% extends "banking/dashboard_base.html" %}
{% block title %}View Profile - Stanbic IBTC{% endblock %}
{% block content %}
<div class="bg-white rounded-xl shadow-sm overflow-hidden">
  <div class="bg-gradient-to-br from-brand to-accent text-white text-center px-5 py-7">
    <div class="relative w-24 h-24 mx-auto mb-3">
      <div class="w-full h-full rounded-full bg-white text-brand font-bold text-3xl flex items-center justify-center border-4 border-white/60">
        {{ account.full_name|slice:":2"|upper }}
      </div>
      <span class="absolute bottom-0 right-0 bg-teal-400 text-white text-[10px] font-bold px-2 py-0.5 rounded-full border-2 border-brand">VERIFIED</span>
    </div>
    <h2 class="text-lg font-semibold">{{ account.full_name }}</h2>
    <p class="text-sm opacity-90">Acc No: {{ account.account_number }}</p>
  </div>
  <div class="p-5">
    <div class="text-xs uppercase text-gray-400 tracking-wide border-b border-gray-100 pb-1.5 mb-4">Personal Information</div>
    <div class="flex justify-between items-center mb-4 text-sm">
      <span class="text-gray-500">Email Address</span><span class="font-semibold">{{ account.user.email }}</span>
    </div>
    <div class="flex justify-between items-center mb-4 text-sm">
      <span class="text-gray-500">Phone Number</span><span class="font-semibold">{{ account.phone }}</span>
    </div>
    <div class="flex justify-between items-center mb-6 text-sm">
      <span class="text-gray-500">BVN</span><span class="font-semibold">{{ account.bvn|slice:":3" }}******{{ account.bvn|slice:"-2:" }}</span>
    </div>
    <div class="text-xs uppercase text-gray-400 tracking-wide border-b border-gray-100 pb-1.5 mb-4">Account Details</div>
    <div class="flex justify-between items-center mb-4 text-sm">
      <span class="text-gray-500">Account Type</span><span class="font-semibold">{{ account.get_account_type_display }}</span>
    </div>
    <div class="flex justify-between items-center text-sm">
      <span class="text-gray-500">Branch</span><span class="font-semibold">Walter Carrington, Lagos</span>
    </div>
  </div>
  <div class="flex gap-3 px-5 pb-5">
    <button type="button" class="flex-1 border border-brand text-brand rounded-md py-2.5 text-sm font-semibold">Edit Profile</button>
    <a href="{% url 'dashboard' %}" class="flex-1 bg-brand text-white rounded-md py-2.5 text-sm font-semibold text-center">Back to Dashboard</a>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 4: Verify**

```bash
python manage.py runserver 0:8000 &
sleep 2
curl -s -b /tmp/cookies2.txt http://127.0.0.1:8000/profile/view/ -o /tmp/view_profile.html -w "%{http_code}\n"
grep -q "Personal Information" /tmp/view_profile.html && echo "VIEW PROFILE OK"
kill %1
```
Expected: `200`, `VIEW PROFILE OK`.

- [ ] **Step 5: Commit**

```bash
git add banking/views.py banking/urls.py banking/templates/banking/view_profile.html
git commit -m "Add view profile page with real user data"
```

---

### Task 22: Transaction receipt

**Files:**
- Create: `banking/templates/banking/transaction.html`
- Modify: `banking/views.py`
- Modify: `banking/urls.py`

- [ ] **Step 1: Add the view**

Append to `banking/views.py`:

```python
@login_required
def transaction_receipt(request):
    return render(request, "banking/transaction.html", {"account": request.user.account})
```

- [ ] **Step 2: Add the URL**

In `banking/urls.py`, add after `view_profile`:

```python
    path("transaction/", views.transaction_receipt, name="transaction_receipt"),
```

- [ ] **Step 3: Write `transaction.html`**

Static demo receipt (per spec — transaction history is not DB-backed), with working print/download buttons:

```html
{% extends "banking/dashboard_base.html" %}
{% block title %}Transaction Receipt - Stanbic IBTC{% endblock %}
{% block content %}
<div class="bg-white rounded-lg shadow-sm overflow-hidden border-t-8 border-brand">
  <div class="text-center px-6 pt-7 pb-5 border-b border-dashed border-gray-200">
    <div class="text-xl font-extrabold text-brand uppercase tracking-wide">Stanbic IBTC</div>
    <div class="text-[11px] text-gray-400 uppercase tracking-widest mb-5">A member of Standard Bank Group</div>
    <div class="text-base font-semibold text-gray-800 mb-1.5">Transaction Receipt</div>
    <div class="text-2xl font-bold text-brand mt-2">NGN 50,000.00</div>
    <span class="inline-block bg-teal-50 text-teal-700 text-xs font-semibold px-3 py-1 rounded-full mt-2 uppercase">Successful</span>
  </div>
  <div class="px-6 py-2">
    <div class="flex justify-between py-3 border-b border-gray-100 text-sm"><span class="text-gray-500">Transaction Date</span><span class="font-semibold text-right">27-Aug-2026 14:32:10</span></div>
    <div class="flex justify-between py-3 border-b border-gray-100 text-sm"><span class="text-gray-500">Transaction Type</span><span class="font-semibold text-right">Inter-Bank Transfer</span></div>
    <div class="flex justify-between py-3 border-b border-gray-100 text-sm"><span class="text-gray-500">Sender Name</span><span class="font-semibold text-right">{{ account.full_name|upper }}</span></div>
    <div class="flex justify-between py-3 border-b border-gray-100 text-sm"><span class="text-gray-500">Sender Account</span><span class="font-semibold text-right">{{ account.account_number }}</span></div>
    <div class="flex justify-between py-3 border-b border-gray-100 text-sm"><span class="text-gray-500">Beneficiary Bank</span><span class="font-semibold text-right">Access Bank</span></div>
    <div class="flex justify-between py-3 border-b border-gray-100 text-sm"><span class="text-gray-500">Beneficiary Name</span><span class="font-semibold text-right">AMINA BELLO INVESTMENT LTD</span></div>
    <div class="flex justify-between py-3 border-b border-gray-100 text-sm"><span class="text-gray-500">Beneficiary Account</span><span class="font-semibold text-right">0123456789</span></div>
    <div class="flex justify-between py-3 border-b border-gray-100 text-sm"><span class="text-gray-500">Narration</span><span class="font-semibold text-right">Project supply payment phase 1</span></div>
    <div class="flex justify-between py-3 text-sm"><span class="text-gray-500">Reference Number</span><span class="font-semibold text-right">SIBTC/FT/20260827/984321055</span></div>
  </div>
  <div class="bg-gray-50 border-t border-gray-100 px-6 py-5 text-center">
    <p class="text-[11px] text-gray-400 mb-4 leading-relaxed">This is an automated transaction receipt generated by Stanbic IBTC Bank. Financial transactions are subject to final clearing.</p>
    <div class="flex gap-2.5 justify-center">
      <button type="button" onclick="window.print()" class="bg-brand text-white text-xs font-semibold rounded px-4 py-2">Print Receipt</button>
      <button type="button" onclick="alert('Download triggered')" class="bg-gray-200 text-gray-600 text-xs font-semibold rounded px-4 py-2">Download PDF</button>
    </div>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 4: Verify**

```bash
python manage.py runserver 0:8000 &
sleep 2
curl -s -b /tmp/cookies2.txt http://127.0.0.1:8000/transaction/ -o /tmp/transaction.html -w "%{http_code}\n"
grep -q "Print Receipt" /tmp/transaction.html && echo "TRANSACTION RECEIPT OK"
kill %1
```
Expected: `200`, `TRANSACTION RECEIPT OK`.

- [ ] **Step 5: Commit**

```bash
git add banking/views.py banking/urls.py banking/templates/banking/transaction.html
git commit -m "Add transaction receipt page"
```

---

### Task 23: Final cleanup and QA pass

**Files:**
- Delete: all 18 original root-level `*.html` files (now superseded by Django templates)
- Modify: `README.md`

- [ ] **Step 1: Confirm every original page has a working replacement**

```bash
python manage.py runserver 0:8000 &
sleep 2
for path in / /login/ /open/ /home/ /account/ /view-accounts/ /transfer/ /beneficiary/ /bulk-transfer/ /airtime/ /electricity/ /loan/ /payments/ /approvals/ /profile/ /profile/view/ /transaction/; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -b /tmp/cookies2.txt "http://127.0.0.1:8000$path")
  echo "$path -> $code"
done
kill %1
```
Expected: every path returns `200` (public paths `/`, `/login/`, `/open/` return `200` even without the cookie jar; the rest return `200` because `/tmp/cookies2.txt` holds the logged-in session from earlier tasks — if that session expired, log in again first via the Task 8 curl sequence).

- [ ] **Step 2: Remove the superseded static HTML files from the repo root**

```bash
git rm account.html airtime.html approvals.html bankings.html beneficiary.html bulk.html electricity.html index.html loan.html login.html logout.html open.html payments.html profile.html transaction.html transfer.html view.html viewprofile.html
```
(These are fully replaced by the Django templates added in Tasks 6–22; their content was read and ported faithfully in those tasks.)

- [ ] **Step 3: Update `README.md` with run instructions**

Read the current `README.md` and append a "Running the prototype" section under the existing content:

```markdown

## Running the prototype

```bash
python3 -m venv venv
source venv/bin/activate
pip install django
python manage.py migrate
python manage.py runserver
```

Visit http://127.0.0.1:8000/ — sign up via "Open an Account" to get a generated account number and password, then log in.
```

- [ ] **Step 4: Full manual click-through**

Start the server (`python manage.py runserver`), open `http://127.0.0.1:8000/` in a browser, and manually walk the full path: landing → Open an Account (submit the form) → note the generated email/password on the success screen → Sign In → Home → open the side menu and visit every menu item → go to Transfer, submit the form, confirm the 10s "Processing…" then "Completed" overlay appears and the Done button returns to Home → repeat the submit-and-wait check on Beneficiary Transfer, Bulk Transfer, Airtime, and Electricity → Logout → confirm redirected to the logout confirmation page and that visiting `/home/` afterward redirects to `/login/`.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "Remove superseded static HTML pages and document how to run the prototype"
```
