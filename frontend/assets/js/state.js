export const state = {
  bonos: [],
  filtro: 'todos',
  token: localStorage.getItem('token') || '',
  pollInterval: null,
  apiBase:
    localStorage.getItem('apiBase') ||
    window.__API_BASE__ ||
    document.querySelector('meta[name="api-base"]')?.content ||
    window.location.origin,
};