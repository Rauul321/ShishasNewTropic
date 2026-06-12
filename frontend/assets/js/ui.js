import { state } from './state.js';

export function toast(msg, type = 'success') {
  const element = document.getElementById('toast');
  element.textContent = msg;
  element.className = `show ${type}`;
  clearTimeout(window._tt);
  window._tt = setTimeout(() => {
    element.className = '';
  }, 3000);
}

export function setActivePreset(button) {
  document.querySelectorAll('.preset-btn').forEach((item) => item.classList.remove('active'));
  button.classList.add('active');
}

export function clearPresetSelection() {
  document.querySelectorAll('.preset-btn').forEach((item) => item.classList.remove('active'));
}

export function setActiveFilter(button) {
  document.querySelectorAll('.ftab').forEach((item) => item.classList.remove('active'));
  button.classList.add('active');
}

export function setServerStatus(online) {
  const dot = document.getElementById('status-dot');
  const text = document.getElementById('status-text');
  if (online) {
    dot.classList.add('on');
    text.textContent = 'Conectado';
  } else {
    dot.classList.remove('on');
    text.textContent = 'Sin conexión';
  }
}

export function setLoginVisible(visible) {
  document.getElementById('login-overlay').classList.toggle('show', visible);
}

export function setCreateButtonLoading(loading) {
  const button = document.getElementById('btn-crear');
  const text = document.getElementById('btn-text');
  button.disabled = loading;
  text.innerHTML = loading ? '<div class="spinner"></div>' : 'Generar Bono PDF';
}

export function updateStats() {
  const activos = state.bonos.filter((bono) => bono.usos_restantes > 0).length;
  const agotados = state.bonos.filter((bono) => bono.usos_restantes === 0).length;
  const usos = state.bonos.reduce((sum, bono) => sum + bono.usos_realizados, 0);

  document.getElementById('s-total').textContent = state.bonos.length;
  document.getElementById('s-activos').textContent = activos;
  document.getElementById('s-agotados').textContent = agotados;
  document.getElementById('s-usos').textContent = usos;
}

export function renderTable() {
  const query = document.getElementById('search').value.toLowerCase();
  let data = state.bonos;

  if (state.filtro === 'activos') data = data.filter((bono) => bono.usos_restantes > 0);
  if (state.filtro === 'agotados') data = data.filter((bono) => bono.usos_restantes === 0);
  if (query) {
    data = data.filter((bono) =>
      bono.cliente.toLowerCase().includes(query) ||
      bono.id.toLowerCase().includes(query) ||
      (bono.telefono || '').includes(query)
    );
  }

  const tbody = document.getElementById('table-body');

  if (!data.length) {
    tbody.innerHTML = `<tr><td colspan="7"><div class="empty"><span class="empty-big">○</span>Sin resultados</div></td></tr>`;
    return;
  }

  tbody.innerHTML = data.map((bono) => {
    const pct = Math.round((bono.usos_restantes / bono.usos_totales) * 100);
    const low = pct <= 20 && bono.usos_restantes > 0;
    const out = bono.usos_restantes === 0;
    const pillClass = out ? 'pill-off' : low ? 'pill-low' : 'pill-on';
    const pillText = out ? 'Agotado' : low ? 'Bajo' : 'Activo';

    return `<tr>
      <td class="mono">${bono.id}</td>
      <td>
        <div class="client-name">${bono.cliente}</div>
        ${bono.telefono ? `<div class="client-phone">${bono.telefono}</div>` : ''}
      </td>
      <td>
        <div class="uses-row">
          <div class="bar"><div class="bar-inner ${low ? 'low' : ''}" style="width:${out ? 0 : pct}%"></div></div>
          <span class="uses-count" style="color:${out ? 'var(--grey2)' : 'var(--white)'}">${bono.usos_restantes}/${bono.usos_totales}</span>
        </div>
      </td>
      <td class="dim">${bono.fecha_compra}</td>
      <td><span class="pill ${pillClass}">${pillText}</span></td>
      <td><button class="btn-action" data-pdf="${bono.id}">PDF</button></td>
    </tr>`;
  }).join('');
}