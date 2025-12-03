document.addEventListener('DOMContentLoaded', function () {
  const buttons = document.querySelectorAll('.theme-toggle');
  const STORAGE_KEY = 'bbs_theme';

  function applyTheme(dark) {
    if (dark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem(STORAGE_KEY, dark ? 'dark' : 'light');
  }

  buttons.forEach(btn => {
    btn.addEventListener('click', function () {
      applyTheme(!document.documentElement.classList.contains('dark'));
    });
  });

  if (localStorage.getItem(STORAGE_KEY) === 'dark') {
    applyTheme(true);
  } else if (localStorage.getItem(STORAGE_KEY) === 'light') {
    applyTheme(false);
  } else {
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    applyTheme(prefersDark);
  }
});
