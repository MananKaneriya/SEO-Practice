/* Ortheon AI – small progressive enhancements. Vanilla JS, no dependencies.
   Every page works without this file; it only adds the clock, the mobile menu,
   the FAQ accordion and the scroll fade-up. */
(function () {
  'use strict';

  var doc = document;
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---- 1. Live Ahmedabad (IST) clock ---- */
  var clocks = doc.querySelectorAll('[data-clock]');
  if (clocks.length && window.Intl && Intl.DateTimeFormat) {
    var fmt = new Intl.DateTimeFormat('en-GB', {
      timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23'
    });
    var tick = function () {
      var t = fmt.format(new Date());
      for (var i = 0; i < clocks.length; i++) clocks[i].textContent = t;
    };
    tick();
    setInterval(tick, 1000);
  }

  /* ---- 2. Footer year ---- */
  var years = doc.querySelectorAll('[data-year]');
  for (var y = 0; y < years.length; y++) years[y].textContent = String(new Date().getFullYear());

  /* ---- 3. Mobile menu ---- */
  var header = doc.querySelector('.site-header');
  var toggle = doc.querySelector('.nav-toggle');
  var menu = doc.getElementById('site-menu');
  if (header && toggle && menu) {
    header.classList.add('is-ready');
    var setMenu = function (open) {
      menu.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    };
    toggle.addEventListener('click', function () {
      setMenu(toggle.getAttribute('aria-expanded') !== 'true');
    });
    menu.addEventListener('click', function (e) {
      if (e.target.closest && e.target.closest('a')) setMenu(false);
    });
    doc.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        setMenu(false);
        toggle.focus();
      }
    });
    window.addEventListener('resize', function () {
      if (window.innerWidth >= 900) setMenu(false);
    });
  }

  /* ---- 4. FAQ accordion: turns each <dt> into a button, each <dd> into a collapsible panel ---- */
  var faqs = doc.querySelectorAll('dl.faq');
  for (var f = 0; f < faqs.length; f++) {
    var dl = faqs[f];
    var terms = dl.querySelectorAll(':scope > dt');
    for (var n = 0; n < terms.length; n++) {
      var dt = terms[n];
      var dd = dt.nextElementSibling;
      if (!dd || dd.tagName !== 'DD') continue;

      var id = 'faq-' + f + '-' + n;
      var btn = doc.createElement('button');
      btn.type = 'button';
      btn.className = 'faq__q';
      btn.id = id + '-q';
      btn.setAttribute('aria-expanded', 'false');
      btn.setAttribute('aria-controls', id + '-a');
      var label = doc.createElement('span');
      while (dt.firstChild) label.appendChild(dt.firstChild);
      var icon = doc.createElement('span');
      icon.className = 'faq__icon';
      icon.setAttribute('aria-hidden', 'true');
      btn.appendChild(label);
      btn.appendChild(icon);
      dt.appendChild(btn);

      var inner = doc.createElement('div');
      inner.className = 'faq__a-in';
      var pad = doc.createElement('div');
      pad.className = 'faq__a-pad';
      while (dd.firstChild) pad.appendChild(dd.firstChild);
      inner.appendChild(pad);
      dd.appendChild(inner);
      dd.id = id + '-a';
      dd.setAttribute('role', 'region');
      dd.setAttribute('aria-labelledby', id + '-q');

      btn.addEventListener('click', (function (b, d) {
        return function () {
          var open = b.getAttribute('aria-expanded') !== 'true';
          b.setAttribute('aria-expanded', open ? 'true' : 'false');
          d.classList.toggle('is-open', open);
        };
      })(btn, dd));
    }
    dl.classList.add('faq--ready');
  }

  /* ---- 5. Fade-up on scroll (only for elements that start below the fold) ---- */
  if (!reduceMotion && 'IntersectionObserver' in window) {
    var targets = doc.querySelectorAll(
      '.section > :not(.features):not(.steps):not(.areas):not(.tags), ' +
      '.features > li, .steps > li, .areas > li, .tags > li'
    );
    var io = new IntersectionObserver(function (entries) {
      for (var i = 0; i < entries.length; i++) {
        if (entries[i].isIntersecting) {
          entries[i].target.classList.add('is-in');
          io.unobserve(entries[i].target);
        }
      }
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });

    // once the fade has finished, drop the helper classes so hover transitions work normally again
    var finish = function (e) {
      if (e.target !== this || e.propertyName !== 'opacity') return;
      this.classList.remove('reveal', 'is-in');
      this.style.removeProperty('--d');
      this.removeEventListener('transitionend', finish);
    };

    var vh = window.innerHeight || doc.documentElement.clientHeight;
    var lastParent = null;
    var idx = 0;
    for (var t = 0; t < targets.length; t++) {
      var el = targets[t];
      if (el.getBoundingClientRect().top < vh) continue;        // already on screen: no flash
      if (el.parentNode !== lastParent) { lastParent = el.parentNode; idx = 0; }
      el.style.setProperty('--d', (idx++ % 6) * 70 + 'ms');     // small stagger inside a group
      el.classList.add('reveal');
      el.addEventListener('transitionend', finish);
      io.observe(el);
    }
  }
})();
