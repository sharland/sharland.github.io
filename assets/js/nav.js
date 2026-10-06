/* Section menu: marks the section currently in view with aria-current on every
   menu link that points at it (the sidebar and the sticky bar share this). Falls
   back to plain anchor links when IntersectionObserver is missing. */
(function () {
  'use strict';
  var links = Array.prototype.slice.call(document.querySelectorAll('a[data-section]'));
  if (!links.length || !('IntersectionObserver' in window)) { return; }

  var ids = [];
  links.forEach(function (a) {
    var id = a.getAttribute('data-section');
    if (ids.indexOf(id) < 0) { ids.push(id); }
  });
  var sections = ids.map(function (id) { return document.getElementById(id); }).filter(Boolean);
  if (!sections.length) { return; }  /* not the front page */

  function setCurrent(id) {
    links.forEach(function (a) {
      if (a.getAttribute('data-section') === id) { a.setAttribute('aria-current', 'true'); }
      else { a.removeAttribute('aria-current'); }
    });
  }

  /* The last section may be too short ever to reach the band; at the foot of
     the page it is the current one regardless. */
  function atEnd() {
    return window.innerHeight + window.pageYOffset >= document.documentElement.scrollHeight - 2;
  }
  function update() {
    if (atEnd()) { setCurrent(sections[sections.length - 1].id); return; }
    for (var i = 0; i < sections.length; i++) {
      if (inBand[sections[i].id]) { setCurrent(sections[i].id); return; }
    }
  }

  var inBand = {};
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { inBand[e.target.id] = e.isIntersecting; });
    update();
  }, { rootMargin: '-20% 0px -65% 0px', threshold: 0 });
  sections.forEach(function (s) { observer.observe(s); });
  window.addEventListener('scroll', update, { passive: true });

  if (location.hash && ids.indexOf(location.hash.slice(1)) >= 0) {
    setCurrent(location.hash.slice(1));
  }
})();
