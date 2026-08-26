import { store, formatINR } from '../store.js';

function getOrderName(wfid, workflows) {
  const wf = workflows.find(w => w.workflow_id === wfid);
  if (!wf) return wfid;
  let meta = {};
  if (wf.metadata_json) {
    try { meta = typeof wf.metadata_json === 'string' ? JSON.parse(wf.metadata_json) : wf.metadata_json; } catch(e){}
  }
  return meta.order_name ? `${meta.order_name} (${wfid})` : wfid;
}

export function renderApprovalsPage(container) {
  const state = store.getState();
  const approvals = state.approvals || [];
  const workflows = state.workflows || [];
  const pending = approvals.filter(a => a.approval_status === 'PENDING');
  const resolved = approvals.filter(a => a.approval_status !== 'PENDING');

  container.innerHTML = `
    <div class="card-3d" style="margin-bottom: 20px;">
      <div class="card-head">
        <div class="card-title"><span>🛡️</span> Human Approval Gate</div>
        <span class="pill ${pending.length > 0 ? 'pill-waiting_for_approval' : 'pill-completed'}">
          ${pending.length} Pending
        </span>
      </div>

      <!-- Pending Decisions -->
      <div style="margin-bottom: 24px;">
        <div style="font-weight: 800; font-size: 13.5px; color: var(--text-main); margin-bottom: 12px;">
          Pending Operations Approvals
        </div>

        ${pending.length > 0 ? `
          <div style="display: flex; flex-direction: column; gap: 14px;">
            ${pending.map(appr => {
              const orderName = getOrderName(appr.workflow_id, workflows);
              return `
              <div class="card-3d" style="background: var(--bg-card); border: 1.5px solid var(--warning-border); box-shadow: 0 0 20px var(--warning-glow);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px; margin-bottom: 10px;">
                  <div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <span class="pill pill-waiting_for_approval">${appr.risk_level} Risk</span>
                      <span style="font-size: 12.5px; font-weight: 800; color: var(--primary);">${orderName}</span>
                    </div>
                    <div style="font-size: 15px; font-weight: 800; color: var(--text-main); margin-top: 4px;">
                      ${appr.proposed_action}
                    </div>
                  </div>

                  <div style="display: flex; gap: 8px;">
                    <button class="btn btn-success btn-sm btn-approve-approval" data-apprid="${appr.id}" data-wfid="${appr.workflow_id}">
                      ✓ Authorize Upgrade
                    </button>
                    <button class="btn btn-danger btn-sm btn-reject-approval" data-apprid="${appr.id}" data-wfid="${appr.workflow_id}">
                      ✗ Reject
                    </button>
                  </div>
                </div>

                <div style="background: var(--bg-subtle); padding: 10px 14px; border-radius: var(--r-sm); font-size: 12px; color: var(--text-body); border-left: 3px solid var(--warning);">
                  <strong style="color: var(--text-main);">Impact Analysis:</strong> ${appr.impact_summary || appr.reasoning}
                </div>
              </div>
            `}).join('')}
          </div>
        ` : `
          <div style="background: var(--bg-subtle); padding: 24px; text-align: center; border-radius: var(--r-md); color: var(--text-muted); font-size: 13px; border: 1px dashed var(--border);">
            ✨ No pending approvals. Autonomous AI agent is executing authorized workflows.
          </div>
        `}
      </div>

      <!-- Resolved History -->
      <div>
        <div style="font-weight: 800; font-size: 13.5px; color: var(--text-main); margin-bottom: 10px;">
          Resolved History
        </div>

        <div class="table-wrap">
          <table class="table-clean">
            <thead>
              <tr>
                <th>Workflow</th>
                <th>Action</th>
                <th>Status</th>
                <th>Authorizer</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              ${resolved.map(appr => `
                <tr>
                  <td><strong style="color: var(--primary);">${appr.workflow_id}</strong></td>
                  <td>${appr.proposed_action}</td>
                  <td>
                    <span class="pill pill-${appr.approval_status === 'APPROVED' ? 'completed' : 'failed'}">
                      ${appr.approval_status}
                    </span>
                  </td>
                  <td>${appr.approved_by || 'Operator'}</td>
                  <td style="font-family: var(--font-mono); font-size: 12px; color: var(--text-muted);">${new Date(appr.resolved_at || appr.created_at).toLocaleTimeString()}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;

  // Event bindings
  document.querySelectorAll('.btn-approve-approval').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const apprid = e.currentTarget.getAttribute('data-apprid');
      const wfid = e.currentTarget.getAttribute('data-wfid');
      try {
        await window.app.approveRecovery(apprid);
        window.app.showToast(`Workflow ${wfid} approved & completed.`);
      } catch (err) {
        window.app.showToast(`Error: ${err.message}`, 'error');
      }
    });
  });

  document.querySelectorAll('.btn-reject-approval').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const apprid = e.currentTarget.getAttribute('data-apprid');
      const wfid = e.currentTarget.getAttribute('data-wfid');
      try {
        await window.app.rejectRecovery(apprid);
        window.app.showToast(`Workflow ${wfid} rejected & cancelled.`, 'warning');
      } catch (err) {
        window.app.showToast(`Error: ${err.message}`, 'error');
      }
    });
  });
}
