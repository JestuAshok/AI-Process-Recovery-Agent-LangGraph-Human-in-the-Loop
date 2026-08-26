import { store, formatINR } from '../store.js';
import { renderAIOrb } from '../components/aiOrb.js';
import { renderWorkflowMap } from '../components/workflowMap.js';
import { renderHealthRing } from '../components/healthRing.js';

export function renderDashboardPage(container) {
  const state = store.getState();
  const stats = state.workflowStats || {};
  const recentWorkflows = state.workflows.slice(0, 5);
  const services = state.servicesHealth || [];

  container.innerHTML = `
    <!-- Top Hero Bar with AI Orb & Quick Action Scenario Pills -->
    <div class="card-3d" style="margin-bottom: 20px;">
      <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px;">
        <div id="dash-orb-mount"></div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          <button class="btn btn-subtle btn-sm btn-quick-scen" data-scen="inventory_out_of_stock">
            <span>📦</span> Bangalore Out of Stock
          </button>
          <button class="btn btn-subtle btn-sm btn-quick-scen" data-scen="payment_timeout">
            <span>💳</span> UPI Payment Timeout
          </button>
          <button class="btn btn-subtle btn-sm btn-quick-scen" data-scen="inventory_service_down">
            <span>⚡</span> Mumbai 503 Outage
          </button>
          <button class="btn btn-subtle btn-sm btn-quick-scen" data-scen="delivery_failed">
            <span>🚚</span> Blue Dart Switchover
          </button>
        </div>
      </div>
    </div>

    <!-- 3D KPI Grid -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-disc kpi-disc-purple">⚡</div>
        <div>
          <div class="kpi-label">Workflows</div>
          <div class="kpi-value">${stats.total_workflows || 0}</div>
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-disc kpi-disc-green">✅</div>
        <div>
          <div class="kpi-label">Recovered</div>
          <div class="kpi-value">${stats.completed_workflows || 0}</div>
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-disc kpi-disc-coral">⚠️</div>
        <div>
          <div class="kpi-label">Failures</div>
          <div class="kpi-value">${stats.failed_workflows || 0}</div>
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-disc kpi-disc-amber">🛡️</div>
        <div>
          <div class="kpi-label">Approvals</div>
          <div class="kpi-value">${stats.pending_approvals || 0}</div>
        </div>
      </div>
    </div>

    <!-- 3D Pipeline Map -->
    <div class="card-head" style="margin-top: 4px; margin-bottom: 10px;">
      <div class="card-title"><span>🗺️</span> Active Process Pipeline</div>
      <span class="pill pill-running">LIVE TELEMETRY</span>
    </div>
    <div id="dash-pipeline-mount"></div>

    <!-- Split Grid: Live Stream & Microservices -->
    <div class="grid-2" style="margin-top: 20px;">
      <!-- Active Workflows -->
      <div class="card-3d">
        <div class="card-head">
          <div class="card-title"><span>📋</span> Recent Orders</div>
          <button class="btn btn-subtle btn-sm" onclick="window.app.navigate('workflows')">View All</button>
        </div>

        <div class="table-wrap">
          <table class="table-clean">
            <thead>
              <tr>
                <th>Order Name & ID</th>
                <th>Status</th>
                <th>Amount (INR)</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              ${recentWorkflows.map(wf => {
                let meta = {};
                if (wf.metadata_json) {
                  try { meta = typeof wf.metadata_json === 'string' ? JSON.parse(wf.metadata_json) : wf.metadata_json; } catch(e){}
                }
                const orderName = meta.order_name || wf.workflow_id;
                return `
                <tr>
                  <td>
                    <div style="font-weight: 800; color: var(--text-main); font-size: 12.5px;">${orderName}</div>
                    <div style="font-size: 10.5px; color: var(--text-muted);">${wf.workflow_id} &bull; ${wf.customer_id}</div>
                  </td>
                  <td><span class="pill pill-${wf.status.toLowerCase()}">${wf.status}</span></td>
                  <td style="font-weight: 800; color: var(--primary); font-family: var(--font-mono);">${formatINR(wf.total_amount)}</td>
                  <td>
                    <button class="btn btn-subtle btn-sm btn-dash-inspect" data-wfid="${wf.workflow_id}">
                      Inspect
                    </button>
                  </td>
                </tr>
              `}).join('')}
            </tbody>
          </table>
        </div>
      </div>

      <!-- Services Health -->
      <div class="card-3d">
        <div class="card-head">
          <div class="card-title"><span>🏥</span> Service Health</div>
          <button class="btn btn-subtle btn-sm" onclick="window.app.navigate('services')">Chaos Studio</button>
        </div>

        <div style="display: flex; align-items: center; justify-content: space-around; padding: 10px 0 16px;">
          <div id="dash-ring-mount"></div>
          <div style="display: flex; flex-direction: column; gap: 6px;">
            ${services.slice(0, 4).map(s => `
              <div style="display: flex; align-items: center; justify-content: space-between; gap: 20px; font-size: 12px;">
                <span style="font-weight: 700; color: var(--text-main);">${s.service_name}</span>
                <span class="pill pill-${s.status.toLowerCase()}">${s.response_time_ms}ms</span>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    </div>
  `;

  // Mount components
  renderAIOrb('dash-orb-mount', state.aiAgentState);
  renderWorkflowMap('dash-pipeline-mount', 'INVENTORY_CHECK', 'RECOVERING');
  renderHealthRing('dash-ring-mount', stats.recovery_success_rate || 98.5, 'Recovery');

  // Event bindings
  document.querySelectorAll('.btn-quick-scen').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const scen = e.currentTarget.getAttribute('data-scen');
      window.app.triggerDemoScenario(scen);
    });
  });

  document.querySelectorAll('.btn-dash-inspect').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const wfid = e.currentTarget.getAttribute('data-wfid');
      window.app.navigateToWorkflow(wfid);
    });
  });
}
