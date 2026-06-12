export const state = {
  bonos: [],
  filtro: 'todos',
  token: localStorage.getItem('token') || '',
  pollInterval: null,
  apiBase: window.location.origin,
};