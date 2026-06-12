import { state } from './state.js';
import { fetchJson } from './api.js';
import { setLoginVisible, toast } from './ui.js';

export function showLogin() {
  setLoginVisible(true);
  document.getElementById('login-password').focus();
  if (state.pollInterval) {
    clearInterval(state.pollInterval);
    state.pollInterval = null;
  }
}

export function hideLogin() {
  setLoginVisible(false);
}

export async function submitLogin() {
  const password = document.getElementById('login-password').value;
  if (!password) {
    toast('Introduce la contraseña', 'error');
    return;
  }

  try {
    const response = await fetchJson('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    });

    const data = await response.json();
    if (!response.ok) {
      toast(data.error || 'Contraseña incorrecta', 'error');
      return;
    }

    state.token = data.token;
    localStorage.setItem('token', state.token);
    document.getElementById('login-password').value = '';
    hideLogin();
    toast('Acceso autorizado', 'success');
    document.dispatchEvent(new CustomEvent('auth:logged-in'));
  } catch {
    toast('Error de conexión con el servidor', 'error');
  }
}

export function logout() {
  state.token = '';
  localStorage.removeItem('token');
  if (state.pollInterval) {
    clearInterval(state.pollInterval);
    state.pollInterval = null;
  }
  showLogin();
}