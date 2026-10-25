(() => {
  const pane = document.getElementById('detail-pane');
  const records = Array.from(pane.querySelectorAll('.detail-content'));
  const triggers = Array.from(document.querySelectorAll('[data-select]'));
  const placeholder = pane.querySelector('.detail-placeholder');
  const recordById = new Map(records.map(el => [el.dataset.id, el]));
  const recordByAnchor = new Map(records.map(el => [el.id, el]));
  let lastTrigger = null;
  const stagePanels = Array.from(document.querySelectorAll('[data-stage-panel]'));
  const stageLinks = Array.from(document.querySelectorAll('[data-stage-nav]'));
  const designCards = Array.from(document.querySelectorAll('[data-design-card]'));
  const showDesign = id => {
    const card = designCards.find(el => el.dataset.designCard === id);
    if (!card) return;
    const gallery = card.closest('.design-gallery');
    const index = gallery.querySelector('.design-index');
    if (matchMedia('(max-width: 650px)').matches) {
      index.open = false;
      index.querySelector('summary').textContent = card.querySelector('h3').textContent + ' · 切换图示';
    }
    gallery.querySelectorAll('[data-design-card]').forEach(el => { el.hidden = el !== card; });
    gallery.querySelectorAll('[data-design-select]').forEach(el => {
      const active = el.dataset.designSelect === id;
      el.classList.toggle('is-active', active);
      if (active) el.setAttribute('aria-current', 'page'); else el.removeAttribute('aria-current');
    });
  };
  const showStage = name => {
    if (!stagePanels.some(el => el.dataset.stagePanel === name)) return false;
    stagePanels.forEach(el => { el.hidden = el.dataset.stagePanel !== name; });
    stageLinks.forEach(el => {
      const active = el.dataset.stageNav === name;
      el.classList.toggle('is-active', active);
      if (active) el.setAttribute('aria-current', 'step'); else el.removeAttribute('aria-current');
    });
    return true;
  };
  const select = (id, focus = false) => {
    const record = recordById.get(id);
    if (!record) return false;
    if (record.dataset.recordStage) showStage(record.dataset.recordStage);
    showDesign(id);
    records.forEach(el => { el.hidden = el !== record; });
    placeholder.hidden = true;
    triggers.forEach(el => {
      const active = el.dataset.select === id;
      el.classList.toggle('is-selected', active);
      if (active) el.setAttribute('aria-current', 'true'); else el.removeAttribute('aria-current');
    });
    document.querySelectorAll('[data-edge-id]').forEach(el => {
      el.classList.toggle('is-connected', el.dataset.edgeId === id || el.dataset.from === id || el.dataset.to === id);
    });
    if (focus) {
      record.querySelector('h2').focus({preventScroll: true});
      if (matchMedia('(max-width: 1200px)').matches) pane.scrollIntoView({block: 'start', behavior: 'instant'});
    }
    return true;
  };
  const resolveHash = () => {
    const key = location.hash.slice(1);
    const record = recordByAnchor.get(key);
    if (record) return select(record.dataset.id);
    if (key.startsWith('design-') || key.startsWith('decision-')) {
      let target;
      try { target = document.getElementById(decodeURIComponent(key)); } catch { return false; }
      const item = target?.querySelector('.design-viewer')?.dataset.designId || target?.dataset.decisionItem;
      if (item) {
        select(item);
        for (let parent = target.parentElement; parent; parent = parent.parentElement) {
          if (parent.tagName === 'DETAILS') parent.open = true;
        }
        requestAnimationFrame(() => target.scrollIntoView({block: 'start'}));
        return true;
      }
    }
    if (key.startsWith('feedback-')) {
      const area = document.getElementById(key);
      if (!area) return false;
      const stage = area.closest('[data-stage-panel]');
      if (stage) showStage(stage.dataset.stagePanel);
      area.open = true;
      requestAnimationFrame(() => area.scrollIntoView({block: 'start'}));
      return true;
    }
    if (key.startsWith('stage-') && showStage(key.slice(6))) {
      const first = records.find(el => el.dataset.recordStage === key.slice(6));
      if (first) select(first.dataset.id);
      else { records.forEach(el => { el.hidden = true; }); placeholder.hidden = false; }
      return true;
    }
    return false;
  };
  let handledHash = null;
  const fromHash = (force = false) => {
    if (!force && handledHash === location.hash) return true;
    const handled = resolveHash();
    handledHash = handled ? location.hash : null;
    return handled;
  };
  document.documentElement.classList.add('interactive');
  document.querySelectorAll('.design-gallery').forEach(el => showDesign(el.querySelector('[data-design-card]')?.dataset.designCard));
  showStage(document.body.dataset.currentStage);
  if (!fromHash()) select(pane.dataset.default);
  triggers.forEach(el => el.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    // Related links disappear with their panel; keep a return target on the map.
    if (!pane.contains(el)) lastTrigger = el;
    if (select(el.dataset.select, true)) {
      history.pushState(null, '', el.getAttribute('href'));
    }
  }));
  stageLinks.forEach(el => el.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    history.pushState(null, '', el.getAttribute('href'));
    fromHash(true);
  }));
  document.querySelectorAll('[data-design-select]').forEach(el => el.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    history.pushState(null, '', el.getAttribute('href'));
    fromHash(true);
  }));
  window.addEventListener('hashchange', () => { if (!fromHash()) select(pane.dataset.default); });
  window.addEventListener('popstate', () => { if (!fromHash()) select(pane.dataset.default); });
  pane.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      const visible = el => el && el.isConnected && el.getClientRects().length > 0;
      const fallback = triggers.find(el => !pane.contains(el) &&
        el.dataset.select === records.find(record => !record.hidden)?.dataset.id && visible(el));
      const target = visible(lastTrigger) ? lastTrigger : fallback;
      if (target) { event.preventDefault();target.focus(); }
    }
  });
})();
