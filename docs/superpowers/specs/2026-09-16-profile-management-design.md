# Profile Management: Editable Details, Password, Transaction PIN

## Context

`banking/templates/banking/profile.html` currently has four static buttons — "View Profile" (already links to `view_profile`), "Update Contact Details", "Change Password", "Transaction PIN", "Linked Devices" — none of the latter three do anything. This adds real functionality to three of them, drops "Linked Devices," and introduces a transaction PIN that gates every existing fake-transaction form (transfer, beneficiary, bulk, airtime, electricity/TV) behind a PIN-entry modal once a PIN has been set.

## Goals

- Users can update their full name, phone, email, and BVN from the Profile Management page.
- Users can change their password, given their current password.
- Users can set/change a 4-digit transaction PIN with no guard (no current-PIN required).
- Once a PIN is set, every fake-transaction form on the site requires entering it (via a modal) before the existing 10-second processing/completed flow runs. Accounts with no PIN set see no change in behavior.
- "Linked Devices" is removed from the page.

## Non-Goals

- No email verification/confirmation link for any of these changes (explicit user instruction: no email, no guard, straight change — except password, which requires the current password per user correction).
- No PIN attempt limiting/lockout — wrong PIN just shows an inline error and lets the user retry.
- No change to `account_number`, `account_type`, or `balance` — not user-editable.
- No new pages/URLs beyond the four POST-only endpoints below — everything renders on the existing `/profile/` page.

## Data model

One new field on `Account` (`banking/models.py`):

```python
transaction_pin = models.CharField(max_length=128, blank=True, default="")
```

Stores a hash produced by `django.contrib.auth.hashers.make_password` (same hasher already used for `User.password` — no new hashing logic introduced). An empty string means "no PIN set." Requires a migration.

## Profile page (`/profile/`)

Stays a single view/template. `profile.html`'s three buttons (`Update Details`, `Change Password`, `Transaction PIN`) each become a toggle button (`onclick`, same `classList.toggle('hidden')` pattern `account.html` already uses for its account-switch dropdown) that reveals an inline `<form>` directly beneath it. "Linked Devices" is deleted from the template entirely.

`dashboard_base.html` gets a small messages banner (Django's `django.contrib.messages`) added once, near the top of `{% block content %}`'s wrapper, so any page can surface a success/error notice — first consumer is this page, redirected back to after each POST.

### `POST /profile/update-details/`
Fields: `full_name`, `phone`, `bvn` (written to `Account`), `email` (written to `User`). No current-password/PIN check. On success: updates the row, adds a success message, redirects to `profile`. On validation failure (e.g. blank required field): error message, redirect to `profile`, form values are not preserved (prototype-level simplicity — user just re-fills).

### `POST /profile/change-password/`
Fields: `current_password`, `new_password`, `confirm_password`. Validates `current_password` via `request.user.check_password(...)` — if wrong, error message, no change. Validates `new_password == confirm_password` — if not, error message, no change. On success: `user.set_password(new_password)`, `user.save()`, then `update_session_auth_hash(request, user)` (so the current session survives the password hash change — otherwise Django would log them out immediately after changing it), success message, redirect to `profile`.

### `POST /profile/set-pin/`
Fields: `pin`, `confirm_pin`. Validates both are exactly 4 digits (`str.isdigit() and len == 4`) and `pin == confirm_pin`. No current-PIN check (works identically whether this is the first PIN or a change). On success: `account.transaction_pin = make_password(pin)`, save, success message, redirect to `profile`. This is the only one of the three that doesn't touch `User` — it's purely on `Account`.

All three views are `@login_required`, `@require_POST`, and operate on `request.user`/`request.user.account` only — no ID is ever taken from the request, so there's no way to edit another account.

## Transaction PIN gate

### New shared pieces
- `banking/templates/banking/_pin_modal.html` — a modal (same visual language as `_processing_overlay.html`: fixed inset overlay, centered white card) with a 4-digit numeric input, a submit button, and an inline error message area (hidden by default). Included once from `dashboard_base.html`, alongside the existing processing overlay include.
- `dashboard_base.html`'s outer wrapper div gets `data-has-pin="{{ request.user.account.transaction_pin|yesno:'true,false' }}"`.
- `POST /profile/verify-pin/` — `@login_required`, `@require_POST`, takes `pin` from the POST body, returns JSON `{"valid": true}` or `{"valid": false}` via `check_password(pin, request.user.account.transaction_pin)`. If no PIN is set on the account, returns `{"valid": false}` (this endpoint is never called by the JS in that case anyway, but it fails closed rather than open if hit directly).

### `app.js` change
Inside `initFakeTransactionForms()`, the existing submit handler currently validates the form and amount, then immediately shows the processing overlay. That "show processing overlay" step becomes a function `proceedToProcessing()`. Before calling it, the handler now checks `document.querySelector('[data-has-pin]').dataset.hasPin`:
- `"false"` → call `proceedToProcessing()` directly (today's behavior, unchanged).
- `"true"` → show `#pinModal` instead. On the modal's own submit: `fetch('/profile/verify-pin/', {method: 'POST', body: new FormData with pin + csrf token})`. If `valid: true`: hide the modal, call `proceedToProcessing()`. If `valid: false`: show the modal's inline error text, clear the input, let the user retry (no limit).

This is a single, generic gate — it applies uniformly to every current and future `data-fake-transaction` form (transfer, beneficiary, bulk, airtime, both electricity/TV forms) with no per-page changes needed to those five templates.

## Risks / Open Considerations

- `transaction_pin` is hashed, not stored as an unrecoverable-but-still-4-digit-space secret — 4 numeric digits is inherently low-entropy (10,000 possibilities) even hashed, same as any real bank PIN. Hashing here matches the password precedent and is effectively free to add, but isn't meant to imply this is cryptographically strong; that's consistent with how real transaction PINs work too (short, paired with rate-limiting in real banks — which this prototype explicitly excludes per Non-Goals).
- `update_session_auth_hash` is required after `set_password` in the same request or the user gets logged out mid-flow; this is called out explicitly above so it isn't missed during implementation.
