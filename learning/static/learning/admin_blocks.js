// Shows only the fields that matter for each lesson block type in the admin.
(function () {
  var SHOW = {
    text: ['title', 'body'], must_know: ['title', 'body'], highlight: ['body'],
    example: ['title', 'body', 'options', 'correct_option', 'explanation'],
    code: ['title', 'body', 'code'], video: ['title', 'video_url', 'body'], summary: ['title', 'body']
  };
  var ALL = ['title', 'body', 'code', 'video_url', 'options', 'correct_option', 'explanation'];
  function apply(form) {
    var sel = form.querySelector('select[name$="-block_type"]');
    if (!sel) return;
    var show = SHOW[sel.value] || ALL;
    ALL.forEach(function (f) {
      var row = form.querySelector('.field-' + f);
      if (row) row.style.display = show.indexOf(f) > -1 ? '' : 'none';
    });
  }
  function init() {
    document.querySelectorAll('.inline-related').forEach(function (form) {
      apply(form);
      var sel = form.querySelector('select[name$="-block_type"]');
      if (sel && !sel.dataset.bound) { sel.dataset.bound = '1'; sel.addEventListener('change', function () { apply(form); }); }
    });
  }
  document.addEventListener('DOMContentLoaded', init);
  document.addEventListener('formset:added', init);
})();
