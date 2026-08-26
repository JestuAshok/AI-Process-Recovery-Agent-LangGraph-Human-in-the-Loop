import { store, formatINR } from '../store.js';

function getOrderTitle(wf) {
  if (!wf) return '';
  let meta = {};
  if (wf.metadata_json) {
    try {
      meta = typeof wf.metadata_json === 'string' ? JSON.parse(wf.metadata_json) : wf.metadata_json;
    } catch (e) {}
  }
  return meta.order_name || wf.workflow_id;
}

export function renderWorkflowsPage(container) {
  const state = store.getState();
  const workflows = state.workflows || [];

  container.innerHTML = `
    <div class="card-3d" style="margin-bottom: 20px;">
      <div class="card-head" style="flex-wrap: wrap; gap: 12px;">
        <div class="card-title"><span>⚡</span> Order Workflows Explorer</div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          <input
            type="text"
            id="wf-search-input"
            placeholder="Search Product / Customer / Order ID..."
            style="padding: 7px 12px; border-radius: var(--r-sm); border: 1px solid var(--border); font-size: 12.5px; outline: none; width: 260px;"
          />
          <select id="wf-status-filter" style="padding: 7px 12px; border-radius: var(--r-sm); border: 1px solid var(--border); font-size: 12.5px; outline: none;">
            <option value="">All Statuses</option>
            <option value="COMPLETED">Completed</option>
            <option value="WAITING_FOR_APPROVAL">Waiting Approval</option>
            <option value="RECOVERING">Recovering</option>
            <option value="FAILED">Failed</option>
            <option value="RUNNING">In-Flight</option>
          </select>
          <button class="btn btn-primary btn-sm" id="btn-create-new-wf">
            <span>➕</span> New Order
          </button>
        </div>
      </div>

      <!-- 3D Card Grid -->
      <div class="grid-3" id="wf-grid-container">
        ${workflows.map(wf => {
          const title = getOrderTitle(wf);
          return `
          <div class="card-3d" style="padding: 16px; cursor: pointer;" onclick="window.app.navigateToWorkflow('${wf.workflow_id}')">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 6px;">
              <span style="font-size: 13.5px; font-weight: 800; color: var(--text-main); line-height: 1.3;">${title}</span>
              <span class="pill pill-${wf.status.toLowerCase()}">${wf.status}</span>
            </div>
            <div style="font-size: 11.5px; color: var(--text-muted); margin-bottom: 10px;">
              ID: <strong style="color: var(--primary);">${wf.workflow_id}</strong> &bull; ${wf.customer_id}
            </div>
            <div style="font-size: 13px; font-weight: 800; color: var(--primary); font-family: var(--font-mono); margin-bottom: 10px;">
              ${formatINR(wf.total_amount)}
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border); padding-top: 10px; font-size: 11px;">
              <span style="color: var(--text-light);">${wf.current_step.replace(/_/g, ' ')}</span>
              <span style="color: var(--primary); font-weight: 700;">Inspect &rarr;</span>
            </div>
          </div>
        `}).join('')}
      </div>
    </div>
  `;

  // Search & Filter
  const searchInput = document.getElementById('wf-search-input');
  const statusFilter = document.getElementById('wf-status-filter');

  const handleFilter = () => {
    const q = searchInput.value.toLowerCase();
    const st = statusFilter.value;
    const filtered = (state.workflows || []).filter(wf => {
      const title = getOrderTitle(wf).toLowerCase();
      const matchQ = wf.workflow_id.toLowerCase().includes(q) || wf.customer_id.toLowerCase().includes(q) || title.includes(q);
      const matchSt = !st || wf.status === st;
      return matchQ && matchSt;
    });

    const grid = document.getElementById('wf-grid-container');
    if (grid) {
      grid.innerHTML = filtered.map(wf => {
        const title = getOrderTitle(wf);
        return `
        <div class="card-3d" style="padding: 16px; cursor: pointer;" onclick="window.app.navigateToWorkflow('${wf.workflow_id}')">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 6px;">
            <span style="font-size: 13.5px; font-weight: 800; color: var(--text-main); line-height: 1.3;">${title}</span>
            <span class="pill pill-${wf.status.toLowerCase()}">${wf.status}</span>
          </div>
          <div style="font-size: 11.5px; color: var(--text-muted); margin-bottom: 8px;">
            ID: <strong style="color: var(--primary);">${wf.workflow_id}</strong> &bull; ${wf.customer_id}
          </div>
          <div style="font-size: 13px; font-weight: 800; color: var(--primary); font-family: var(--font-mono); margin-bottom: 10px;">
            ${formatINR(wf.total_amount)}
          </div>
          <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border); padding-top: 10px; font-size: 11px;">
            <span style="color: var(--text-light);">${wf.current_step.replace(/_/g, ' ')}</span>
            <span style="color: var(--primary); font-weight: 700;">Inspect &rarr;</span>
          </div>
        </div>
      `}).join('') || '<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 30px;">No workflows found matching your criteria.</div>';
    }
  };

  searchInput?.addEventListener('input', handleFilter);
  statusFilter?.addEventListener('change', handleFilter);

  document.getElementById('btn-create-new-wf')?.addEventListener('click', async () => {
    try {
      const created = await window.app.createNewWorkflow();
      window.app.showToast(`Order ${created.workflow_id} created.`);
      window.app.navigateToWorkflow(created.workflow_id);
    } catch (e) {
      window.app.showToast(`Error: ${e.message}`, 'error');
    }
  });
}
