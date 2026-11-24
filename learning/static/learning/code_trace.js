document.querySelectorAll('[data-code-trace]').forEach((trace) => {
  const find = (name) => trace.querySelector(`[data-trace-${name}]`);
  const copy = find('copy');
  if (navigator.clipboard) {
    copy.hidden = false;
    let resetLabel;
    copy.addEventListener('click', async () => {
      const source = [...trace.querySelectorAll('.trace-code-text')].map((line) => line.textContent).join('\n');
      try {
        await navigator.clipboard.writeText(source);
        copy.textContent = 'Copied';
      } catch {
        copy.textContent = 'Could not copy';
      }
      clearTimeout(resetLabel);
      resetLabel = setTimeout(() => { copy.textContent = 'Copy'; }, 1600);
    });
  }

  const frames = JSON.parse(find('data').firstElementChild.textContent);
  if (!frames.length) return;

  const back = find('back');
  const next = find('next');
  const play = find('play');
  const output = find('output');
  const state = find('state');
  const lines = [...trace.querySelectorAll('[data-trace-line]')];
  const finalOutput = output.textContent;
  let position = -1;
  let timer;

  function stop() {
    clearInterval(timer);
    timer = undefined;
    play.textContent = 'Play';
  }

  function render() {
    const frame = frames[position];
    back.disabled = position < 0;
    next.disabled = position >= frames.length - 1;
    find('counter').textContent = position < 0 ? 'Ready' : `Step ${position + 1} of ${frames.length}`;
    find('caption').textContent = frame?.caption || 'Step through the code to see which line runs and what it changes.';
    state.textContent = frame?.state || '';
    state.hidden = !state.textContent;
    const currentOutput = frame?.output ?? (next.disabled ? finalOutput : '');
    output.textContent = currentOutput || 'No output yet';
    output.classList.toggle('trace-empty', !currentOutput);
    lines.forEach((line) => {
      line.classList.toggle('trace-active', Number(line.dataset.traceLine) === frame?.line);
    });
  }

  back.addEventListener('click', () => {
    stop();
    position -= 1;
    render();
  });
  next.addEventListener('click', () => {
    stop();
    position += 1;
    render();
  });
  play.addEventListener('click', () => {
    if (timer !== undefined) {
      stop();
      return;
    }
    if (position >= frames.length - 1) position = -1;
    position += 1;
    render();
    if (next.disabled) return;
    play.textContent = 'Pause';
    timer = setInterval(() => {
      position += 1;
      render();
      if (next.disabled) stop();
    }, 1550);
  });

  play.parentElement.hidden = false;
  find('counter').parentElement.hidden = false;
  render();
});
