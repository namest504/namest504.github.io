// Article enhancements. Harmless on pages without code blocks or diagrams.
// - Copy buttons for code blocks (layouts/_markup/render-codeblock.html).
//   The copied text is each .code-line's text joined by "\n". Notes (.code-note) sit outside
//   .code-line, so they are never copied; diff blocks keep their +/-/space markers.
// - Wide inline SVG diagrams that scroll sideways get a keyboard stop.
// - Native heading links in a sticky table of contents, collapsed on narrow screens.
(() => {
  const SUCCESS_MS = 2000;
  const FAILURE_MS = 6000;

  const toc = document.querySelector('[data-article-toc]');
  if (toc) {
    const wide = matchMedia('(min-width: 1200px)');
    const summary = toc.querySelector('summary');
    const resizeToc = () => { toc.open = wide.matches; };
    resizeToc();
    wide.addEventListener('change', resizeToc);

    toc.addEventListener('click', event => {
      const link = event.target.closest('a[href^="#"]');
      if (!link) return;
      if (!wide.matches) toc.open = false;
      // Preserve native fragment navigation while moving keyboard focus into the article.
      const heading = document.getElementById(decodeURIComponent(link.hash.slice(1)));
      if (heading) {
        heading.tabIndex = -1;
        heading.focus({ preventScroll: true });
      }
    });
    toc.addEventListener('keydown', event => {
      if (event.key !== 'Escape' || !toc.open) return;
      toc.open = false;
      summary.focus({ preventScroll: true });
    });
    document.addEventListener('click', event => {
      if (!wide.matches && toc.open && !toc.contains(event.target)) toc.open = false;
    });
  }

  function blockText(figure) {
    return Array.from(figure.querySelectorAll('.code-line'), (line) => line.textContent).join('\n');
  }

  function legacyCopy(text) {
    const area = document.createElement('textarea');
    area.value = text;
    area.setAttribute('readonly', '');
    area.style.position = 'fixed';
    area.style.top = '0';
    area.style.left = '0';
    area.style.opacity = '0';
    document.body.append(area);
    area.select();
    let copied = false;
    try {
      copied = document.execCommand('copy');
    } finally {
      area.remove();
    }
    if (!copied) throw new Error('execCommand("copy") returned false');
  }

  async function copyText(text) {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
      try {
        await navigator.clipboard.writeText(text);
        return;
      } catch (clipboardError) {
        // Permission denied or insecure context: try the legacy path before reporting failure.
        try {
          legacyCopy(text);
          return;
        } catch {
          throw clipboardError;
        }
      }
    }
    legacyCopy(text);
  }

  for (const figure of document.querySelectorAll('[data-code-block]')) {
    const button = figure.querySelector('[data-copy-code]');
    const status = figure.querySelector('.code-status');
    if (!button || !status) continue;

    const idleLabel = button.textContent;
    const isDiff = figure.classList.contains('is-diff');
    let resetTimer = 0;

    const setState = (state, label, message, resetAfter) => {
      window.clearTimeout(resetTimer);
      button.textContent = label;
      button.dataset.state = state;
      status.dataset.state = state;
      status.textContent = message;
      if (resetAfter) {
        resetTimer = window.setTimeout(() => {
          button.textContent = idleLabel;
          delete button.dataset.state;
          delete status.dataset.state;
          status.textContent = '';
        }, resetAfter);
      }
    };

    button.addEventListener('click', async () => {
      const text = blockText(figure);
      const lineCount = text.split('\n').length;
      button.setAttribute('aria-busy', 'true');
      try {
        await copyText(text);
        const what = isDiff ? 'diff lines with +/- markers' : 'lines';
        setState('copied', 'Copied', `Copied ${lineCount} ${what}`, SUCCESS_MS);
      } catch (error) {
        const reason = error && error.name === 'NotAllowedError' ? 'clipboard access was blocked' : 'the browser refused to copy';
        setState('failed', 'Copy failed', `Copy failed: ${reason}. Select the code and copy it manually.`, FAILURE_MS);
      } finally {
        button.removeAttribute('aria-busy');
      }
    });

    button.hidden = false;
  }

  // render-image inlines diagrams as <figure class="diagram"><svg …></figure>.
  // When the figure is narrower than the SVG, make it focusable so arrow keys can scroll it.
  const diagrams = document.querySelectorAll('.post-body figure.diagram');
  if (diagrams.length && 'ResizeObserver' in window) {
    const update = (figure) => {
      const scrollable = figure.scrollWidth > figure.clientWidth + 1;
      if (scrollable && !figure.hasAttribute('tabindex')) {
        figure.tabIndex = 0;
        figure.setAttribute('role', 'group');
        const title = figure.querySelector('svg title');
        figure.setAttribute('aria-label', title ? title.textContent : 'Diagram');
      } else if (!scrollable && figure.hasAttribute('tabindex')) {
        figure.removeAttribute('tabindex');
        figure.removeAttribute('role');
        figure.removeAttribute('aria-label');
      }
    };
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) update(entry.target);
    });
    for (const figure of diagrams) observer.observe(figure);
  }
})();
