// darkmode.js

function applyDarkModeSetting() {
  const isDark = localStorage.getItem('darkMode') === 'true';
  document.body.classList.toggle('dark', isDark);
}

function createDarkModeToggle() {
  const toggle = document.createElement('button');
  toggle.textContent = '🌓 Toggle Dark Mode';
  toggle.setAttribute('aria-label', 'Toggle dark mode');

  Object.assign(toggle.style, {
    position: 'fixed',
    bottom: '20px',
    right: '20px',
    zIndex: '9999',
    padding: '10px 14px',
    borderRadius: '6px',
    border: 'none',
    cursor: 'pointer',
    backgroundColor: '#2a7de1',
    color: 'white',
    fontWeight: 'bold',
    boxShadow: '0 2px 6px rgba(0,0,0,0.2)'
  });

  toggle.addEventListener('click', () => {
    const enabled = document.body.classList.toggle('dark');
    localStorage.setItem('darkMode', enabled);
  });

  document.body.appendChild(toggle);
}

document.addEventListener('DOMContentLoaded', () => {
  applyDarkModeSetting();
  createDarkModeToggle();
});

// darkmode.js

// Expose this function globally
window.toggleDarkMode = function () {
  const isDark = document.body.classList.toggle('dark');
  localStorage.setItem('darkMode', isDark);
};

// Automatically apply dark mode on page load
document.addEventListener('DOMContentLoaded', function () {
  if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark');
  }
});
