// Show and label the relevant controls in each lesson content block.
(() => {
  const selector = 'select[data-block-fields]';
  const formSelector = '.inline-related';
  const editors = new WeakMap();

  function getEditor(select) {
    if (editors.has(select)) return editors.get(select);
    const form = select.closest(formSelector);
    const types = JSON.parse(select.dataset.blockFields);
    const names = new Set(Object.values(types).flatMap(Object.keys));
    const fields = [...names].map(name => {
      const row = form.querySelector(`.field-${name}`);
      if (!row) return null;
      const control = row.querySelector(`[name$="-${name}"]`);
      const label = row.querySelector('label');
      const help = row.querySelector('.help > div');
      return {
        name, row, label, help,
        defaultLabel: control?.dataset.defaultLabel
          ? `${control.dataset.defaultLabel}:`
          : label?.textContent,
        defaultHelp: control?.dataset.defaultHelp ?? help?.textContent,
      };
    }).filter(Boolean);

    const editor = {types, fields};
    editors.set(select, editor);
    return editor;
  }

  function apply(select) {
    const {types, fields} = getEditor(select);
    const visible = types[select.value];
    for (const field of fields) {
      const labels = visible?.[field.name];
      field.row.style.display = visible && !labels && !field.row.querySelector('.errorlist') ? 'none' : '';
      if (field.label) field.label.textContent = labels?.length ? `${labels[0]}:` : field.defaultLabel;
      if (field.help) field.help.textContent = labels?.length ? labels[1] : field.defaultHelp;
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll(selector).forEach(apply);
  });
  document.addEventListener('change', event => {
    if (event.target.matches(selector)) apply(event.target);
  });
  document.addEventListener('formset:added', event => {
    event.target.querySelectorAll(selector).forEach(apply);
  });
})();
