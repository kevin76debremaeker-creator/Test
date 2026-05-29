// Hotel Zeezicht — interactie

// Jaar in footer
document.getElementById('year').textContent = new Date().getFullYear();

// Header krijgt achtergrond bij scrollen
const header = document.getElementById('header');
const onScroll = () => header.classList.toggle('scrolled', window.scrollY > 40);
onScroll();
window.addEventListener('scroll', onScroll, { passive: true });

// Mobiel menu
const navToggle = document.getElementById('navToggle');
const nav = document.getElementById('nav');
navToggle.addEventListener('click', () => {
  const open = nav.classList.toggle('open');
  navToggle.setAttribute('aria-expanded', String(open));
});
// Sluit menu na klik op een link
nav.querySelectorAll('a').forEach((link) =>
  link.addEventListener('click', () => {
    nav.classList.remove('open');
    navToggle.setAttribute('aria-expanded', 'false');
  })
);

// Scroll-reveal: voeg .reveal toe aan secties en toon ze in beeld
const revealEls = document.querySelectorAll('.section, .room-card, .feature, .env-card');
revealEls.forEach((el) => el.classList.add('reveal'));

if ('IntersectionObserver' in window) {
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          io.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 }
  );
  revealEls.forEach((el) => io.observe(el));
} else {
  revealEls.forEach((el) => el.classList.add('visible'));
}

// Reserveringsformulier
const form = document.getElementById('reserveForm');
const msg = document.getElementById('formMsg');

form.addEventListener('submit', (e) => {
  e.preventDefault();
  msg.className = 'form-msg';

  const data = new FormData(form);
  const aankomst = data.get('aankomst');
  const vertrek = data.get('vertrek');

  if (!form.checkValidity()) {
    msg.textContent = 'Vul alstublieft alle verplichte velden in.';
    msg.classList.add('err');
    form.reportValidity();
    return;
  }

  if (aankomst && vertrek && new Date(vertrek) <= new Date(aankomst)) {
    msg.textContent = 'De vertrekdatum moet na de aankomstdatum liggen.';
    msg.classList.add('err');
    return;
  }

  // Demo: geen backend — toon een bevestiging
  const naam = data.get('naam');
  msg.textContent = `Bedankt, ${naam}! Uw aanvraag is ontvangen. We bevestigen binnen 24 uur per e-mail.`;
  msg.classList.add('ok');
  form.reset();
});
