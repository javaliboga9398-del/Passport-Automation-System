/**
 * Passport Automation System - Global JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Auto-dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transition = 'opacity 0.5s ease';
      setTimeout(() => alert.remove(), 500);
    }, 5000);
  });

  // 2. Demo credential auto-fill helper (on Login page)
  const demoButtons = document.querySelectorAll('[data-demo-email]');
  demoButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const emailInput = document.getElementById('email');
      const passwordInput = document.getElementById('password');
      if (emailInput && passwordInput) {
        emailInput.value = btn.getAttribute('data-demo-email');
        passwordInput.value = btn.getAttribute('data-demo-password');
        // Flash subtle highlight
        emailInput.style.backgroundColor = '#ecfdf5';
        passwordInput.style.backgroundColor = '#ecfdf5';
        setTimeout(() => {
          emailInput.style.backgroundColor = '';
          passwordInput.style.backgroundColor = '';
        }, 600);
      }
    });
  });

  // 3. Modal helper functions
  window.openModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('active');
    }
  };

  window.closeModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('active');
    }
  };

  // Close modals when clicking overlay backdrop
  const modalOverlays = document.querySelectorAll('.modal-overlay');
  modalOverlays.forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        overlay.classList.remove('active');
      }
    });
  });

  // 4. Print trigger helper
  const printTriggers = document.querySelectorAll('[data-action="print"]');
  printTriggers.forEach(btn => {
    btn.addEventListener('click', () => window.print());
  });
});
