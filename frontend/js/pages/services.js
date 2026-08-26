import { store } from '../store.js';

export function renderServicesPage(container) {
  const state = store.getState();
  const services = state.servicesHealth || [];

  container.innerHTML = `
    <div class="card-3d" style="margin-bottom: 20px;">
      <div class="card-head">
        <div class="card-title"><span>🧪</span> Business Services & Chaos Studio</div>
        <button class="btn btn-danger btn-sm" id="btn-reset-chaos">
          <span>🧹</span> Reset Faults
        </button>
      </div>

      <div class="grid-3" style="margin-bottom: 20px;">
        ${services.map(s => {
          const isFault = !!s.active_chaos_fault;
          return `
            <div class="card-3d" style="padding: 18px; background: var(--bg-card); border: 1.5px solid ${isFault ? 'var(--danger)' : 'var(--border)'}; ${isFault ? 'box-shadow: 0 0 16px var(--danger-glow);' : ''}">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 14px; font-weight: 800; color: var(--text-main);">${s.service_name}</span>
                <span class="pill pill-${s.status.toLowerCase()}">${s.status}</span>
              </div>

              <div style="display: flex; gap: 12px; margin-bottom: 12px; font-size: 11.5px; color: var(--text-muted);">
                <span>Latency: <strong style="color: var(--text-main); font-family: var(--font-mono);">${s.response_time_ms}ms</strong></span>
                <span>Reqs: <strong style="color: var(--text-main); font-family: var(--font-mono);">${s.request_count}</strong></span>
                <span>Fails: <strong style="color: ${s.failure_count > 0 ? 'var(--danger)' : 'var(--text-main)'}; font-family: var(--font-mono);">${s.failure_count}</strong></span>
              </div>

              ${isFault ? `
                <div style="background: var(--danger-light); padding: 6px 10px; border-radius: var(--r-sm); font-size: 11px; color: var(--danger); font-weight: 700; margin-bottom: 10px; border: 1px solid var(--danger-border);">
                  ⚠️ Fault Active: ${s.active_chaos_fault}
                </div>
              ` : ''}

              <!-- Chaos Trigger Pills -->
              <div style="border-top: 1px solid var(--border); padding-top: 10px; display: flex; flex-wrap: wrap; gap: 6px;">
                ${getChaosPills(s.service_name)}
              </div>
            </div>
          `;
        }).join('')}
      </div>
    </div>
  `;

  function getChaosPills(svcName) {
    const name = svcName.toLowerCase();
    if (name.includes('payment')) {
      return `
        <button class="btn btn-subtle btn-sm btn-inject-chaos" data-svc="payment" data-fault="TIMEOUT">Timeout</button>
        <button class="btn btn-subtle btn-sm btn-inject-chaos" data-svc="payment" data-fault="DECLINED">Declined</button>
      `;
    } else if (name.includes('inventory')) {
      return `
        <button class="btn btn-subtle btn-sm btn-inject-chaos" data-svc="inventory" data-fault="out_of_stock">Out of Stock</button>
        <button class="btn btn-subtle btn-sm btn-inject-chaos" data-svc="inventory" data-fault="service_down">503 Down</button>
      `;
    } else if (name.includes('delivery')) {
      return `
        <button class="btn btn-subtle btn-sm btn-inject-chaos" data-svc="delivery" data-fault="carrier_down">Carrier Fail</button>
      `;
    }
    return `<button class="btn btn-subtle btn-sm btn-inject-chaos" data-svc="order" data-fault="high_latency">Latency Spike</button>`;
  }

  // Bindings
  document.querySelectorAll('.btn-inject-chaos').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const svc = e.currentTarget.getAttribute('data-svc');
      const fault = e.currentTarget.getAttribute('data-fault');
      try {
        await window.app.injectChaos(svc, fault);
        window.app.showToast(`Injected ${fault} on ${svc}.`);
      } catch (err) {
        window.app.showToast(`Error: ${err.message}`, 'error');
      }
    });
  });

  document.getElementById('btn-reset-chaos')?.addEventListener('click', async () => {
    try {
      await window.app.resetChaos();
      window.app.showToast('All chaos faults cleared.');
    } catch (err) {
      window.app.showToast(`Error: ${err.message}`, 'error');
    }
  });
}
