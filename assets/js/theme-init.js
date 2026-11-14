(() => {
  let theme = 'dark';
  try {
    const stored = localStorage.getItem('theme');
    if (stored === 'dark' || stored === 'light') theme = stored;
  } catch { /* Keep the dark default when storage is unavailable. */ }
  document.documentElement.dataset.theme = theme;
})();
