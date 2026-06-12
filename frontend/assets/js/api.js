import { state } from './state.js';

export function apiUrl(path) {
  return `${state.apiBase}${path}`;
}

export async function fetchJson(path, options = {}) {
  return fetch(apiUrl(path), options);
}