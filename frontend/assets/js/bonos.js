import { state } from './state.js';
import { fetchJson } from './api.js';
import { setServerStatus, renderTable, updateStats, toast, setCreateButtonLoading } from './ui.js';
import { logout } from './auth.js';

export async function loadBonos() {
  if (!state.token) {
    return;
  }

  try {
    const response = await fetchJson('/bonos', {
      headers: { Authorization: `Bearer ${state.token}` },
    });

    if (response.status === 401) {
      logout();
      return;
    }

    if (!response.ok) throw new Error();

    state.bonos = await response.json();
    updateStats();
    renderTable();
    setServerStatus(true);
  } catch {
    setServerStatus(false);
    document.getElementById('table-body').innerHTML = `<tr><td colspan="7"><div class="empty"><span class="empty-big">!</span>Sin conexión al servidor</div></td></tr>`;
  }
}

export async function crearBono() {
  const cliente = document.getElementById('cliente').value.trim();
  const telefono = document.getElementById('telefono').value.trim();
  const usos = parseInt(document.getElementById('usos').value, 10);

  if (!cliente) { toast('Introduce el nombre del cliente', 'error'); return; }
  if (!usos || usos < 1) { toast('El número de usos debe ser mayor a 0', 'error'); return; }

  setCreateButtonLoading(true);

  try {
    const response = await fetchJson('/crear_bono', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${state.token}`,
      },
      body: JSON.stringify({ cliente, telefono, usos, base_url: state.apiBase }),
    });

    if (response.status === 401) { logout(); return; }
    if (!response.ok) throw new Error();

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `bono_${cliente.replace(/\s+/g, '_')}.pdf`;
    anchor.click();
    URL.revokeObjectURL(url);

    toast(`Bono generado · ${cliente}`);
    document.getElementById('cliente').value = '';
    document.getElementById('telefono').value = '';
    await loadBonos();
  } catch {
    toast('Error al conectar con el servidor', 'error');
  } finally {
    setCreateButtonLoading(false);
  }
}

export async function reprintPDF(id) {
  try {
    const response = await fetchJson(`/bono/${id}/pdf`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${state.token}`,
      },
      body: JSON.stringify({ base_url: state.apiBase }),
    });

    if (response.status === 401) { logout(); return; }
    if (!response.ok) throw new Error();

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `bono_${id}.pdf`;
    anchor.click();
    URL.revokeObjectURL(url);
    toast('PDF descargado');
  } catch {
    toast('Error al reimprimir', 'error');
  }
}