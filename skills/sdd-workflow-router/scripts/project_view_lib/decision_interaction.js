/* Compose an explicit answer for the project conversation; drafts never approve. */
(() => {
  async function copy(text, textarea, status) {
    try {
      if (!navigator.clipboard?.writeText) throw Error('clipboard unavailable');
      await navigator.clipboard.writeText(text);
      status.textContent = '已复制。回到对话粘贴并发送，我收到后再处理。';
    } catch {
      textarea.focus(); textarea.select();
      const copied = document.execCommand('copy');
      status.textContent = copied ? '已复制。回到对话粘贴并发送，我收到后再处理。'
        : '复制未成功，已选中下面的话，请手动复制到对话。';
    }
  }
  document.querySelectorAll('[data-copy-clarification]').forEach(button => {
    button.addEventListener('click', () => {
      const card = button.closest('.decision-card'), textarea = card.querySelector('textarea');
      copy(textarea.value, textarea, card.querySelector('.decision-status'));
    });
  });
  document.querySelectorAll('.decision-form').forEach(form => {
    const request = JSON.parse(form.dataset.decisionRequest);
    const status = form.querySelector('.decision-status');
    const note = form.querySelector('[data-decision-note]');
    const output = form.querySelector('.decision-output');
    const textarea = output.querySelector('textarea');
    form.addEventListener('submit', e => e.preventDefault());
    const requirements = () => {
      const answer = form.querySelector('input:checked')?.value;
      const option = request.options.find(option => option.id === answer);
      note.required = Boolean(option?.requires_note);
      const wrap = form.querySelector('.decision-note-wrap');
      if (note.required) wrap.open = true;
      wrap.querySelector('summary').textContent = note.required ? '想改哪里？' : '补充一句（可选）';
      note.setCustomValidity(note.required && !note.value.trim() ? '请说明需要修改的内容或理由。' : '');
    };
    form.addEventListener('input', () => {
      requirements();
      status.textContent = '';
      output.hidden = true;
    });
    form.querySelectorAll('[data-decision-action]').forEach(button => button.addEventListener('click', async () => {
      if (button.dataset.decisionAction === 'submit') return; // Local service owns direct feedback submission.
      requirements();
      if (!form.reportValidity()) return;
      const answer = request.kind === 'input' ? form.querySelector('[data-decision-answer]').value.trim()
        : form.querySelector('input:checked')?.value;
      if (!answer) { status.textContent = '请先填写答复。'; return; }
      const response = {schema: request.schema, project_id: request.project_id,
        snapshot_sha256: request.snapshot_sha256, item_id: request.item_id, decision_id: request.decision_id,
        answer, note: note.value.trim(), origin: 'board_draft'};
      const option = request.options.find(option => option.id === answer);
      const text = `关于「${request.subject}」，我的${request.kind === 'feedback' ? '反馈' : '答复'}是：${option?.label || answer}。` +
        (response.note ? `\n${response.note}` : '') +
        `\n\n〔${request.decision_id} · 版本 ${request.snapshot_sha256.slice(0, 12)}〕`;
      output.hidden = false; output.open = true;
      textarea.value = text;
      status.textContent = '下面是要发送的话，复制到对话后发送即可。';
      if (button.dataset.decisionAction === 'copy') await copy(text, textarea, status);
      if (button.dataset.decisionAction === 'download') {
        const url = URL.createObjectURL(new Blob([JSON.stringify(response, null, 2) + '\n'], {type:'application/json'}));
        const link = document.createElement('a');
        link.href = url; link.download = `decision-${request.decision_id.replace(/[\\/:*?"<>|]/g, '-')}.json`;
        link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
        status.textContent = '已导出答复文件，可在项目对话中附上并说明处理意图。';
      }
    }));
  });
})();
