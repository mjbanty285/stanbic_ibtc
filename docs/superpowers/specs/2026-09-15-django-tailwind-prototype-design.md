# Stanbic IBTC Prototype: Tailwind + JS + Django Conversion

## Context

The project is currently 18 static HTML files, each with its own inline `<style>` block, no shared layout, no JS interactivity, and no backend. The README asks for:
- A consistent, mobile-focused UI using Tailwind (Play CDN).
- JS interactivity.
- A Django + SQLite backend with real authentication, converting the static HTML into Django templates using `extends`/`include` for shared layout.
- All "money-moving" actions (transfer, airtime, bulk transfer, electricity/TV) must fake processing: show a loading state for 10 seconds, then show "completed" — no real transaction logic.

The README explicitly says this is a prototype: avoid writing tests, avoid complex logic.

This is a combined build (not phased): Tailwind, JS, and Django all land together, with existing static HTML rewritten directly into Django templates rather than restyled first and converted later.

## Goals

- All 18 existing pages become Django templates sharing one consistent Tailwind-based design system, built mobile-first (no phone-frame chrome — the layout fills the real viewport).
- Real signup + login backed by SQLite via Django's built-in `User` model.
- Per-user account data (balance, account number, profile fields) persisted in the DB.
- Beneficiary lists and transaction history remain static/hardcoded — no DB writes for those.
- Fake transaction flow (10s "processing" → "completed") is purely client-side JS with no server round-trip.
- Single Django app, function-based views, no unnecessary abstraction.

## Non-Goals

- No real money movement, no real balance mutation from transactions.
- No automated tests (explicitly excluded by README).
- No Beneficiary/Transaction database models.
- No deployment concerns — this runs via `manage.py runserver` for local demo purposes only.
- No custom auth backend complexity beyond using email as the `username` value.

## Architecture

### Project structure

One Django project (e.g. `stanbic_ibtc`) containing one app: `banking`.

```
stanbic_ibtc/
  manage.py
  stanbic_ibtc/          # project settings, root urls.py
  banking/               # the one app
    models.py
    views.py
    urls.py
    templates/banking/
      base.html
      _header.html
      _bottomnav.html
      _sidemenu.html
      bankings.html      # public landing (was bankings.html)
      login.html
      open.html          # signup
      index.html         # dashboard home
      transfer.html
      beneficiary.html
      airtime.html
      electricity.html
      loan.html
      account.html
      profile.html
      viewprofile.html
      view.html
      bulk.html
      payments.html
      approvals.html
      transaction.html
      logout.html        # not really a template — logout is a view that redirects
    static/banking/
      js/app.js
  db.sqlite3
```

### Data model

Uses Django's built-in `django.contrib.auth.models.User` for authentication, extended with one additional model:

```python
class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    bvn = models.CharField(max_length=11)
    account_type = models.CharField(max_length=10, choices=[("savings", "Savings"), ("current", "Current")])
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("1000000000.00"))
```

No `Beneficiary` or `Transaction` model. Beneficiary lists (used on `beneficiary.html`, `bulk.html`) and transaction history (`transaction.html`, `view.html`) are hardcoded lists of dicts defined directly in the relevant views or templates — same static demo data for every user.

### Auth flow

- **Signup (`open.html` → `POST /open/`):** Form collects full name, phone, email, BVN, account type (existing fields, unchanged). On submit:
  1. Generate a random account number and a random password.
  2. Create a `User` with `username=email`, `email=email`, the generated password (hashed via `set_password`).
  3. Create the linked `Account` with `balance=1_000_000_000.00`.
  4. Show a success screen displaying the generated account number and password (told to the user once — this is a prototype, so no email delivery).
- **Login (`login.html` → `POST /login/`):** Form field labeled "Email" (not "Username"), calls `django.contrib.auth.authenticate(username=email, password=...)` — works because `username` was set to the email at signup, so no custom backend is needed.
- **Logout:** `GET /logout/` calls `django.contrib.auth.logout` and redirects to the landing page, rendering `logout.html` as a brief "you've been logged out" confirmation before/after.
- **Protection:** Every view except landing, login, and signup is decorated with `@login_required` (`LOGIN_URL` pointed at the login view).

### Templates & shared layout

`base.html` defines the HTML shell: `<head>` with the Tailwind Play CDN script tag and a link to `static/banking/js/app.js`, and a `{% block content %}`. Three partials (`_header.html`, `_bottomnav.html`, `_sidemenu.html`) are `{% include %}`-ed from `base.html` (or from a `dashboard_base.html` that extends `base.html`, used only by logged-in pages — landing/login/signup extend `base.html` directly without nav chrome). Every existing page becomes a template that extends the appropriate base and fills in `{% block content %}` with its Tailwind-classed markup, replacing the inline `<style>` blocks entirely.

### Styling

- Single brand color `#0033a0` (Tailwind arbitrary value `bg-[#0033a0]` or a small `tailwind.config` color extension via the CDN's inline config script) used everywhere instead of the current two-blue inconsistency.
- Text wordmark logo ("Stanbic **IBTC**", IBTC in a lighter accent) — no image asset.
- Mobile-first: layout fills the real viewport (`min-h-screen`, `max-w-md mx-auto` centering on wider screens so it doesn't look broken on desktop, but no fixed phone-frame/status-bar chrome).

### JS interactivity (`static/banking/js/app.js`)

One shared script loaded on every page, providing:
- Side-menu open/close (replaces `toggleMenu()`).
- Balance show/hide eye-icon toggle.
- Tab/segment switches (account type selector, airtime vs data, electricity vs TV) — generalized versions of the existing `switchTab`/`selectNetwork`/`setAmount` inline handlers.
- Client-side form validation: required fields, and amount-≤-balance checks on money-moving forms.
- Copy-account-number-to-clipboard button.
- The fake transaction flow (below).

### Fake transaction flow

On every money-moving form (transfer, beneficiary transfer, bulk transfer, airtime, electricity/TV):
1. JS intercepts `submit`, calls `preventDefault()`.
2. Shows a full-screen overlay with a spinner and "Processing…" text.
3. After exactly 10 seconds (`setTimeout`), swaps the overlay content to a checkmark and "Completed" message.
4. No `fetch`/form POST is made for the transaction itself; nothing is persisted. A "Done" button dismisses the overlay back to the dashboard.

### URLs

| Path | View | Auth |
|---|---|---|
| `/` | landing (`bankings.html`) | public |
| `/login/` | login | public |
| `/open/` | signup | public |
| `/logout/` | logout | required |
| `/home/` | index/dashboard | required |
| `/transfer/`, `/beneficiary/`, `/airtime/`, `/electricity/`, `/loan/`, `/account/`, `/profile/`, `/profile/view/`, `/view/`, `/bulk/`, `/payments/`, `/approvals/`, `/transaction/` | one view each, mostly rendering static/demo content plus real `Account`/`User` data where relevant (balance, account number, profile fields) | required |

## Risks / Open Considerations

- Showing a plaintext generated password once on the signup success screen is a prototype-only shortcut (no real password-reset/email flow) — acceptable per README's "avoid complex logic" instruction, not something to harden.
- Tailwind Play CDN is not meant for production but matches the README's explicit instruction to use it.
