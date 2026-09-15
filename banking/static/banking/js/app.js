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
