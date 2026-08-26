/**
 * Minimalist 3D AI Agent Orb
 */

export function renderAIOrb(containerId, currentState = 'Monitoring') {
  const container = document.getElementById(containerId);
  if (!container) return;

  const stateConfigs = {
    Monitoring: { icon: '🛡️', badge: 'pill-running', text: 'Monitoring Telemetry' },
    Analyzing:  { icon: '🧠', badge: 'pill-waiting_for_approval', text: 'Analyzing Root Cause' },
    Planning:   { icon: '⚡', badge: 'pill-running', text: 'Planning Recovery' },
    Recovering: { icon: '🔧', badge: 'pill-recovering', text: 'Executing Recovery Tool' },
    Verifying:  { icon: '✨', badge: 'pill-completed', text: 'Verifying Multi-Factor State' }
  };

  const cfg = stateConfigs[currentState] || stateConfigs.Monitoring;

  container.innerHTML = `
    <div class="ai-orb-wrap">
      <div class="ai-orb-sphere">
        <div class="ai-orb-ring"></div>
        <div class="ai-orb-ball">
          <span>${cfg.icon}</span>
        </div>
      </div>
      <div>
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 2px;">
          <span class="pill ${cfg.badge}">${currentState}</span>
          <span style="font-size: 11px; font-weight: 700; color: var(--text-light);">LANGGRAPH</span>
        </div>
        <div style="font-size: 14px; font-weight: 800; color: var(--text-main);">${cfg.text}</div>
      </div>
    </div>
  `;
}
