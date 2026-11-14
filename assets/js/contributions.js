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

  // Without JS both panels and every project list stay visible; turn them into tabs and disclosures here.
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

  function setExpanded(button, expanded) {
    button.setAttribute('aria-expanded', String(expanded));
    button.setAttribute('aria-label', `${expanded ? 'Hide' : 'Show'} contributions to ${button.dataset.project}`);
    button.querySelector('.toggle-sign').textContent = expanded ? '−' : '+';
    document.getElementById(button.getAttribute('aria-controls')).hidden = !expanded;
  }
  for (const button of page.querySelectorAll('.project-toggle')) {
    const count = button.parentElement.querySelector('.project-count');
    if (count) count.hidden = true;
    setExpanded(button, false);
    button.hidden = false;
    button.addEventListener('click', () => {
      const expanded = button.getAttribute('aria-expanded') !== 'true';
      setExpanded(button, expanded);
      if (expanded) enter(document.getElementById(button.getAttribute('aria-controls')));
    });
  }
})();
