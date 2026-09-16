# Profile Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Profile Management page's "Update Details", "Change Password", and "Transaction PIN" buttons actually work (inline forms, no new pages), drop "Linked Devices", and gate every existing fake-transaction form (transfer, beneficiary, bulk, airtime, electricity/TV) behind a PIN-entry modal once a PIN has been set.

**Architecture:** One new `Account.transaction_pin` field (hashed via Django's existing password hasher). Four new POST-only views on the existing `banking` app (`update_details`, `change_password`, `set_pin`, `verify_pin`), all `@login_required` + `@require_POST`, operating only on `request.user`/`request.user.account`. `profile.html` gets three inline toggle forms replacing the dead buttons. A new shared `_pin_modal.html` partial (included from `dashboard_base.html`, same pattern as `_processing_overlay.html`) plus a `data-has-pin` attribute on the page wrapper let `app.js` generically gate every `data-fake-transaction` form with zero per-page template changes.

**Tech Stack:** Django (existing project), vanilla JS `fetch()` for the PIN-verification AJAX call, Django's `messages` framework for success/error feedback.

**No automated tests are written in this plan** — the project's README explicitly says to avoid writing tests for this prototype. Verification is manual (`manage.py check`, `manage.py shell`, curl) after each task.

---

### Task 1: `transaction_pin` field + migration

**Files:**
- Modify: `banking/models.py`
- Create: `banking/migrations/0002_account_transaction_pin.py` (generated)

- [ ] **Step 1: Add the field**

In `banking/models.py`, add `transaction_pin` right after `balance`:

```python
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("1000000000.00"))
    transaction_pin = models.CharField(max_length=128, blank=True, default="")
```

- [ ] **Step 2: Generate and run the migration**

```bash
source venv/bin/activate
python manage.py makemigrations banking
python manage.py migrate
```
Expected: a new `banking/migrations/0002_account_transaction_pin.py` is created and applies cleanly.

- [ ] **Step 3: Verify**

```bash
python manage.py check
python manage.py shell -c "from banking.models import Account; print(Account._meta.get_field('transaction_pin').default)"
```
Expected: 0 issues, and the second command prints an empty string (`''`).

- [ ] **Step 4: Commit**

```bash
git add banking/models.py banking/migrations
git commit -m "Add transaction_pin field to Account"
```

---

### Task 2: `update_details` view

**Files:**
- Modify: `banking/views.py`
- Modify: `banking/urls.py`

- [ ] **Step 1: Add new imports**

At the top of `banking/views.py`, replace the existing import block with (this adds everything needed for this task AND Tasks 3-5, so those tasks don't need to touch the import block again):

```python
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
```

- [ ] **Step 2: Add the view**

Append to the end of `banking/views.py` (after `transaction_receipt`):

```python
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
```

- [ ] **Step 3: Add the URL**

In `banking/urls.py`, add after `transaction_receipt`:

```python
    path("profile/update-details/", views.update_details, name="update_details"),
```

- [ ] **Step 4: Verify**

```bash
python manage.py check
```
Expected: 0 issues. (This view isn't reachable from the UI yet — `profile.html` is rewired in Task 6 — so no end-to-end check yet; `check` just confirms no import/syntax errors.)

- [ ] **Step 5: Commit**

```bash
git add banking/views.py banking/urls.py
git commit -m "Add update_details view for editing account details"
```

---

### Task 3: `change_password` view

**Files:**
- Modify: `banking/views.py`
- Modify: `banking/urls.py`

- [ ] **Step 1: Add the view**

Append to the end of `banking/views.py`:

```python
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
```

- [ ] **Step 2: Add the URL**

In `banking/urls.py`, add after `update_details`:

```python
    path("profile/change-password/", views.change_password, name="change_password"),
```

- [ ] **Step 3: Verify**

```bash
python manage.py check
```
Expected: 0 issues.

- [ ] **Step 4: Commit**

```bash
git add banking/views.py banking/urls.py
git commit -m "Add change_password view requiring current password"
```

---

### Task 4: `set_pin` view

**Files:**
- Modify: `banking/views.py`
- Modify: `banking/urls.py`

- [ ] **Step 1: Add the view**

Append to the end of `banking/views.py`:

```python
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
```

- [ ] **Step 2: Add the URL**

In `banking/urls.py`, add after `change_password`:

```python
    path("profile/set-pin/", views.set_pin, name="set_pin"),
```

- [ ] **Step 3: Verify**

```bash
python manage.py check
```
Expected: 0 issues.

- [ ] **Step 4: Commit**

```bash
git add banking/views.py banking/urls.py
git commit -m "Add set_pin view for setting/changing the transaction PIN"
```

---

### Task 5: `verify_pin` view

**Files:**
- Modify: `banking/views.py`
- Modify: `banking/urls.py`

- [ ] **Step 1: Add the view**

Append to the end of `banking/views.py`:

```python
@login_required
@require_POST
def verify_pin(request):
    pin = request.POST.get("pin", "")
    account = request.user.account

    if not account.transaction_pin:
        return JsonResponse({"valid": False})

    return JsonResponse({"valid": check_password(pin, account.transaction_pin)})
```

- [ ] **Step 2: Add the URL**

In `banking/urls.py`, add after `set_pin`:

```python
    path("profile/verify-pin/", views.verify_pin, name="verify_pin"),
```

- [ ] **Step 3: Verify end-to-end (this view is fully testable now, independent of the UI)**

```bash
python manage.py check
python manage.py runserver 0:8000 &
sleep 2
rm -f /tmp/cookies_pin.txt
# Sign up + log in a fresh test user
curl -s -c /tmp/cookies_pin.txt http://127.0.0.1:8000/open/ -o /dev/null
TOKEN=$(grep csrftoken /tmp/cookies_pin.txt | awk '{print $7}')
curl -s -b /tmp/cookies_pin.txt -c /tmp/cookies_pin.txt \
  -d "csrfmiddlewaretoken=$TOKEN&fullname=Pin+Test&phone=08010000001&email=pintest@example.com&bvn=10101010101&account_type=savings" \
  -o /tmp/signup_pin.html \
  http://127.0.0.1:8000/open/
python manage.py shell -c "
from django.contrib.auth.models import User
u = User.objects.get(username='pintest@example.com')
u.set_password('pinpass123')
u.save()
"
TOKEN2=$(grep csrftoken /tmp/cookies_pin.txt | awk '{print $7}')
curl -s -b /tmp/cookies_pin.txt -c /tmp/cookies_pin.txt \
  -d "csrfmiddlewaretoken=$TOKEN2&email=pintest@example.com&password=pinpass123" \
  -o /dev/null -w "login: %{http_code}\n" \
  http://127.0.0.1:8000/login/
# Set a PIN directly via Django (set_pin view isn't wired into the UI yet, so use ORM)
python manage.py shell -c "
from banking.models import Account
from django.contrib.auth.hashers import make_password
a = Account.objects.get(user__username='pintest@example.com')
a.transaction_pin = make_password('1234')
a.save()
"
# Verify with correct PIN
TOKEN3=$(grep csrftoken /tmp/cookies_pin.txt | awk '{print $7}')
curl -s -b /tmp/cookies_pin.txt -c /tmp/cookies_pin.txt \
  -H "X-CSRFToken: $TOKEN3" \
  -d "pin=1234" \
  http://127.0.0.1:8000/profile/verify-pin/
echo ""
# Verify with wrong PIN
curl -s -b /tmp/cookies_pin.txt -c /tmp/cookies_pin.txt \
  -H "X-CSRFToken: $TOKEN3" \
  -d "pin=9999" \
  http://127.0.0.1:8000/profile/verify-pin/
kill %1
```
Expected: the correct-PIN call returns `{"valid": true}` and the wrong-PIN call returns `{"valid": false}`.

- [ ] **Step 4: Commit**

```bash
git add banking/views.py banking/urls.py
git commit -m "Add verify_pin JSON endpoint"
```

---

### Task 6: Wire up `profile.html`

**Files:**
- Modify: `banking/templates/banking/profile.html`

- [ ] **Step 1: Replace the file's content block**

Replace the entire contents of `banking/templates/banking/profile.html`:

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

  <button type="button" onclick="document.getElementById('detailsForm').classList.toggle('hidden')" class="w-full text-left bg-gray-50 border border-gray-200 rounded-lg px-4 py-3.5 mb-2.5 text-sm">Update Details</button>
  <form method="POST" action="{% url 'update_details' %}" id="detailsForm" class="hidden mb-2.5 bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-3">
    {% csrf_token %}
    <div>
      <label class="block text-xs font-medium text-gray-600 mb-1">Full Name</label>
      <input type="text" name="full_name" value="{{ account.full_name }}" required class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm">
    </div>
    <div>
      <label class="block text-xs font-medium text-gray-600 mb-1">Phone</label>
      <input type="text" name="phone" value="{{ account.phone }}" required class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm">
    </div>
    <div>
      <label class="block text-xs font-medium text-gray-600 mb-1">Email</label>
      <input type="email" name="email" value="{{ account.user.email }}" required class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm">
    </div>
    <div>
      <label class="block text-xs font-medium text-gray-600 mb-1">BVN</label>
      <input type="text" name="bvn" value="{{ account.bvn }}" maxlength="11" required class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm">
    </div>
    <button type="submit" class="w-full bg-brand text-white rounded-lg py-2.5 text-sm font-semibold">Save Details</button>
  </form>

  <button type="button" onclick="document.getElementById('passwordForm').classList.toggle('hidden')" class="w-full text-left bg-gray-50 border border-gray-200 rounded-lg px-4 py-3.5 mb-2.5 text-sm">Change Password</button>
  <form method="POST" action="{% url 'change_password' %}" id="passwordForm" class="hidden mb-2.5 bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-3">
    {% csrf_token %}
    <div>
      <label class="block text-xs font-medium text-gray-600 mb-1">Current Password</label>
      <input type="password" name="current_password" required class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm">
    </div>
    <div>
      <label class="block text-xs font-medium text-gray-600 mb-1">New Password</label>
      <input type="password" name="new_password" required class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm">
    </div>
    <div>
      <label class="block text-xs font-medium text-gray-600 mb-1">Confirm New Password</label>
      <input type="password" name="confirm_password" required class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm">
    </div>
    <button type="submit" class="w-full bg-brand text-white rounded-lg py-2.5 text-sm font-semibold">Save Password</button>
  </form>

  <button type="button" onclick="document.getElementById('pinForm').classList.toggle('hidden')" class="w-full text-left bg-gray-50 border border-gray-200 rounded-lg px-4 py-3.5 text-sm">Transaction PIN</button>
  <form method="POST" action="{% url 'set_pin' %}" id="pinForm" class="hidden mt-2.5 bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-3">
    {% csrf_token %}
    <div>
      <label class="block text-xs font-medium text-gray-600 mb-1">New 4-Digit PIN</label>
      <input type="password" name="pin" inputmode="numeric" pattern="[0-9]{4}" maxlength="4" required class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm">
    </div>
    <div>
      <label class="block text-xs font-medium text-gray-600 mb-1">Confirm PIN</label>
      <input type="password" name="confirm_pin" inputmode="numeric" pattern="[0-9]{4}" maxlength="4" required class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm">
    </div>
    <button type="submit" class="w-full bg-brand text-white rounded-lg py-2.5 text-sm font-semibold">Save PIN</button>
  </form>
</div>
{% endblock %}
```

Note: "Linked Devices" is gone — it's not carried over into this file.

- [ ] **Step 2: Verify**

```bash
python manage.py check
```
Expected: 0 issues.

- [ ] **Step 3: Commit**

```bash
git add banking/templates/banking/profile.html
git commit -m "Wire profile page to update-details/change-password/set-pin forms"
```

---

### Task 7: Messages banner + PIN modal partial + `dashboard_base.html` wiring

**Files:**
- Create: `banking/templates/banking/_pin_modal.html`
- Modify: `banking/templates/banking/dashboard_base.html`

- [ ] **Step 1: Write `_pin_modal.html`**

```html
<div id="pinModal" class="fixed inset-0 bg-black/50 hidden items-center justify-center z-50 px-6">
  {% csrf_token %}
  <div class="bg-white rounded-2xl p-8 text-center w-72">
    <p class="font-semibold text-gray-800 mb-1">Enter Transaction PIN</p>
    <p class="text-xs text-gray-500 mb-4">Enter your 4-digit PIN to continue</p>
    <input id="pinModalInput" type="password" inputmode="numeric" pattern="[0-9]{4}" maxlength="4" class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-center text-lg tracking-widest mb-2">
    <p id="pinModalError" class="hidden text-xs text-red-600 mb-2">Incorrect PIN. Please try again.</p>
    <div class="flex gap-2.5 mt-2">
      <button type="button" id="pinModalCancel" class="flex-1 border border-gray-300 text-gray-600 rounded-lg py-2.5 text-sm font-semibold">Cancel</button>
      <button type="button" id="pinModalSubmit" class="flex-1 bg-brand text-white rounded-lg py-2.5 text-sm font-semibold">Confirm</button>
    </div>
  </div>
</div>
```

- [ ] **Step 2: Update `dashboard_base.html`**

Replace the entire contents of `banking/templates/banking/dashboard_base.html`:

```html
{% extends "banking/base.html" %}
{% block body %}
<div class="max-w-md mx-auto bg-gray-100 min-h-screen relative pb-20" data-has-pin="{{ request.user.account.transaction_pin|yesno:'true,false' }}">
  {% include "banking/_sidemenu.html" %}
  {% include "banking/_header.html" %}
  <main class="px-4 pt-4">
    {% if messages %}
      <div class="mb-4 space-y-2">
        {% for message in messages %}
          <div class="rounded-lg px-4 py-3 text-sm {% if message.tags == 'error' %}bg-red-50 text-red-700{% else %}bg-green-50 text-green-700{% endif %}">{{ message }}</div>
        {% endfor %}
      </div>
    {% endif %}
    {% block content %}{% endblock %}
  </main>
  {% include "banking/_bottomnav.html" %}
  {% include "banking/_processing_overlay.html" %}
  {% include "banking/_pin_modal.html" %}
</div>
{% block extra_js %}{% endblock %}
{% endblock %}
```

- [ ] **Step 3: Verify**

```bash
python manage.py check
```
Expected: 0 issues. Then confirm the dashboard still renders for a logged-in user without a PIN set (the attribute should read `data-has-pin="false"`):

```bash
python manage.py runserver 0:8000 &
sleep 2
curl -s -b /tmp/cookies_pin.txt http://127.0.0.1:8000/home/ -o /tmp/home_check.html -w "%{http_code}\n"
grep -o 'data-has-pin="[a-z]*"' /tmp/home_check.html
kill %1
```
Expected: `200`, and since the `pintest@example.com` user from Task 5 already has a PIN set, this should print `data-has-pin="true"`. (If you want to double check the `false` case too, run the same curl against a freshly signed-up user with no PIN.)

- [ ] **Step 4: Commit**

```bash
git add banking/templates/banking/_pin_modal.html banking/templates/banking/dashboard_base.html
git commit -m "Add shared PIN modal and messages banner to dashboard chrome"
```

---

### Task 8: PIN gate in `app.js`

**Files:**
- Modify: `banking/static/banking/js/app.js`

- [ ] **Step 1: Replace `initFakeTransactionForms`**

In `banking/static/banking/js/app.js`, replace the entire `initFakeTransactionForms` function (currently lines 29-76) with:

```javascript
function initFakeTransactionForms() {
  const overlay = document.getElementById('processingOverlay');
  const processing = document.getElementById('processingState');
  const success = document.getElementById('successState');
  const doneBtn = document.getElementById('processingDoneBtn');
  const pinModal = document.getElementById('pinModal');
  const pinInput = document.getElementById('pinModalInput');
  const pinError = document.getElementById('pinModalError');
  const pinSubmit = document.getElementById('pinModalSubmit');
  const pinCancel = document.getElementById('pinModalCancel');

  function showProcessingOverlay() {
    if (!overlay) return;
    overlay.classList.remove('hidden');
    overlay.classList.add('flex');
    processing.classList.remove('hidden');
    success.classList.add('hidden');

    setTimeout(function () {
      processing.classList.add('hidden');
      success.classList.remove('hidden');
    }, 10000);
  }

  function hasPin() {
    const wrapper = document.querySelector('[data-has-pin]');
    return !!wrapper && wrapper.dataset.hasPin === 'true';
  }

  function showPinModal(onVerified) {
    if (!pinModal) { onVerified(); return; }
    pinInput.value = '';
    pinError.classList.add('hidden');
    pinModal.classList.remove('hidden');
    pinModal.classList.add('flex');

    function cleanup() {
      pinModal.classList.add('hidden');
      pinModal.classList.remove('flex');
      pinSubmit.removeEventListener('click', onSubmit);
      pinCancel.removeEventListener('click', onCancel);
    }

    function onCancel() {
      cleanup();
    }

    function onSubmit() {
      const csrfToken = pinModal.querySelector('[name=csrfmiddlewaretoken]').value;
      const body = new FormData();
      body.append('pin', pinInput.value);
      fetch('/profile/verify-pin/', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken },
        body: body,
      })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          if (data.valid) {
            cleanup();
            onVerified();
          } else {
            pinError.classList.remove('hidden');
            pinInput.value = '';
          }
        });
    }

    pinSubmit.addEventListener('click', onSubmit);
    pinCancel.addEventListener('click', onCancel);
  }

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

      if (hasPin()) {
        showPinModal(showProcessingOverlay);
      } else {
        showProcessingOverlay();
      }
    });
  });

  if (doneBtn) {
    doneBtn.addEventListener('click', function () {
      window.location.href = doneBtn.dataset.redirect;
    });
  }
}
```

The rest of the file (`toggleMenu`, `initBalanceToggles`, `initCopyButtons`, the `DOMContentLoaded` listener) is unchanged.

- [ ] **Step 2: Verify**

```bash
python manage.py check
```
Expected: 0 issues (this is a static JS file, so `check` won't catch JS errors — it's just confirming nothing else broke). Then manually sanity-check the JS is syntactically valid:

```bash
node --check banking/static/banking/js/app.js
```
Expected: no output (exit code 0) — confirms valid JavaScript syntax. (If `node` isn't available, skip this and rely on Task 9's live browser/curl walkthrough instead.)

- [ ] **Step 3: Commit**

```bash
git add banking/static/banking/js/app.js
git commit -m "Gate fake-transaction forms behind a PIN-entry modal"
```

---

### Task 9: End-to-end verification

**Files:** none (verification only)

- [ ] **Step 1: Full walkthrough for a user WITHOUT a PIN set**

```bash
source venv/bin/activate
python manage.py check
python manage.py runserver 0:8000 &
sleep 2
rm -f /tmp/cookies_nopin.txt
curl -s -c /tmp/cookies_nopin.txt http://127.0.0.1:8000/open/ -o /dev/null
TOKEN=$(grep csrftoken /tmp/cookies_nopin.txt | awk '{print $7}')
curl -s -b /tmp/cookies_nopin.txt -c /tmp/cookies_nopin.txt \
  -d "csrfmiddlewaretoken=$TOKEN&fullname=No+Pin&phone=08020000002&email=nopin@example.com&bvn=20202020202&account_type=savings" \
  -o /tmp/signup_nopin.html \
  http://127.0.0.1:8000/open/
python manage.py shell -c "
from django.contrib.auth.models import User
u = User.objects.get(username='nopin@example.com')
u.set_password('nopinpass123')
u.save()
"
TOKEN2=$(grep csrftoken /tmp/cookies_nopin.txt | awk '{print $7}')
curl -s -b /tmp/cookies_nopin.txt -c /tmp/cookies_nopin.txt \
  -d "csrfmiddlewaretoken=$TOKEN2&email=nopin@example.com&password=nopinpass123" \
  -o /dev/null -w "login: %{http_code}\n" \
  http://127.0.0.1:8000/login/
curl -s -b /tmp/cookies_nopin.txt http://127.0.0.1:8000/profile/ -o /tmp/profile_nopin.html -w "profile: %{http_code}\n"
grep -c 'Update Details\|Change Password\|Transaction PIN' /tmp/profile_nopin.html
grep -c 'Linked Devices' /tmp/profile_nopin.html
grep -o 'data-has-pin="[a-z]*"' /tmp/profile_nopin.html
kill %1
```
Expected: `profile: 200`, the three button-label grep count is `3`, the "Linked Devices" grep count is `0`, and `data-has-pin="false"`.

- [ ] **Step 2: Full walkthrough exercising all three profile forms, then confirm PIN gate turns on**

```bash
python manage.py runserver 0:8000 &
sleep 2
# Update details
TOKEN3=$(grep csrftoken /tmp/cookies_nopin.txt | awk '{print $7}')
curl -s -b /tmp/cookies_nopin.txt -c /tmp/cookies_nopin.txt \
  -d "csrfmiddlewaretoken=$TOKEN3&full_name=Updated+Name&phone=08099999999&email=nopin@example.com&bvn=30303030303" \
  -o /dev/null -w "update-details: %{http_code}\n" \
  http://127.0.0.1:8000/profile/update-details/
python manage.py shell -c "
from banking.models import Account
a = Account.objects.get(user__username='nopin@example.com')
print('full_name now:', a.full_name, '| bvn now:', a.bvn)
"
# Change password (wrong current password should fail)
TOKEN4=$(grep csrftoken /tmp/cookies_nopin.txt | awk '{print $7}')
curl -s -b /tmp/cookies_nopin.txt -c /tmp/cookies_nopin.txt \
  -d "csrfmiddlewaretoken=$TOKEN4&current_password=wrongpass&new_password=newpass456&confirm_password=newpass456" \
  -o /tmp/pw_wrong.html -w "change-password (wrong current): %{http_code}\n" \
  http://127.0.0.1:8000/profile/change-password/
grep -o 'Current password is incorrect' /tmp/pw_wrong.html
# Change password (correct current password should succeed)
TOKEN5=$(grep csrftoken /tmp/cookies_nopin.txt | awk '{print $7}')
curl -s -b /tmp/cookies_nopin.txt -c /tmp/cookies_nopin.txt \
  -d "csrfmiddlewaretoken=$TOKEN5&current_password=nopinpass123&new_password=newpass456&confirm_password=newpass456" \
  -o /dev/null -w "change-password (correct current): %{http_code}\n" \
  http://127.0.0.1:8000/profile/change-password/
python manage.py shell -c "
from django.contrib.auth.models import User
u = User.objects.get(username='nopin@example.com')
print('new password works:', u.check_password('newpass456'))
"
# Confirm the session survived the password change (no forced logout)
curl -s -b /tmp/cookies_nopin.txt http://127.0.0.1:8000/profile/ -o /dev/null -w "profile after pw change (should still be 200, not redirected to login): %{http_code}\n"
# Set a PIN
TOKEN6=$(grep csrftoken /tmp/cookies_nopin.txt | awk '{print $7}')
curl -s -b /tmp/cookies_nopin.txt -c /tmp/cookies_nopin.txt \
  -d "csrfmiddlewaretoken=$TOKEN6&pin=4321&confirm_pin=4321" \
  -o /dev/null -w "set-pin: %{http_code}\n" \
  http://127.0.0.1:8000/profile/set-pin/
# Confirm data-has-pin flipped to true
curl -s -b /tmp/cookies_nopin.txt http://127.0.0.1:8000/home/ -o /tmp/home_haspin.html
grep -o 'data-has-pin="[a-z]*"' /tmp/home_haspin.html
# Confirm the PIN modal markup and JS hook are present on a transaction page
curl -s -b /tmp/cookies_nopin.txt http://127.0.0.1:8000/transfer/ -o /tmp/transfer_pin.html -w "transfer: %{http_code}\n"
grep -c 'id="pinModal"' /tmp/transfer_pin.html
grep -c 'data-fake-transaction' /tmp/transfer_pin.html
kill %1
```
Expected: `update-details: 200` with `full_name now: Updated Name | bvn now: 30303030303`; `change-password (wrong current): 200` with the error text found; `change-password (correct current): 200` with `new password works: True`; the post-password-change profile fetch returns `200` (not a redirect to login, confirming `update_session_auth_hash` worked); `set-pin: 200`; `data-has-pin="true"`; `transfer: 200` with both the PIN modal and the fake-transaction form present (count `1` each).

- [ ] **Step 3: Clean up test data**

```bash
python manage.py shell -c "
from django.contrib.auth.models import User
User.objects.filter(username__in=['pintest@example.com', 'nopin@example.com']).delete()
"
rm -f /tmp/cookies_pin.txt /tmp/cookies_nopin.txt /tmp/signup_pin.html /tmp/signup_nopin.html /tmp/profile_nopin.html /tmp/pw_wrong.html /tmp/home_haspin.html /tmp/transfer_pin.html /tmp/home_check.html
```

- [ ] **Step 4: No commit for this task** — it's verification-only, nothing changed.
