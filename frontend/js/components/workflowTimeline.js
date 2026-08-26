/**
 * Cybernetic Lifecycle & Recovery Branch Timeline
 */

export function renderWorkflowTimeline(containerId, workflowDetail) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (!workflowDetail) {
    container.innerHTML = '<div style="padding: 30px; text-align: center; color: var(--text-muted);">No workflow selected.</div>';
    return;
  }

  const steps = workflowDetail.steps || [];
  const failures = workflowDetail.failures || [];
  const recoveryActions = workflowDetail.recovery_actions || [];
  const approvals = workflowDetail.approvals || [];
  const hasFailure = failures.length > 0;

  let html = `<div style="display: flex; flex-direction: column; gap: 14px;">`;

  steps.forEach((step) => {
    const isFailed = step.status === 'FAILED';
    const isSuccess = step.status === 'SUCCESS';
    const isRecovering = step.status === 'RECOVERING';

    let icon = '⚪';
    let pillClass = 'pill-pending';
    if (isSuccess) { icon = '✅'; pillClass = 'pill-completed'; }
    else if (isFailed) { icon = '⚠️'; pillClass = 'pill-failed'; }
    else if (isRecovering) { icon = '🔄'; pillClass = 'pill-recovering'; }

    html += `
      <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--r-md); padding: 14px 16px; box-shadow: var(--shadow-sm);">
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 16px;">${icon}</span>
            <div>
              <div style="font-weight: 800; font-size: 13.5px; color: var(--text-main);">
                ${step.step_name.replace(/_/g, ' ')}
              </div>
              <div style="font-size: 11px; color: var(--text-muted);">Step #${step.step_order}</div>
            </div>
          </div>
          <span class="pill ${pillClass}">${step.status}</span>
        </div>

        ${isFailed ? `
          <div style="margin-top: 10px; background: var(--danger-light); border: 1px solid var(--danger-border); border-radius: var(--r-sm); padding: 8px 12px; font-size: 12px; color: var(--danger); font-weight: 700;">
            🚨 ${step.error_code || 'EXCEPTION'}: ${step.error_message || 'Step failure intercepted'}
          </div>
        ` : ''}
      </div>
    `;

    // AI Recovery Branch if step failed
    if (isFailed && hasFailure) {
      const fail = failures[0];
      const rec = recoveryActions[0];
      const appr = approvals[0];

      html += `
        <div style="margin-left: 20px; padding-left: 16px; border-left: 3px dashed var(--primary); display: flex; flex-direction: column; gap: 8px;">
          <!-- RCA -->
          <div style="background: var(--primary-light); border-radius: var(--r-md); padding: 12px 14px; border: 1px solid var(--primary-border); box-shadow: 0 0 14px var(--primary-glow);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
              <span style="font-size: 11.5px; font-weight: 800; color: var(--primary);">⚡ AI ROOT-CAUSE</span>
              <span class="pill pill-waiting_for_approval">${fail.severity}</span>
            </div>
            <div style="font-size: 12.5px; font-weight: 600; color: var(--text-main);">${fail.root_cause}</div>
          </div>

          ${rec ? `
            <!-- Recovery Action -->
            <div style="background: var(--bg-card); border-radius: var(--r-md); padding: 12px 14px; border: 1px solid var(--border); box-shadow: var(--shadow-sm);">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                <span style="font-size: 11.5px; font-weight: 800; color: var(--text-main);">🔧 TOOL: <code style="color: var(--primary);">${rec.tool_name}</code></span>
                <span class="pill ${rec.status === 'VERIFIED' ? 'pill-completed' : 'pill-recovering'}">${rec.status}</span>
              </div>
              <div style="font-size: 12px; color: var(--text-body);">${rec.proposed_action}</div>
            </div>
          ` : ''}

          ${appr ? `
            <!-- Approval Gate -->
            <div style="background: var(--warning-light); border-radius: var(--r-md); padding: 12px 14px; border: 1px solid var(--warning-border); box-shadow: 0 0 14px var(--warning-glow);">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                <span style="font-size: 11.5px; font-weight: 800; color: var(--warning);">🛡️ HUMAN GATE</span>
                <span class="pill ${appr.approval_status === 'APPROVED' ? 'pill-completed' : 'pill-waiting_for_approval'}">${appr.approval_status}</span>
              </div>
              <div style="font-size: 12px; color: var(--text-main);">${appr.impact_summary || appr.proposed_action}</div>
            </div>
          ` : ''}
        </div>
      `;
    }
  });

  html += `</div>`;
  container.innerHTML = html;
}
