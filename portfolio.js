/* Portfolio interactions — calm micro-motion, CAD accordion, image modal */

(function () {
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── Scroll reveal ── */
  if (!prefersReduced) {
    const revealEls = document.querySelectorAll(
      '.section-inner, .hero-inner, .cad-panel, .project-item, .about-grid'
    );
    revealEls.forEach((el) => el.classList.add('reveal'));

    const revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            revealObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.08, rootMargin: '0px 0px -6% 0px' }
    );
    revealEls.forEach((el) => revealObserver.observe(el));
  } else {
    document.querySelectorAll('.reveal').forEach((el) => el.classList.add('is-visible'));
  }

  /* ── CAD accordion ── */
  const cadPanels = document.querySelectorAll('.cad-panel');
  cadPanels.forEach((panel, index) => {
    const trigger = panel.querySelector('.cad-panel-trigger');
    const body = panel.querySelector('.cad-panel-body');
    if (!trigger || !body) return;

    const panelId = panel.dataset.cad || `cad-${index}`;
    trigger.setAttribute('aria-controls', `${panelId}-body`);
    trigger.setAttribute('id', `${panelId}-trigger`);
    body.id = `${panelId}-body`;

    const open = () => {
      const isOpen = panel.classList.contains('is-open');
      cadPanels.forEach((p) => {
        p.classList.remove('is-open');
        const t = p.querySelector('.cad-panel-trigger');
        const b = p.querySelector('.cad-panel-body');
        if (t) t.setAttribute('aria-expanded', 'false');
        if (b) b.hidden = true;
      });
      if (!isOpen) {
        panel.classList.add('is-open');
        trigger.setAttribute('aria-expanded', 'true');
        body.hidden = false;
        if (!prefersReduced) {
          panel.classList.remove('is-opening');
          void panel.offsetWidth;
          panel.classList.add('is-opening');
          setTimeout(() => panel.classList.remove('is-opening'), 720);
        }
        panel.scrollIntoView({ behavior: prefersReduced ? 'auto' : 'smooth', block: 'nearest' });
      } else {
        panel.classList.remove('is-opening');
      }
    };

    trigger.addEventListener('click', open);
    trigger.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        open();
      }
    });

    if (index === 0) {
      panel.classList.add('is-open', 'is-opening');
      trigger.setAttribute('aria-expanded', 'true');
      body.hidden = false;
      if (!prefersReduced) {
        setTimeout(() => panel.classList.remove('is-opening'), 700);
      }
    }
  });

  /* ── Image lightbox modal ── */
  const modal = document.getElementById('gallery-modal');
  const modalImg = document.getElementById('gallery-modal-img');
  const modalCaption = document.getElementById('gallery-modal-caption');
  const modalClose = document.querySelector('.gallery-modal-close');

  if (modal && modalImg) {
    const openModal = (img) => {
      modalImg.src = img.currentSrc || img.src;
      modalImg.alt = img.alt || '';
      if (modalCaption) {
        modalCaption.textContent = img.dataset.caption || img.alt || '';
      }
      modal.classList.add('is-open');
      modal.setAttribute('aria-hidden', 'false');
      document.body.classList.add('modal-open');
      modalClose?.focus();
    };

    const closeModal = () => {
      modal.classList.remove('is-open');
      modal.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('modal-open');
      modalImg.src = '';
    };

    document.querySelectorAll('.cad-images--editorial img, .cad-figure img, .project-visual img').forEach((img) => {
      img.classList.add('zoomable');
      img.tabIndex = 0;
      img.setAttribute('role', 'button');
      img.setAttribute('aria-label', `View larger: ${img.alt || 'image'}`);
      const handler = () => openModal(img);
      img.addEventListener('click', handler);
      img.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') handler();
      });
    });

    modalClose?.addEventListener('click', closeModal);
    modal.querySelector('.gallery-modal-backdrop')?.addEventListener('click', closeModal);
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modal.classList.contains('is-open')) closeModal();
    });
  }

  /* ── Nav scroll state ── */
  const nav = document.getElementById('site-nav');
  if (nav) {
    const onScroll = () => nav.classList.toggle('is-scrolled', window.scrollY > 24);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ── Cursor-follow hint on hero (subtle) ── */
  const hero = document.querySelector('.hero');
  const heroGlow = document.querySelector('.hero-glow');
  if (hero && heroGlow && !prefersReduced && window.matchMedia('(pointer: fine)').matches) {
    hero.addEventListener('mousemove', (e) => {
      const rect = hero.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      heroGlow.style.setProperty('--mx', `${x}%`);
      heroGlow.style.setProperty('--my', `${y}%`);
    });
  }
})();