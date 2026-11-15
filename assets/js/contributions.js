(() => {
  const page = document.querySelector('.contributions-page');
  const tablist = page && page.querySelector('.contrib-tabs');
  if (!tablist) return;
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const motionStyle = getComputedStyle(page);
  const motionOptions = {
    duration: parseFloat(motionStyle.getPropertyValue('--dur-fast')) || 180,
    easing: motionStyle.getPropertyValue('--ease-out').trim() || 'ease-out',
  };

  function enter(element) {
    if (reduceMotion.matches || !element.animate) return;
    for (const animation of element.getAnimations()) animation.cancel();
    element.animate(
      [{ opacity: 0, transform: 'translateY(6px)' }, { opacity: 1, transform: 'none' }],
      motionOptions,
    );
  }

  // Without JS both panels and all entry details remain readable.
  const tabs = [...tablist.querySelectorAll('[role="tab"]')];
  for (const tab of tabs) {
    const panel = document.getElementById(tab.getAttribute('aria-controls'));
    panel.setAttribute('role', 'tabpanel');
    panel.setAttribute('aria-labelledby', tab.id);
    panel.tabIndex = 0;
    panel.hidden = tab.getAttribute('aria-selected') !== 'true';
    for (const title of panel.querySelectorAll('.contrib-panel-title')) title.hidden = true;
  }
  tablist.hidden = false;

  function activateTab(activeTab, moveFocus = false) {
    for (const tab of tabs) {
      const selected = tab === activeTab;
      const wasSelected = tab.getAttribute('aria-selected') === 'true';
      tab.setAttribute('aria-selected', String(selected));
      tab.tabIndex = selected ? 0 : -1;
      const panel = document.getElementById(tab.getAttribute('aria-controls'));
      panel.hidden = !selected;
      if (selected && !wasSelected) enter(panel);
    }
    if (moveFocus) activeTab.focus({ preventScroll: true });
  }
  for (const tab of tabs) {
    tab.addEventListener('click', () => activateTab(tab));
    tab.addEventListener('keydown', (event) => {
      let index = tabs.indexOf(tab);
      if (event.key === 'ArrowRight') index = (index + 1) % tabs.length;
      else if (event.key === 'ArrowLeft') index = (index + tabs.length - 1) % tabs.length;
      else if (event.key === 'Home') index = 0;
      else if (event.key === 'End') index = tabs.length - 1;
      else return;
      event.preventDefault();
      activateTab(tabs[index], true);
    });
  }

  const explorer = page.querySelector('.contrib-explorer');
  const dialog = page.querySelector('.contribution-dialog');
  const search = explorer.querySelector('input[type="search"]');
  const filters = [...explorer.querySelectorAll('[data-filter]')];
  const views = [...explorer.querySelectorAll('.view-switch button')];
  const expandButton = explorer.querySelector('.expand-entries');
  const empty = explorer.querySelector('.contrib-empty');
  const groups = [...explorer.querySelectorAll('.project-group')].map(element => ({
    element,
    entries: [...element.querySelectorAll('.contrib-entry')].map(entry => ({
      element: entry,
      details: entry.querySelector('details'),
      summary: entry.querySelector('summary'),
      text: `${element.dataset.project} ${entry.textContent}`.toLowerCase(),
    })),
  }));
  let filter = 'all';
  let view = 'cards';
  let opener;
  const canShowDialog = typeof dialog.showModal === 'function';

  function visibleEntries() {
    return groups.flatMap(group => group.entries.filter(entry => !entry.element.hidden));
  }

  function updateExpandButton() {
    const visible = visibleEntries();
    expandButton.hidden = view !== 'list' || !visible.length;
    expandButton.textContent = visible.length && visible.every(entry => entry.details.open)
      ? 'Collapse descriptions' : 'Expand descriptions';
  }

  function applyFilters() {
    const query = search.value.trim().toLowerCase();
    let entryCount = 0;
    let projectCount = 0;
    for (const group of groups) {
      let count = 0;
      for (const entry of group.entries) {
        entry.element.hidden = (filter !== 'all' && filter !== group.element.dataset.category)
          || !entry.text.includes(query);
        if (!entry.element.hidden) count++;
      }
      group.element.hidden = count === 0;
      group.element.querySelector('.project-count').textContent = count;
      entryCount += count;
      if (count) projectCount++;
    }
    explorer.querySelector('.result-count').textContent =
      `${entryCount} ${entryCount === 1 ? 'entry' : 'entries'} · ${projectCount} ${projectCount === 1 ? 'project' : 'projects'}`;
    empty.hidden = entryCount !== 0;
    for (const button of filters) button.setAttribute('aria-pressed', String(button.dataset.filter === filter));
    updateExpandButton();
  }

  function setView(nextView) {
    view = nextView;
    explorer.dataset.view = view;
    for (const button of views) button.setAttribute('aria-pressed', String(button.dataset.view === view));
    for (const group of groups) {
      for (const entry of group.entries) {
        entry.details.open = false;
        if (view === 'cards' && canShowDialog) entry.summary.setAttribute('aria-haspopup', 'dialog');
        else entry.summary.removeAttribute('aria-haspopup');
      }
    }
    updateExpandButton();
  }

  for (const group of groups) {
    for (const entry of group.entries) {
      entry.details.addEventListener('toggle', updateExpandButton);
      entry.summary.addEventListener('click', event => {
        if (view !== 'cards' || !canShowDialog) return;
        event.preventDefault();
        opener = entry.summary;
        dialog.querySelector('.dialog-project').textContent =
          `${group.element.dataset.project} · ${entry.element.querySelector('.entry-id').textContent}`;
        dialog.querySelector('h3').textContent = entry.element.querySelector('.entry-title').textContent;
        const content = dialog.querySelector('.dialog-content');
        content.replaceChildren(entry.element.querySelector('.entry-detail').cloneNode(true));
        const note = group.element.querySelector('.adoption-note');
        if (note) {
          const label = document.createElement('p');
          label.className = 'dialog-note-label';
          label.textContent = 'Project context';
          content.append(label, note.cloneNode(true));
        }
        dialog.showModal();
      });
    }
  }
  dialog.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => {
    if (opener && opener.isConnected) opener.focus({ preventScroll: true });
  });
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right
      || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
  });
  for (const button of filters) {
    button.querySelector('.filter-count').textContent = groups
      .filter(group => button.dataset.filter === 'all' || group.element.dataset.category === button.dataset.filter)
      .reduce((count, group) => count + group.entries.length, 0);
    button.addEventListener('click', () => {
      filter = button.dataset.filter;
      applyFilters();
    });
  }
  for (const button of views) button.addEventListener('click', () => setView(button.dataset.view));
  search.addEventListener('input', applyFilters);
  empty.querySelector('button').addEventListener('click', () => {
    filter = 'all';
    search.value = '';
    applyFilters();
    search.focus();
  });
  expandButton.addEventListener('click', () => {
    const visible = visibleEntries();
    const expand = !visible.every(entry => entry.details.open);
    for (const entry of visible) entry.details.open = expand;
    updateExpandButton();
  });
  explorer.classList.add('is-enhanced');
  setView('cards');
  applyFilters();
  explorer.querySelector('.explorer-controls').hidden = false;
})();
