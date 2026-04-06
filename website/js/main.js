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
  
  // For now, open email client (replace with Formspree/Netlify Forms when deployed)
  const subject = encodeURIComponent('Website Inquiry from ' + data.name);
  const body = encodeURIComponent(
    `Name: ${data.name}\nEmail: ${data.email}\nPhone: ${data.phone}\nInterest: ${data.interest}\n\nMessage:\n${data.message}`
  );
  window.location.href = `mailto:mike@gullicksenrealty.com?subject=${subject}&body=${body}`;
  
  status.textContent = 'Opening your email client...';
  status.style.color = '#27ae60';
  btn.disabled = false;
  btn.textContent = 'Send Message';
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
