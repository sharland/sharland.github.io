/* The disc.
   A filled circle in the piece's own ground colour, with one of four line
   systems drawn inside it and clipped to the circle. The piece (colours and
   kind) comes from CSS custom properties chosen in <head> by data-disc; the
   geometry comes from a seed derived from today's date, so each piece changes
   once a day and is otherwise stable. No libraries. */
(function () {
  'use strict';
  var canvas = document.getElementById('disc');
  if (!canvas || !canvas.getContext) { return; }
  var ctx = canvas.getContext('2d');
  var root = document.documentElement;
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var TAU = Math.PI * 2;
  var frame = 0;

  function mulberry32(a) {
    return function () {
      a |= 0; a = a + 0x6D2B79F5 | 0;
      var t = Math.imul(a ^ a >>> 15, 1 | a);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  function todaySeed() {
    var d = new Date();
    return d.getFullYear() * 10000 + (d.getMonth() + 1) * 100 + d.getDate();
  }
  function cssVar(name) { return getComputedStyle(root).getPropertyValue(name).trim(); }
  function rgb(hex) {
    var h = hex.replace('#', '');
    if (h.length === 3) { h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2]; }
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }
  function mix(a, b, t) {
    return 'rgb(' + Math.round(a[0] + (b[0] - a[0]) * t) + ',' + Math.round(a[1] + (b[1] - a[1]) * t) + ',' + Math.round(a[2] + (b[2] - a[2]) * t) + ')';
  }

  /* A closed curve inside the unit disc: two sinusoids per axis. */
  function curve(rng) {
    var ax = 0.25 + rng() * 0.7, ay = 0.25 + rng() * 0.7;
    var fx = 1 + Math.floor(rng() * 3), fy = 1 + Math.floor(rng() * 3);
    var px = rng() * TAU, py = rng() * TAU;
    var gx = rng() * 0.35, gy = rng() * 0.35;
    var hx = 2 + Math.floor(rng() * 4), hy = 2 + Math.floor(rng() * 4);
    return function (t) {
      var u = t * TAU;
      return [ax * Math.sin(fx * u + px) + gx * Math.sin(hx * u), ay * Math.cos(fy * u + py) + gy * Math.cos(hy * u)];
    };
  }

  /* Each builder returns a list of strokes in unit-disc coordinates:
     ['l', x1, y1, x2, y2, colour, alpha, width] or ['c', cx, cy, r, colour, alpha, width]. */
  var build = {
    ribbons: function (rng, c) {
      var out = [], pairs = 2 + Math.floor(rng() * 2), n = 1400;
      for (var k = 0; k < pairs; k++) {
        var A = curve(rng), B = curve(rng);
        var c1 = c[k % c.length], c2 = c[(k + 1) % c.length];
        var alpha = 0.05 + rng() * 0.04;
        for (var i = 0; i < n; i++) {
          var t = i / n, p = A(t), q = B(t);
          out.push(['l', p[0], p[1], q[0], q[1], mix(c1, c2, t), alpha, 0.8]);
        }
      }
      return out;
    },
    rings: function (rng, c) {
      var out = [], n = 96;
      for (var pass = 0; pass < 2; pass++) {
        var dx = (0.04 + rng() * 0.08) * (rng() < 0.5 ? -1 : 1), dy = (0.04 + rng() * 0.08) * (rng() < 0.5 ? -1 : 1);
        var f1 = 0.5 + rng() * 1.5, f2 = 0.5 + rng() * 1.5, w = pass ? 0.9 : 1.2, a = pass ? 0.55 : 0.95;
        for (var i = 0; i < n; i++) {
          var t = i / (n - 1), r = 0.07 + 0.92 * Math.pow(t, 0.92);
          out.push(['c', dx * Math.sin(t * Math.PI * f1), dy * Math.cos(t * Math.PI * f2), r, mix(c[0], c[1], t), a, w]);
        }
      }
      return out;
    },
    burst: function (rng, c) {
      var out = [], n = 1100, a = 0.5 + rng() * 0.15, b = 0.18 + rng() * 0.12;
      var twist = 0.4 + rng() * 0.9, k = 1 + Math.floor(rng() * 3), rot = rng() * Math.PI;
      for (var i = 0; i < n; i++) {
        var th = i / n * TAU, ph = th + twist * Math.sin(k * th);
        var x1 = Math.cos(th), y1 = Math.sin(th);
        var ex = a * Math.cos(ph), ey = b * Math.sin(ph);
        var x2 = ex * Math.cos(rot) - ey * Math.sin(rot), y2 = ex * Math.sin(rot) + ey * Math.cos(rot);
        out.push(['l', x1, y1, x2, y2, mix(c[0], c[1], 0.5 + 0.5 * Math.sin(th * 2)), 0.42, 0.7]);
      }
      return out;
    },
    mesh: function (rng, c) {
      var out = [], n = 700, families = 3;
      for (var f = 0; f < families; f++) {
        var base = rng() * TAU, spread = 0.55 + rng() * 0.5;
        for (var i = 0; i < n; i++) {
          var t1 = base + (rng() - 0.5) * spread, t2 = base + Math.PI + (rng() - 0.5) * spread;
          out.push(['l', Math.cos(t1), Math.sin(t1), Math.cos(t2), Math.sin(t2), mix(c[0], c[1], rng()), 0.09, 0.7]);
        }
      }
      return out;
    }
  };

  function paint(strokes, from, to, R) {
    ctx.save();
    ctx.beginPath(); ctx.arc(R, R, R * 0.985, 0, TAU); ctx.clip();
    for (var i = from; i < to && i < strokes.length; i++) {
      var s = strokes[i];
      ctx.beginPath();
      if (s[0] === 'l') {
        ctx.moveTo(R + s[1] * R, R + s[2] * R); ctx.lineTo(R + s[3] * R, R + s[4] * R);
        ctx.strokeStyle = s[5]; ctx.globalAlpha = s[6]; ctx.lineWidth = s[7];
      } else {
        ctx.arc(R + s[1] * R, R + s[2] * R, s[3] * R, 0, TAU);
        ctx.strokeStyle = s[4]; ctx.globalAlpha = s[5]; ctx.lineWidth = s[6];
      }
      ctx.stroke();
    }
    ctx.restore();
  }

  function draw(animate) {
    if (frame) { cancelAnimationFrame(frame); frame = 0; }
    var rect = canvas.getBoundingClientRect();
    var S = Math.max(2, Math.round(Math.min(rect.width, rect.height) || rect.width));
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = S * dpr; canvas.height = S * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, S, S);
    var R = S / 2;

    var kind = cssVar('--disc-kind') || 'burst';
    var plate = cssVar('--plate') || '#f4efe6';
    var colours = ['--c1', '--c2', '--c3'].map(cssVar).filter(Boolean).map(rgb);
    if (!colours.length) { colours = [rgb('#8e0b0b')]; }
    while (colours.length < 2) { colours.push(colours[0]); }

    ctx.beginPath(); ctx.arc(R, R, R, 0, TAU); ctx.fillStyle = plate; ctx.globalAlpha = 1; ctx.fill();
    ctx.lineCap = 'butt';

    var strokes = (build[kind] || build.burst)(mulberry32(todaySeed()), colours);
    if (!animate || reduceMotion.matches) { paint(strokes, 0, strokes.length, R); return; }
    var per = Math.ceil(strokes.length / 60), i = 0;
    (function step() {
      paint(strokes, i, i + per, R);
      i += per;
      frame = i < strokes.length ? requestAnimationFrame(step) : 0;
    })();
  }

  var timer = 0;
  window.addEventListener('resize', function () {
    clearTimeout(timer);
    timer = setTimeout(function () { draw(false); }, 150);
  });
  /* The switcher (controls.js) changes data-disc on <html>; redraw when it does. */
  if (window.MutationObserver) {
    new MutationObserver(function (muts) {
      for (var i = 0; i < muts.length; i++) {
        if (muts[i].attributeName === 'data-disc') { draw(true); return; }
      }
    }).observe(root, { attributes: true, attributeFilter: ['data-disc'] });
  }
  draw(true);
})();
