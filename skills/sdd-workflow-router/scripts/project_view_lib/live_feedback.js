/* Optional loopback service: explicit user feedback, separate from engineering approval. */
(() => {
  const token = document.querySelector('meta[name="sdd-feedback-token"]')?.content;
  if (!token) return; // A static/offline snapshot keeps its conversation route.
  async function api(method, payload) {
    const response = await fetch('/api/feedback', {method, credentials: 'omit', cache: 'no-store',
      headers: {'X-SDD-Token': token, ...(payload ? {'Content-Type': 'application/json'} : {})},
      body: payload ? JSON.stringify(payload) : undefined, signal: AbortSignal.timeout(12000)});
    const result = await response.json();
    if (!response.ok) throw Error(result.error || '提交未完成，请保留内容后重试。');
    return result;
  }
  const forms = [...document.querySelectorAll('.decision-form')]
    .filter(form => JSON.parse(form.dataset.decisionRequest).kind === 'feedback');
  if (!forms.length) return;
  // One status read for the page; drafts on other cards must not overwrite persisted revisions.
  const state = api('GET');
  forms.forEach(async form => {
    const request = JSON.parse(form.dataset.decisionRequest);
    const card = form.closest('.decision-card');
    const main = form.querySelector('[data-decision-action="copy"]');
    const status = form.querySelector('.decision-status');
    const hint = form.querySelector('.decision-actions > span');
    const output = form.querySelector('.decision-output');
    const fields = form.querySelector('.decision-fields');
    const originalDisabled = fields.disabled;
    const receipt = document.createElement('section');
    receipt.className = 'live-feedback-receipt'; receipt.hidden = true;
    receipt.setAttribute('aria-live', 'polite');
    form.before(receipt);
    let revision = 0, pending = null, busy = false, submitted = null;
    main.dataset.decisionAction = 'submit'; main.textContent = '提交反馈'; main.disabled = true;
    hint.textContent = '正在连接本机记录服务…';
    form.querySelector('.decision-help').textContent = '提交后保存在本机，刷新后仍可查看。也可以直接在对话里反馈。';
    function showSaved(record, current = true) {
      submitted = record; revision = record.revision;
      receipt.replaceChildren();
      const heading = document.createElement('strong'); heading.textContent = record.status;
      const answer = document.createElement('p'); answer.textContent = record.answer_label;
      const note = document.createElement('p'); note.className = 'live-feedback-note'; note.textContent = record.note;
      const time = document.createElement('small');
      time.textContent = '提交于 ' + new Date(record.submitted_at).toLocaleString('zh-CN', {hour12:false});
      const context = document.createElement('small');
      context.textContent = current ? (record.effect === 'REQUEST_CHANGES'
        ? '修改意见已保存到本机，等待后续处理。' : '已保存到本机，可随时修改反馈。')
        : '这是此前保存的反馈；图示来源已变化，请先重新核对。';
      const edit = document.createElement('button'); edit.type = 'button'; edit.textContent = '修改反馈'; edit.disabled = !current;
      edit.addEventListener('click', () => {
        receipt.hidden = true; form.hidden = false;
        form.querySelectorAll('input[type="radio"]').forEach(radio => radio.checked = radio.value === submitted.answer);
        const noteField = form.querySelector('[data-decision-note]'); noteField.value = submitted.note;
        noteField.dispatchEvent(new Event('input', {bubbles:true}));
        if (submitted.note) form.querySelector('.decision-note-wrap').open = true;
        main.textContent = '更新反馈'; hint.textContent = '更新后保留之前的提交记录。';
        main.focus();
      });
      receipt.append(heading, answer);
      if (record.note) receipt.append(note);
      receipt.append(time, context, edit);
      receipt.hidden = false; form.hidden = true;
      const badge = card.querySelector('.decision-heading .badge');
      badge.textContent = current ? record.status : '反馈来源待核对';
      badge.dataset.feedback = record.effect;
      const summary = card.closest('.feedback-area')?.querySelector(':scope > summary > span:last-child');
      if (summary) summary.textContent = current ? record.status + ' · 查看记录 →' : '反馈来源待核对 →';
    }
    form.addEventListener('input', () => { if (!busy) pending = null; });
    main.addEventListener('click', async () => {
      if (busy || main.disabled) return;
      // Existing draft logic maintains required notes on input; reportValidity also covers empty selection.
      if (!form.reportValidity()) return;
      const answer = form.querySelector('input:checked')?.value;
      if (!answer) { status.textContent = '请先选择你的反馈。'; return; }
      const note = form.querySelector('[data-decision-note]').value.trim();
      if (!pending) pending = {schema: request.schema, project_id: request.project_id,
        snapshot_sha256: request.snapshot_sha256, item_id: request.item_id, decision_id: request.decision_id,
        answer, note, origin: 'local_board_submit', request_id: crypto.randomUUID(), expected_revision: revision};
      busy = true; fields.disabled = true; output.hidden = true;
      status.textContent = '正在保存反馈…'; main.textContent = '正在保存…';
      try {
        const result = await api('POST', pending);
        if (!result.saved || result.record.request_id !== pending.request_id) throw Error('尚未确认保存，请重试。');
        pending = null; showSaved(result.record);
        status.textContent = '';
      } catch (error) {
        status.textContent = (error.name === 'TimeoutError' || error instanceof TypeError)
          ? '连接中断，尚未确认保存。内容已保留，可重试；同一次提交不会重复记录。' : error.message;
      } finally {
        busy = false; fields.disabled = originalDisabled;
        main.textContent = revision ? '更新反馈' : '提交反馈';
      }
    });
    try {
      const result = await state;
      if (result.snapshot_sha256 !== request.snapshot_sha256) throw Error('看板版本已变化，请刷新后再提交。');
      const current = Boolean(result.current[request.item_id]) && !originalDisabled;
      main.disabled = !current;
      hint.textContent = current ? '直接保存到本机，无需复制到对话。' : '图示来源已变化，请先重新核对。';
      if (result.records[request.item_id]) showSaved(result.records[request.item_id], current);
    } catch (error) {
      hint.textContent = '本机记录服务连接失败，请刷新后重试。'; status.textContent = error.message;
    }
  });
})();
