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

document.addEventListener('DOMContentLoaded', function () {
  initBalanceToggles();
  initCopyButtons();
  initFakeTransactionForms();
});
