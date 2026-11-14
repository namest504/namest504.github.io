(() => {
  const root = document.documentElement;
  const buttons = document.querySelectorAll('[data-theme-toggle]');
  const canvas = document.getElementById('ambient');
  const context = canvas?.getContext('2d');
  const main = document.getElementById('main');
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const finePointer = matchMedia('(min-width: 769px) and (hover: hover) and (pointer: fine)');
  const spacing = 32;
  const radius = 140;
  let width = 0;
  let height = 0;
  let points = new Float32Array(0);
  let frame = 0;
  let pointerX = -1000;
  let pointerY = -1000;
  let contentLeft = 0;
  let contentRight = 0;
  let color = '';
  let suspended = false;

  function syncTheme() {
    const dark = root.dataset.theme === 'dark';
    for (const button of buttons) {
      button.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
    }
    color = getComputedStyle(root).getPropertyValue('--color-muted').trim();
    requestPaint();
  }

  for (const button of buttons) {
    button.addEventListener('click', () => {
      const theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
      root.dataset.theme = theme;
      try { localStorage.setItem('theme', theme); } catch { /* Theme still changes without storage. */ }
      syncTheme();
    });
  }

  function interactive() {
    return finePointer.matches && !reducedMotion.matches;
  }

  function paint() {
    frame = 0;
    if (!context || suspended || document.hidden) return;
    context.clearRect(0, 0, width, height);
    context.fillStyle = color;
    const moves = interactive();
    let settling = false;
    for (let i = 0; i < points.length; i += 4) {
      const x = points[i];
      const y = points[i + 1];
      let targetX = x;
      let targetY = y;
      if (moves) {
        const dx = x - pointerX;
        const dy = y - pointerY;
        const distanceSquared = dx * dx + dy * dy;
        if (distanceSquared > 0 && distanceSquared < radius * radius) {
          const distance = Math.sqrt(distanceSquared);
          const displacement = 12 * (1 - distance / radius) ** 2;
          targetX += dx / distance * displacement;
          targetY += dy / distance * displacement;
        }
      }
      const deltaX = targetX - points[i + 2];
      const deltaY = targetY - points[i + 3];
      if (moves && (Math.abs(deltaX) > 0.03 || Math.abs(deltaY) > 0.03)) {
        points[i + 2] += deltaX * 0.18;
        points[i + 3] += deltaY * 0.18;
        settling = true;
      } else {
        points[i + 2] = targetX;
        points[i + 3] = targetY;
      }
      // Keep the reading column 94% quieter, fading across its outer 48px.
      const cover = Math.max(0, Math.min(1, (x - contentLeft + 48) / 48, (contentRight + 48 - x) / 48));
      context.globalAlpha = 0.16 * (1 - cover * 0.94);
      context.beginPath();
      context.arc(points[i + 2], points[i + 3], 0.9, 0, Math.PI * 2);
      context.fill();
    }
    context.globalAlpha = 1;
    // No continuous idle animation or hidden-tab work.
    if (settling) requestPaint();
  }

  function requestPaint() {
    if (context && !frame && !suspended && !document.hidden) frame = requestAnimationFrame(paint);
  }

  function resize() {
    if (!context) return;
    width = window.innerWidth;
    height = window.innerHeight;
    const ratio = Math.min(window.devicePixelRatio || 1, 1.5);
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    const bounds = main.getBoundingClientRect();
    contentLeft = bounds.left;
    contentRight = bounds.right;
    const columns = Math.ceil(width / spacing);
    const rows = Math.ceil(height / spacing);
    points = new Float32Array(columns * rows * 4);
    let i = 0;
    for (let row = 0; row < rows; row++) {
      for (let column = 0; column < columns; column++) {
        const x = column * spacing + spacing / 2;
        const y = row * spacing + spacing / 2;
        points[i++] = x;
        points[i++] = y;
        points[i++] = x;
        points[i++] = y;
      }
    }
    requestPaint();
  }

  function resetPointer() {
    pointerX = pointerY = -1000;
    requestPaint();
  }

  syncTheme();
  if (!context || !main) return;
  resize();
  window.addEventListener('resize', resize, { passive: true });
  window.addEventListener('pointermove', event => {
    if (!interactive() || event.pointerType === 'touch') return;
    pointerX = event.clientX;
    pointerY = event.clientY;
    requestPaint();
  }, { passive: true });
  document.documentElement.addEventListener('pointerleave', resetPointer);
  window.addEventListener('blur', resetPointer);
  reducedMotion.addEventListener('change', resetPointer);
  finePointer.addEventListener('change', resetPointer);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      cancelAnimationFrame(frame);
      frame = 0;
    } else resetPointer();
  });
  window.addEventListener('pagehide', () => {
    suspended = true;
    cancelAnimationFrame(frame);
    frame = 0;
  });
  window.addEventListener('pageshow', () => {
    suspended = false;
    resize();
  });
})();
