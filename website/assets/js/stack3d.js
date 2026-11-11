/* Exploded layer-stack viewer: CSS-3D orbit over the neon
   per-layer renders. Drag to rotate; auto-spin while idle if the
   SPIN toggle is on; EXPLODE slider drives the Z separation;
   chips toggle/isolate layers; ISO/TOP/EDGE jump to presets. */
(function () {
  var stage = document.getElementById('stack-stage');
  var scene = document.getElementById('stack-scene');
  if (!stage || !scene) return;
  var layers = Array.prototype.slice.call(
    scene.querySelectorAll('.stack-layer'));
  var slab = scene.querySelector('.stack-slab');
  var gapInput = document.getElementById('stack-gap');
  var spinInput = document.getElementById('stack-spin');
  var chips = Array.prototype.slice.call(
    document.querySelectorAll('.stack-chip'));

  var rx = 56, rz = -32, gap = gapInput ? +gapInput.value : 30;
  var dragging = false, lastX = 0, lastY = 0, lastTouch = 0;

  function apply() {
    scene.style.transform = 'translate(-50%, -50%) ' +
      'rotateX(' + rx + 'deg) rotateZ(' + rz + 'deg)';
    var n = layers.length;
    layers.forEach(function (el, i) {
      el.style.transform =
        'translateZ(' + ((n - 1 - i) * gap) + 'px)';
    });
    if (slab) slab.style.transform = 'translateZ(-7px)';
  }

  function frame() {
    if (!dragging && spinInput && spinInput.checked &&
        performance.now() - lastTouch > 2500) {
      rz += 0.12;
      apply();
    }
    requestAnimationFrame(frame);
  }

  stage.addEventListener('pointerdown', function (e) {
    dragging = true; lastX = e.clientX; lastY = e.clientY;
    lastTouch = performance.now();
    stage.setPointerCapture(e.pointerId);
  });
  stage.addEventListener('pointermove', function (e) {
    if (!dragging) return;
    rz += (e.clientX - lastX) * 0.4;
    rx -= (e.clientY - lastY) * 0.3;
    rx = Math.max(4, Math.min(84, rx));
    lastX = e.clientX; lastY = e.clientY;
    lastTouch = performance.now();
    apply();
  });
  ['pointerup', 'pointercancel'].forEach(function (t) {
    stage.addEventListener(t, function () {
      dragging = false; lastTouch = performance.now();
    });
  });

  if (gapInput) gapInput.addEventListener('input', function () {
    gap = +gapInput.value; lastTouch = performance.now(); apply();
  });
  if (spinInput) spinInput.addEventListener('change', function () {
    lastTouch = performance.now();
  });

  document.querySelectorAll('[data-view]').forEach(function (b) {
    b.addEventListener('click', function () {
      var v = b.getAttribute('data-view');
      if (v === 'iso') { rx = 56; rz = -32; }
      if (v === 'top') { rx = 3; rz = 0; }
      if (v === 'edge') { rx = 82; rz = -90; }
      scene.classList.add('anim');
      apply();
      setTimeout(function () { scene.classList.remove('anim'); }, 650);
      lastTouch = performance.now();
    });
  });

  chips.forEach(function (chip) {
    var name = chip.getAttribute('data-name');
    var el = layers.filter(function (l) {
      return l.getAttribute('data-name') === name;
    })[0];
    if (!el) return;
    chip.addEventListener('click', function () {
      var on = chip.getAttribute('aria-pressed') !== 'true';
      chip.setAttribute('aria-pressed', on ? 'true' : 'false');
      el.classList.toggle('off', !on);
    });
    chip.addEventListener('pointerenter', function () {
      layers.forEach(function (l) {
        if (l !== el && !l.classList.contains('off'))
          l.classList.add('dim');
      });
    });
    chip.addEventListener('pointerleave', function () {
      layers.forEach(function (l) { l.classList.remove('dim'); });
    });
  });

  apply();
  requestAnimationFrame(frame);
})();
