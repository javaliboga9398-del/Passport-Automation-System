/**
 * Multi-Step Form Wizard Handler
 */
document.addEventListener('DOMContentLoaded', () => {
  // Toggle previous passport number field based on service type
  const serviceTypeSelect = document.getElementById('service_type');
  const prevPassportGroup = document.getElementById('prev_passport_group');

  function updatePassportFields() {
    if (serviceTypeSelect && prevPassportGroup) {
      if (serviceTypeSelect.value === 'Renewal') {
        prevPassportGroup.style.display = 'block';
        const input = prevPassportGroup.querySelector('input');
        if (input) input.required = true;
      } else {
        prevPassportGroup.style.display = 'none';
        const input = prevPassportGroup.querySelector('input');
        if (input) input.required = false;
      }
    }
  }

  if (serviceTypeSelect) {
    serviceTypeSelect.addEventListener('change', updatePassportFields);
    updatePassportFields();
  }

  // Client-side quick validation for step 5 declaration checkbox
  const submitBtn = document.getElementById('submit_application_btn');
  const declarationCheck = document.getElementById('declaration_accepted');

  if (submitBtn && declarationCheck) {
    declarationCheck.addEventListener('change', () => {
      submitBtn.disabled = !declarationCheck.checked;
    });
  }
});
