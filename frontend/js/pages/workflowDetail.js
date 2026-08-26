import { store, formatINR } from '../store.js';
import { renderWorkflowTimeline } from '../components/workflowTimeline.js';
import { renderWorkflowMap } from '../components/workflowMap.js';

export function renderWorkflowDetailPage(container) {
  const state = store.getState();
  const wf = state.selectedWorkflowDetail;

  if (!wf) {
    container.innerHTML = `
      <div class="card-3d" style="text-align: center; padding: 40px;">
        <div style="font-size: 32px; margin-bottom: 8px;">📂</div>
        <div style="font-size: 15px; font-weight: 700; color: var(--text-main);">No Workflow Selected</div>
        <button class="btn btn-primary btn-sm" style="margin-top: 12px;" onclick="window.app.navigate('workflows')">Open Explorer</button>
      </div>
    `;
    return;
  }

  const approvals = wf.approvals || [];
  const pendingApproval = approvals.find(a => a.approval_status === 'PENDING');

  let meta = {};
  if (wf.metadata_json) {
    try { meta = typeof wf.metadata_json === 'string' ? JSON.parse(wf.metadata_json) : wf.metadata_json; } catch(e){}
  }
  const orderTitle = meta.order_name || wf.workflow_id;

  container.innerHTML = `
    <!-- Top Header -->
    <div class="card-3d" style="margin-bottom: 20px;">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
        <div style="display: flex; align-items: center; gap: 12px;">
          <button class="btn btn-subtle btn-sm" onclick="window.app.navigate('workflows')">&larr; Back</button>
          <div>
            <div style="font-size: 18px; font-weight: 800; color: var(--text-main); line-height: 1.2;">${orderTitle}</div>
            <div style="font-size: 11.5px; color: var(--text-muted);">ID: <strong style="color: var(--primary); font-family: var(--font-mono);">${wf.workflow_id}</strong> &bull; Customer: <strong style="color: var(--text-body);">${wf.customer_id}</strong></div>
          </div>
          <span class="pill pill-${wf.status.toLowerCase()}">${wf.status}</span>
        </div>

        <div style="display: flex; gap: 8px;">
          ${wf.status === 'PENDING' ? `
            <button class="btn btn-primary btn-sm" id="btn-start-wf" data-wfid="${wf.workflow_id}">
              ▶️ Run Flow
            </button>
          ` : ''}

          ${(wf.status === 'FAILED' || wf.status === 'WAITING_FOR_APPROVAL') ? `
            <button class="btn btn-primary btn-sm" id="btn-recover-wf" data-wfid="${wf.workflow_id}">
              ⚡ Auto-Recover
            </button>
          ` : ''}
        </div>
      </div>
    </div>

    <!-- Active Pipeline Stage -->
    <div id="detail-pipeline-mount" style="margin-bottom: 20px;"></div>

    <!-- Pending Approval Quick Bar if present -->
    ${pendingApproval ? `
      <div class="card-3d" style="margin-bottom: 20px; background: var(--warning-light); border: 1px solid var(--warning-border); box-shadow: 0 0 16px var(--warning-glow);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <div>
            <div style="font-size: 14px; font-weight: 800; color: var(--warning);">
              🛡️ Approval Required: ${pendingApproval.proposed_action || 'Product Substitution'}
            </div>
            <div style="font-size: 12px; color: var(--text-body); margin-top: 2px;">
              ${pendingApproval.impact_summary || pendingApproval.reasoning}
            </div>
          </div>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-success btn-sm btn-approve-direct" data-apprid="${pendingApproval.id}">
              ✓ Approve
            </button>
            <button class="btn btn-danger btn-sm btn-reject-direct" data-apprid="${pendingApproval.id}">
              ✗ Reject
            </button>
          </div>
        </div>
      </div>
    ` : ''}

    <!-- Timeline & Payload -->
    <div class="grid-2">
      <!-- 3D Timeline -->
      <div class="card-3d">
        <div class="card-title" style="margin-bottom: 14px;">
          <span>⏳</span> Execution Timeline
        </div>
        <div id="detail-timeline-mount"></div>
      </div>

      <!-- Structured Order & Customer Context -->
      <div class="card-3d">
        <div class="card-title" style="margin-bottom: 14px;">
          <span>📦</span> Order & Delivery Summary
        </div>
        
        <div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px;">
          <div style="display: flex; justify-content: space-between; padding: 10px 14px; background: var(--bg-subtle); border-radius: var(--r-sm); border: 1px solid var(--border-subtle);">
            <span style="color: var(--text-muted); font-size: 12px;">Order Total</span>
            <span style="font-weight: 800; color: var(--primary); font-family: var(--font-mono); font-size: 14px;">${formatINR(wf.total_amount)}</span>
          </div>

          <div style="display: flex; justify-content: space-between; padding: 10px 14px; background: var(--bg-subtle); border-radius: var(--r-sm); border: 1px solid var(--border-subtle);">
            <span style="color: var(--text-muted); font-size: 12px;">Delivery Carrier</span>
            <span style="font-weight: 700; color: var(--text-main); font-size: 12px;">🚚 ${meta.delivery_carrier || 'Blue Dart Express'}</span>
          </div>

          <div style="padding: 10px 14px; background: var(--bg-subtle); border-radius: var(--r-sm); border: 1px solid var(--border-subtle);">
            <div style="color: var(--text-muted); font-size: 11px; margin-bottom: 2px;">Delivery Address:</div>
            <div style="font-weight: 700; color: var(--text-main); font-size: 12px;">📍 ${meta.delivery_address || 'Bengaluru, Karnataka - 560103'}</div>
          </div>
        </div>

        <div class="card-title" style="margin-bottom: 10px; font-size: 13px;">
          <span>🔍</span> Telemetry State Payload
        </div>
        <div style="background: var(--bg-input); border: 1px solid var(--border); border-radius: var(--r-md); padding: 14px; font-family: var(--font-mono); font-size: 11.5px; max-height: 240px; overflow-y: auto; color: var(--text-body);">
          <pre style="white-space: pre-wrap; margin: 0;">${JSON.stringify({
            workflow_id: wf.workflow_id,
            customer_id: wf.customer_id,
            total_amount_inr: wf.total_amount,
            status: wf.status,
            current_step: wf.current_step,
            metadata: meta
          }, null, 2)}</pre>
        </div>
      </div>
    </div>
  `;

  // Render components
  renderWorkflowMap('detail-pipeline-mount', wf.current_step, wf.status);
  renderWorkflowTimeline('detail-timeline-mount', wf);

  // Button bindings
  document.getElementById('btn-start-wf')?.addEventListener('click', async (e) => {
    const id = e.currentTarget.getAttribute('data-wfid');
    await window.app.startWorkflow(id);
  });
  document.getElementById('btn-recover-wf')?.addEventListener('click', async (e) => {
    const id = e.currentTarget.getAttribute('data-wfid');
    await window.app.triggerWorkflowRecovery(id);
  });
  document.querySelectorAll('.btn-approve-direct').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const apprid = e.currentTarget.getAttribute('data-apprid');
      await window.app.approveRecovery(apprid);
    });
  });
  document.querySelectorAll('.btn-reject-direct').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const apprid = e.currentTarget.getAttribute('data-apprid');
      await window.app.rejectRecovery(apprid);
    });
  });
}
