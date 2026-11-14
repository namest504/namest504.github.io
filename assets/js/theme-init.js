(() => {
  let theme = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  try {
    const stored = localStorage.getItem('theme');
    if (stored === 'dark' || stored === 'light') theme = stored;
  } catch { /* The system preference still works when storage is unavailable. */ }
  document.documentElement.dataset.theme = theme;
})();
