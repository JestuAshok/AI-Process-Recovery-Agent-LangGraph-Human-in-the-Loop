import { store } from '../store.js';

function formatErrorTitle(errorCode, failureType) {
  const map = {
    'OUT_OF_STOCK': 'Bangalore Hub Stock Depletion (Out of Stock)',
    'ERR_INVENTORY_DEPLETED': 'Bangalore Hub Stock Depletion (Out of Stock)',
    'PAYMENT_TIMEOUT': 'UPI / Razorpay Payment Gateway Timeout (4000ms)',
    'ERR_PAYMENT_GATEWAY_TIMEOUT': 'UPI / Razorpay Payment Gateway Timeout (4000ms)',
    'INVENTORY_SERVICE_DOWN': 'Mumbai Warehouse Microservice Down (503 Error)',
    'ERR_INVENTORY_503': 'Mumbai Warehouse Microservice Down (503 Error)',
    'DELIVERY_FAILED': 'Delhivery Courier Dispatch Hub Offline',
    'ERR_LOGISTICS_CARRIER_OFFLINE': 'Delhivery Courier Dispatch Hub Offline',
    'HIGH_VALUE_REFUND': 'High-Value Order Security Review (₹2,50,000+ Threshold)',
    'POLICY_COMPLIANCE_REQUIRED': 'High-Value Order Security Review (₹2,50,000+ Threshold)',
    'CARD_FRAUD_FAILED': 'Razorpay High-Risk Fraud Alert (Declined)',
    'ERR_PAYMENT_FRAUD_FLAG': 'Razorpay High-Risk Fraud Alert (Declined)'
  };
  if (map[errorCode]) return map[errorCode];
  if (map[failureType]) return map[failureType];
  return errorCode ? errorCode.replace(/_/g, ' ') : 'System Failure Intercepted';
}

function getOrderName(wfid, workflows) {
  const wf = workflows.find(w => w.workflow_id === wfid);
  if (!wf) return wfid;
  let meta = {};
  if (wf.metadata_json) {
    try { meta = typeof wf.metadata_json === 'string' ? JSON.parse(wf.metadata_json) : wf.metadata_json; } catch(e){}
  }
  return meta.order_name ? `${meta.order_name} (${wfid})` : wfid;
}

export function renderFailuresPage(container) {
  const state = store.getState();
  const failures = state.failures || [];
  const recoveryActions = state.recoveryActions || [];
  const workflows = state.workflows || [];

  container.innerHTML = `
    <div class="card-3d" style="margin-bottom: 20px;">
      <div class="card-head">
        <div class="card-title"><span>⚠️</span> Incident & Error Logs</div>
        <button class="btn btn-subtle btn-sm" onclick="window.app.refreshAllData()"><span>🔄</span> Refresh Logs</button>
      </div>

      <div class="grid-2">
        <!-- Intercepted Incidents -->
        <div>
          <div style="font-weight: 800; font-size: 13.5px; color: var(--text-main); margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">
            <span>Intercepted Incident Reports (${failures.length})</span>
            <span style="font-size: 11px; color: var(--text-muted); font-weight: 600;">Real-time Telemetry</span>
          </div>

          <div style="display: flex; flex-direction: column; gap: 12px;">
            ${failures.map(fail => {
              const errTitle = formatErrorTitle(fail.error_code, fail.failure_type);
              const orderTitle = getOrderName(fail.workflow_id, workflows);
              const isDanger = fail.severity === 'CRITICAL' || fail.severity === 'HIGH';
              return `
              <div class="card-3d" style="padding: 16px; border-left: 4px solid ${isDanger ? 'var(--danger)' : 'var(--warning)'}; cursor: pointer; transition: transform 0.15s ease, box-shadow 0.15s ease;" onclick="window.app.navigateToWorkflow('${fail.workflow_id}')" title="Click to inspect this order">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 6px;">
                  <div>
                    <div style="font-size: 13.5px; font-weight: 800; color: ${isDanger ? 'var(--danger)' : 'var(--warning)'};">🚨 ${errTitle}</div>
                    <div style="font-size: 11.5px; font-weight: 700; color: var(--text-main); margin-top: 2px;">
                      Order: <span style="color: var(--primary); text-decoration: underline;">${orderTitle}</span>
                    </div>
                  </div>
                  <div style="display: flex; gap: 4px; align-items: center;">
                    <span class="pill pill-${fail.severity ? fail.severity.toLowerCase() : 'medium'}">${fail.severity || 'MEDIUM'}</span>
                    <span class="pill pill-${fail.status.toLowerCase()}">${fail.status}</span>
                  </div>
                </div>

                <div style="font-size: 11.5px; font-weight: 700; color: var(--text-muted); margin-bottom: 8px;">
                  Failed Step: <span style="color: var(--text-main); font-weight: 800;">${(fail.step_name || 'STEP').replace(/_/g, ' ')}</span> &bull; Code: <code style="color: var(--primary);">${fail.error_code}</code>
                </div>

                <div style="font-size: 12px; color: var(--text-body); background: var(--bg-subtle); padding: 10px 12px; border-radius: var(--r-sm); border-left: 3px solid var(--primary); margin-bottom: 8px;">
                  <strong style="color: var(--text-main);">Root Cause Analysis:</strong> ${fail.root_cause}
                </div>

                <div style="display: flex; justify-content: flex-end; font-size: 11.5px; font-weight: 700; color: var(--primary);">
                  <span>Inspect Order &rarr;</span>
                </div>
              </div>
            `}).join('') || '<div style="color: var(--text-muted); font-size: 12.5px; padding: 20px; text-align: center;">No active incidents recorded.</div>'}
          </div>
        </div>

        <!-- AI Self-Healing Executions -->
        <div>
          <div style="font-weight: 800; font-size: 13.5px; color: var(--text-main); margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">
            <span>AI Self-Healing Executions (${recoveryActions.length})</span>
            <span style="font-size: 11px; color: var(--primary); font-weight: 600;">Autonomous Graph Engine</span>
          </div>

          <div style="display: flex; flex-direction: column; gap: 12px;">
            ${recoveryActions.map(rec => {
              const orderTitle = getOrderName(rec.workflow_id, workflows);
              return `
              <div class="card-3d" style="padding: 16px; border-left: 4px solid var(--primary); cursor: pointer; transition: transform 0.15s ease, box-shadow 0.15s ease;" onclick="window.app.navigateToWorkflow('${rec.workflow_id}')" title="Click to inspect this order">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                  <span style="font-size: 12.5px; font-weight: 800; color: var(--primary);">🛠️ Tool: <code>${rec.tool_name}</code></span>
                  <span class="pill ${rec.status === 'VERIFIED' ? 'pill-completed' : 'pill-recovering'}">${rec.status}</span>
                </div>
                <div style="font-size: 13px; font-weight: 700; color: var(--text-main); margin-bottom: 4px;">
                  ${rec.proposed_action}
                </div>
                <div style="font-size: 11.5px; color: var(--text-muted); margin-bottom: 6px;">
                  Target Order: <strong style="color: var(--primary); text-decoration: underline;">${orderTitle}</strong>
                </div>
                ${rec.reasoning ? `
                  <div style="font-size: 11.5px; color: var(--text-body); background: var(--bg-subtle); padding: 8px 10px; border-radius: var(--r-sm); margin-bottom: 8px; border: 1px solid var(--border-subtle);">
                    <strong>Agent Reasoning:</strong> ${rec.reasoning}
                  </div>
                ` : ''}
                <div style="display: flex; justify-content: flex-end; font-size: 11.5px; font-weight: 700; color: var(--primary);">
                  <span>Inspect Order &rarr;</span>
                </div>
              </div>
            `}).join('') || '<div style="color: var(--text-muted); font-size: 12.5px; padding: 20px; text-align: center;">No self-healing actions recorded.</div>'}
          </div>
        </div>
      </div>
    </div>
  `;
}
