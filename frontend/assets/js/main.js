import { state } from './state.js';
import { renderTable, clearPresetSelection, setActiveFilter, setActivePreset, setServerStatus } from './ui.js';
import { loadBonos, crearBono, reprintPDF } from './bonos.js';
import { logout, showLogin, submitLogin } from './auth.js';

function bindEvents() {
  document.getElementById('btn-crear').addEventListener('click', crearBono);
  document.getElementById('btn-login').addEventListener('click', submitLogin);
  document.getElementById('logout-btn').addEventListener('click', (event) => {
    event.preventDefault();
    logout();
  });

  document.getElementById('usos').addEventListener('input', clearPresetSelection);
  document.getElementById('search').addEventListener('input', renderTable);
  document.getElementById('login-password').addEventListener('keydown', (event) => {
    if (event.key === 'Enter') submitLogin();
  });

  document.querySelectorAll('.preset-btn').forEach((button) => {
    button.addEventListener('click', () => {
      document.getElementById('usos').value = button.dataset.usos;
      setActivePreset(button);
    });
  });

  document.querySelectorAll('.ftab').forEach((button) => {
    button.addEventListener('click', () => {
      state.filtro = button.dataset.filter;
      setActiveFilter(button);
      renderTable();
    });
  });

  document.getElementById('table-body').addEventListener('click', (event) => {
    const button = event.target.closest('[data-pdf]');
    if (!button) return;
    reprintPDF(button.dataset.pdf);
  });

  document.addEventListener('auth:logged-in', () => {
    loadBonos();
    if (!state.pollInterval) {
      state.pollInterval = setInterval(loadBonos, 15000);
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && document.activeElement.closest('.sidebar')) {
      crearBono();
    }
  });
}

function boot() {
  bindEvents();
  setServerStatus(false);

  if (state.token) {
    loadBonos();
    state.pollInterval = setInterval(loadBonos, 15000);
  } else {
    showLogin();
  }
}

boot();