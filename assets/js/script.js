
const revealSelector = '.cc-reveal';

function initReveal() {
  const revealElements = document.querySelectorAll(revealSelector);
  if (!revealElements.length) {
    return;
  }

  if (!('IntersectionObserver' in window)) {
    revealElements.forEach((element) => element.classList.add('is-visible'));
    return;
  }

  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) {
        return;
      }

      entry.target.classList.add('is-visible');
      observer.unobserve(entry.target);
    });
  }, {
    rootMargin: '0px 0px -8% 0px',
    threshold: 0.12,
  });

  revealElements.forEach((element, index) => {
    element.style.transitionDelay = `${Math.min(index * 40, 240)}ms`;
    revealObserver.observe(element);
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initReveal);
} else {
  initReveal();
}
