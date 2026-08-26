import { store } from '../store.js';

/** Helper to retrieve a user‑friendly order title from workflows */
function getOrderName(wfid, workflows) {
  const wf = workflows.find(w => w.workflow_id === wfid);
  if (!wf) return wfid;
  let meta = {};
  if (wf.metadata_json) {
    try { meta = typeof wf.metadata_json === 'string' ? JSON.parse(wf.metadata_json) : wf.metadata_json; } catch (e) {}
  }
  return meta.order_name ? `${meta.order_name} (${wfid})` : wfid;
}

export function renderAuditPage(container) {
  const state = store.getState();
  const logs = state.auditLogs || [];
  const workflows = state.workflows || [];

  // newest first for timeline flow
  const sortedLogs = [...logs].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

  container.innerHTML = `
    <div class="card-3d" style="margin-bottom: 20px;">
      <div class="card-head">
        <div class="card-title"><span>📜</span> AI Audit Timeline</div>
        <button class="btn btn-subtle btn-sm" onclick="window.app.refreshAllData()"><span>🔄</span> Refresh</button>
      </div>

      <div style="display: flex; flex-direction: column; gap: 12px; padding: 4px 0;">
        ${sortedLogs.map(log => {
          let icon = '🤖', color = 'var(--primary)';
          if (log.actor === 'HUMAN_OPERATOR') { icon = '👤'; color = 'var(--warning)'; }
          else if (log.actor === 'SYSTEM') { icon = '⚙️'; color = 'var(--success)'; }
          const orderTitle = getOrderName(log.workflow_id, workflows);
          const time = new Date(log.timestamp).toLocaleTimeString();
          return `
            <div class="card-3d" style="padding: 14px 16px; border-left: 4px solid ${color}; background: var(--bg-subtle);">
              <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                  <span style="font-size: 18px;">${icon}</span>
                  <div>
                    <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
                      <span style="font-size: 11px; font-weight: 800; color: ${color};">${log.actor}</span>
                      <span style="font-size: 11px; color: var(--text-light);">&bull;</span>
                      <span style="font-size: 12.5px; font-weight: 700; color: var(--text-main);">${log.event_type}</span>
                      <span style="font-size: 11px; color: var(--text-light);">&bull;</span>
                      <span style="font-size: 11.5px; font-weight: 700; color: var(--primary);">${orderTitle}</span>
                    </div>
                    <div style="font-size: 12px; color: var(--text-body); margin-top: 3px;">
                      ${log.message}
                    </div>
                  </div>
                </div>
                <span style="font-size: 11px; color: var(--text-muted); font-family: var(--font-mono); flex-shrink: 0;">${time}</span>
              </div>
            </div>
          `;
        }).join('') || '<div style="color: var(--text-muted); text-align: center; padding: 24px;">No audit events recorded.</div>'}
      </div>
    </div>
  `;
}
