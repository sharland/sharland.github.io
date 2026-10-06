/* Two small controls.
   The disc switcher: the disc itself, and Previous/Next under it, step through
   the pieces. The choice is kept for this browser session and written into the
   address as ?disc=<name> so it can be shared; the daily rotation returns on the
   next visit.
   The theme switch: Light/Dark, kept in localStorage; with nothing stored the
   system setting applies. Both controls are hidden until this script runs, so
   without JavaScript nothing inert is shown. */
(function () {
  'use strict';
  var root = document.documentElement;

  /* ---- disc switcher ---- */
  var pieces = window.DISC_PIECES || [];
  var canvas = document.getElementById('disc');
  var nameEl = document.getElementById('disc-name');
  var controls = document.querySelector('.disc-controls');

  function currentPiece() { return root.getAttribute('data-disc'); }
  function syncDisc() {
    var n = currentPiece();
    if (nameEl) { nameEl.textContent = n; }
    if (canvas) { canvas.setAttribute('aria-label', 'Generative drawing, piece ' + n + '. Activate to show the next piece.'); }
  }
  function setPiece(name) {
    root.setAttribute('data-disc', name);
    try { sessionStorage.setItem('disc', name); } catch (e) {}
    try {
      var u = new URL(location.href); u.searchParams.set('disc', name);
      history.replaceState(null, '', u.pathname + u.search + u.hash);
    } catch (e) {}
    syncDisc();
  }
  function step(d) {
    var i = pieces.indexOf(currentPiece()); if (i < 0) { i = 0; }
    setPiece(pieces[(i + d + pieces.length) % pieces.length]);
  }
  if (canvas && pieces.length > 1) {
    canvas.setAttribute('role', 'button');
    canvas.tabIndex = 0;
    canvas.classList.add('is-button');
    canvas.addEventListener('click', function () { step(1); });
    canvas.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); step(1); }
    });
    if (controls) {
      controls.hidden = false;
      document.getElementById('disc-prev').addEventListener('click', function () { step(-1); });
      document.getElementById('disc-next').addEventListener('click', function () { step(1); });
    }
    syncDisc();
  }

  /* ---- theme switch ---- */
  var systemDark = window.matchMedia('(prefers-color-scheme: dark)');
  var toggles = Array.prototype.slice.call(document.querySelectorAll('[data-theme-toggle]'));
  var metas = Array.prototype.slice.call(document.querySelectorAll('meta[name="theme-color"]'));
  function isDark() {
    var t = root.getAttribute('data-theme');
    return t ? t === 'dark' : systemDark.matches;
  }
  function syncTheme() {
    var dark = isDark();
    toggles.forEach(function (b) {
      b.hidden = false;
      b.textContent = dark ? 'Light' : 'Dark';
      b.setAttribute('aria-label', dark ? 'Switch to the light theme' : 'Switch to the dark theme');
    });
    metas.forEach(function (m) { m.removeAttribute('media'); m.setAttribute('content', dark ? '#0b0c0f' : '#f4efe6'); });
  }
  toggles.forEach(function (b) {
    b.addEventListener('click', function () {
      var next = isDark() ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('theme', next); } catch (e) {}
      syncTheme();
    });
  });
  if (systemDark.addEventListener) { systemDark.addEventListener('change', syncTheme); }
  syncTheme();
})();
