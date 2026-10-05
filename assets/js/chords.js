/* Chords on a circle.
   Redraws the drawing at the top of the page on a canvas, so it fits any
   screen and both colour schemes. Thousands of straight lines join random
   pairs of points on one very large circle whose left edge sits just inside
   the frame and whose centre is far off to the right, as in the original
   image. The seed is today's date, so the drawing changes once a day and is
   otherwise stable. No libraries. */
(function () {
  'use strict';

  var canvas = document.getElementById('chords');
  if (!canvas || !canvas.getContext) { return; }
  var ctx = canvas.getContext('2d');
  var root = document.documentElement;
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var darkScheme = window.matchMedia('(prefers-color-scheme: dark)');
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

  function cssVar(name) {
    return getComputedStyle(root).getPropertyValue(name).trim();
  }

  /* Choose the chords. Endpoints are uniform on the circumference, which on
     its own produces the denser rim the original has; nothing is added. Only
     chords whose bounding box touches the frame are kept. */
  function plan(W, H, rng) {
    var R = 1.30 * W;
    var cx = 0.10 * W + R;
    var cy = 0.55 * H;
    var N = Math.round(3400 * (W * H) / (1920 * 1280));
    N = Math.max(1200, Math.min(6000, N));
    var chords = [];
    var tries = 0, cap = N * 20;
    var TAU = Math.PI * 2;
    while (chords.length < N && tries++ < cap) {
      var a = rng() * TAU, b = rng() * TAU;
      var x1 = cx + R * Math.cos(a), y1 = cy + R * Math.sin(a);
      var x2 = cx + R * Math.cos(b), y2 = cy + R * Math.sin(b);
      if (Math.max(x1, x2) < 0 || Math.min(x1, x2) > W ||
          Math.max(y1, y2) < 0 || Math.min(y1, y2) > H) { continue; }
      var heavy = rng() < 1 / 80;
      chords.push([x1, y1, x2, y2,
        heavy ? 0.45 : 0.08 + 0.11 * rng(),
        heavy ? 0.9 : 0.75]);
    }
    return chords;
  }

  function strokeRange(chords, from, to, rgb, alphaScale) {
    for (var i = from; i < to && i < chords.length; i++) {
      var c = chords[i];
      ctx.globalAlpha = c[4] * alphaScale;
      ctx.lineWidth = c[5];
      ctx.strokeStyle = 'rgb(' + rgb + ')';
      ctx.beginPath();
      ctx.moveTo(c[0], c[1]);
      ctx.lineTo(c[2], c[3]);
      ctx.stroke();
    }
  }

  function draw(animate) {
    if (frame) { cancelAnimationFrame(frame); frame = 0; }
    var rect = canvas.getBoundingClientRect();
    var W = Math.max(1, Math.round(rect.width));
    var H = Math.max(1, Math.round(rect.height));
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);
    ctx.lineCap = 'butt';

    var rgb = cssVar('--ink-rgb') || '26, 24, 22';
    var alphaScale = parseFloat(cssVar('--chord-alpha')) || 1;
    var chords = plan(W, H, mulberry32(todaySeed()));

    if (!animate || reduceMotion.matches) {
      strokeRange(chords, 0, chords.length, rgb, alphaScale);
      return;
    }
    var perFrame = Math.ceil(chords.length / 60);
    var i = 0;
    (function step() {
      strokeRange(chords, i, i + perFrame, rgb, alphaScale);
      i += perFrame;
      frame = i < chords.length ? requestAnimationFrame(step) : 0;
    })();
  }

  var resizeTimer = 0;
  function onResize() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () { draw(false); }, 150);
  }

  draw(true);
  window.addEventListener('resize', onResize);
  if (darkScheme.addEventListener) {
    darkScheme.addEventListener('change', function () { draw(false); });
  } else if (darkScheme.addListener) {
    darkScheme.addListener(function () { draw(false); });
  }
})();
