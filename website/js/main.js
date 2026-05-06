// Gullicksen & Co Realty — Main JS

// Contact form handler
function handleSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const status = document.getElementById('form-status');
  const btn = form.querySelector('button[type="submit"]');
  
  btn.disabled = true;
  btn.textContent = 'Sending...';
  
  // Collect form data
  const data = {
    name: form.name.value,
    email: form.email.value,
    phone: form.phone.value,
    interest: form.interest.value,
    message: form.message.value
  };
  
  // Web3Forms — sends directly from the website
  const payload = {
    access_key: '3bcf8ab9-c9c7-44d3-a05a-9a5ad7bfd1f1',
    name: data.name,
    email: data.email,
    phone: data.phone,
    subject: 'Website Inquiry from ' + data.name,
    interest: data.interest,
    message: data.message,
    from_name: 'Gullicksen Realty Website'
  };

  fetch('https://api.web3forms.com/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      status.innerHTML = '✅ Message sent! We\'ll reach out within 24 hours.<br>Need us now? Call <a href="tel:+17708252626">(770) 825-2626</a> or email <a href="mailto:mike@gullicksenrealty.com">mike@gullicksenrealty.com</a>.';
      status.style.color = '#27ae60';
      form.reset();
    } else {
      status.textContent = '❌ Something went wrong. Please try again or call us directly.';
      status.style.color = '#e74c3c';
    }
    btn.disabled = false;
    btn.textContent = 'Send Message';
  })
  .catch(() => {
    status.textContent = '❌ Network error. Please try again or call (770) 825-2626.';
    status.style.color = '#e74c3c';
    btn.disabled = false;
    btn.textContent = 'Send Message';
  });
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function(e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) target.scrollIntoView({ behavior: 'smooth' });
  });
});

// Navbar scroll effect
window.addEventListener('scroll', () => {
  const navbar = document.querySelector('.navbar');
  if (window.scrollY > 50) {
    navbar.style.boxShadow = '0 4px 20px rgba(0,0,0,0.4)';
  } else {
    navbar.style.boxShadow = '0 2px 10px rgba(0,0,0,0.3)';
  }
});
