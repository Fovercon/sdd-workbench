/* The engine is bundled locally; the contract source is never rewritten. */
(() => {
  const viewers = [...document.querySelectorAll('.design-viewer')];
  if (!viewers.length) return;
  const font = '"PingFang SC", "Microsoft YaHei", Arial, sans-serif';
  const config = {
    startOnLoad: false, securityLevel: 'strict', suppressErrorRendering: true,
    theme: 'base', look: 'classic', layout: 'dagre', fontFamily: font, htmlLabels: false, maxTextSize: 60000,
    maxEdges: 300, deterministicIds: true, deterministicIDSeed: 'sdd-design',
    themeVariables: {
      fontFamily: font, fontSize: '17px', primaryColor: '#f5f9fa', primaryTextColor: '#263e4a',
      primaryBorderColor: '#8faab5', secondaryColor: '#f1f6f1', tertiaryColor: '#faf6ed',
      lineColor: '#78939e', textColor: '#263e4a', mainBkg: '#f5f9fa',
      nodeBorder: '#8faab5', clusterBkg: '#f8fafb', clusterBorder: '#d3dfe3',
      edgeLabelBackground: '#ffffff', actorBkg: '#f2f7f9', actorBorder: '#8faab5',
      actorTextColor: '#263e4a', actorLineColor: '#c1d0d6', signalColor: '#5d7e8c',
      signalTextColor: '#243b56', noteBkgColor: '#fff9ea', noteBorderColor: '#d5c59a',
      noteTextColor: '#65552f', labelBoxBkgColor: '#eef4fc', labelBoxBorderColor: '#7e9bc4',
      activationBkgColor: '#dbe8fa', activationBorderColor: '#8ca8ce'
    },
    flowchart: {htmlLabels: false, curve: 'basis', nodeSpacing: 42, rankSpacing: 64, padding: 20, wrappingWidth: 260, useMaxWidth: false},
    sequence: {useMaxWidth: false, actorMargin: 65, messageMargin: 38, diagramMarginX: 30,
      diagramMarginY: 24, wrap: true, mirrorActors: false},
    class: {useMaxWidth: false, hideEmptyMembersBox: true},
    state: {useMaxWidth: false, padding: 18, nodeSpacing: 70, rankSpacing: 90,
      labelHeight: 48, fontSize: 16, fontSizeFactor: 10, wrappingWidth: 280},
    er: {useMaxWidth: false, entityPadding: 18}
  };
  config.themeCSS = '.node rect,.node polygon,.node circle,.node path,.classGroup rect,.label-container,.note{filter:none!important;stroke-width:1.2px!important}.edgePath path,.flowchart-link{stroke-width:1.2px!important}';
  config.secure = [...Object.keys(config), 'secure', 'themeCSS', 'layout'];
  mermaid.initialize(config);

  const dialog = document.createElement('dialog');
  dialog.className = 'design-dialog';
  dialog.innerHTML = '<header><div><p>设计视图 · 放大阅读</p><h2 id="design-dialog-title"></h2></div>' +
    '<button type="button" class="design-dialog-close" aria-label="关闭放大视图">关闭 ×</button></header><div class="design-dialog-body"></div>';
  dialog.setAttribute('aria-labelledby', 'design-dialog-title');
  document.body.append(dialog);
  let expanded = null;
  const state = new WeakMap();
  function resize(viewer, fit = false) {
    const s = state.get(viewer);
    if (!s) return;
    const canvas = viewer.querySelector('.design-figure');
    const svg = canvas.querySelector('svg');
    if (fit) {
      s.scale = Math.min(1, Math.max(0.1, (canvas.clientWidth - 48) / s.width));
      if (expanded?.viewer === viewer) s.scale = Math.min(s.scale, (canvas.clientHeight - 48) / s.height);
    }
    svg.style.width = `${Math.max(1, s.width * s.scale)}px`;
    svg.style.height = `${Math.max(1, s.height * s.scale)}px`;
    viewer.querySelector('[data-diagram-action="fit"]').textContent = `${Math.round(s.scale * 100)}% · 适应`;
    if (fit) { canvas.scrollLeft = 0; canvas.scrollTop = 0; }
  }
  function readable(viewer) {
    if (!state.has(viewer)) return;
    resize(viewer, true);
    const s = state.get(viewer), canvas = viewer.querySelector('.design-figure');
    const overview = viewer.dataset.technical !== 'true' && innerWidth > 650;
    if (overview) s.scale = Math.min(s.scale, Math.max(0.1, (canvas.clientHeight - 48) / s.height));
    s.scale = Math.max(overview ? .55 : .65, s.scale);
    resize(viewer);
  }
  function close() { if (dialog.open) dialog.close(); }
  dialog.querySelector('.design-dialog-close').addEventListener('click', close);
  dialog.addEventListener('click', e => { if (e.target === dialog) close(); });
  dialog.addEventListener('close', () => {
    if (!expanded) return;
    const {viewer, placeholder, trigger} = expanded;
    placeholder.replaceWith(viewer);
    viewer.querySelector('[data-diagram-action="expand"]').textContent = '放大查看 ↗';
    expanded = null;
    document.body.classList.remove('design-dialog-open');
    readable(viewer);
    trigger.focus({preventScroll: true});
  });
  function expand(viewer, trigger) {
    if (expanded) return close();
    const placeholder = document.createComment('design-viewer');
    viewer.replaceWith(placeholder);
    expanded = {viewer, placeholder, trigger};
    dialog.querySelector('h2').textContent = viewer.dataset.title;
    const card = placeholder.parentElement;
    const badge = card.querySelector('.badge');
    dialog.querySelector('header .badge')?.remove();
    if (badge) dialog.querySelector('header>div').append(badge.cloneNode(true));
    dialog.querySelector('.design-dialog-body').append(viewer);
    viewer.querySelector('[data-diagram-action="expand"]').textContent = '返回看板 ↙';
    document.body.classList.add('design-dialog-open');
    dialog.showModal();
    resize(viewer, true);
    // Opening a large sequence should improve legibility. Fit remains an explicit
    // option when the reader wants the complete overview instead of scrollable detail.
    state.get(viewer).scale = Math.max(.85, state.get(viewer).scale);
    resize(viewer);
  }
  viewers.forEach(viewer => viewer.addEventListener('click', e => {
    const button = e.target.closest('[data-diagram-action]');
    if (!button || button.disabled) return;
    const action = button.dataset.diagramAction;
    const s = state.get(viewer);
    if (action === 'expand') return expand(viewer, button);
    if (action === 'download') {
      const svg = viewer.querySelector('svg').cloneNode(true);
      svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
      svg.style.width = `${s.width}px`; svg.style.height = `${s.height}px`;
      const blob = new Blob([new XMLSerializer().serializeToString(svg)], {type: 'image/svg+xml;charset=utf-8'});
      const url = URL.createObjectURL(blob), a = document.createElement('a');
      a.href = url; a.download = viewer.dataset.title.replace(/[\\/:*?"<>|]/g, '-') + '.svg';
      a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
      return;
    }
    if (action === 'zoom-in' || action === 'zoom-out') s.scale = Math.max(.1, Math.min(4, s.scale * (action === 'zoom-in' ? 1.25 : .8)));
    resize(viewer, action === 'fit');
  }));
  // Hidden lifecycle stages have no measurable width. Render in a detached reading
  // space, then refit only visible canvases when stage navigation changes.
  const measure = document.createElement('div');
  measure.className = 'design-measure';
  measure.setAttribute('aria-hidden', 'true');
  document.body.append(measure);
  const refit = () => viewers.forEach(v => { if (v.isConnected && v.clientWidth && expanded?.viewer !== v) readable(v); });
  new MutationObserver(refit).observe(document.querySelector('.stage-board') || document.querySelector('main'), {
    attributes: true, attributeFilter: ['hidden'], subtree: true
  });
  let timer;
  window.addEventListener('resize', () => { clearTimeout(timer); timer = setTimeout(() => { refit(); if (expanded) resize(expanded.viewer, true); }, 100); });
  document.addEventListener('toggle', event => {
    if (event.target.matches?.('.design-technical') && event.target.open) {
      event.target.querySelectorAll('.design-viewer').forEach(readable);
    }
  }, true);
  (async () => {
    for (const [index, viewer] of viewers.entries()) {
      const source = viewer.querySelector('[data-design-source]').textContent;
      const canvas = viewer.querySelector('.design-figure');
      try {
        // Diagram-level configuration cannot override the board's theme or safety.
        if (/%%\s*\{|^\s*---/m.test(source)) throw Error('请在设计合同中移除图内配置指令，保留图形定义。');
        const {svg} = await mermaid.render(`sdd-diagram-${index}`, source, measure);
        canvas.innerHTML = svg;
        const element = canvas.querySelector('svg'), box = element.viewBox.baseVal;
        if (!(box.width > 0 && box.height > 0)) throw Error('图形没有可用的尺寸。');
        if (viewer.dataset.technical !== 'true' && /^\s*sequenceDiagram/m.test(source)) {
          const notation = {alt:'分支', loop:'循环', opt:'可选', par:'并行', critical:'临界区', break:'中止'};
          element.querySelectorAll('text.labelText').forEach(label => {
            const localized = notation[label.textContent.trim()];
            if (localized) label.textContent = localized;
          });
        }
        state.set(viewer, {width: box.width, height: box.height, scale: 1});
        element.setAttribute('role', 'img');
        element.setAttribute('aria-label', viewer.dataset.title);
        element.removeAttribute('height'); element.removeAttribute('width');
        element.style.maxWidth = 'none';
        viewer.querySelectorAll('button').forEach(button => { button.disabled = false; });
        viewer.querySelector('details').open = false;
        viewer.dataset.renderState = 'ready';
        readable(viewer);
      } catch (error) {
        canvas.textContent = '';
        const note = document.createElement('p');
        note.className = 'design-render-error'; note.setAttribute('role', 'status');
        note.textContent = '此图暂未绘出，已保留原始图源。' + String(error.message || error).split('\n')[0].slice(0, 160);
        canvas.append(note);
        viewer.dataset.renderState = 'error';
        viewer.querySelector('details').open = true;
      } finally { measure.replaceChildren(); }
    }
    measure.remove();
    document.documentElement.dataset.designsReady = 'true';
  })();
})();
