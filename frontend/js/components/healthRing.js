/**
 * Cybernetic Holographic SVG Health Ring
 */

export function renderHealthRing(containerId, successRate = 98.5, label = 'Heal Rate') {
  const container = document.getElementById(containerId);
  if (!container) return;

  const radius = 46;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (successRate / 100) * circumference;

  container.innerHTML = `
    <div style="display: flex; align-items: center; justify-content: center; position: relative;">
      <svg width="118" height="118" viewBox="0 0 118 118" style="transform: rotate(-90deg); filter: drop-shadow(0 0 10px var(--success-glow));">
        <circle cx="59" cy="59" r="${radius}" stroke="var(--ring-track)" stroke-width="9" fill="transparent" />
        <circle
          cx="59" cy="59" r="${radius}"
          stroke="url(#ringGrad)" stroke-width="9" fill="transparent"
          stroke-dasharray="${circumference}"
          stroke-dashoffset="${strokeDashoffset}"
          stroke-linecap="round"
          style="transition: stroke-dashoffset 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);"
        />
        <defs>
          <linearGradient id="ringGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#34d399" />
            <stop offset="100%" stop-color="#10b981" />
          </linearGradient>
        </defs>
      </svg>
      <div style="position: absolute; text-align: center;">
        <div style="font-size: 20px; font-weight: 800; color: var(--text-main); line-height: 1; font-family: var(--font-mono);">${successRate}%</div>
        <div style="font-size: 9.5px; font-weight: 800; text-transform: uppercase; color: var(--text-muted); margin-top: 3px; letter-spacing: 0.5px;">${label}</div>
      </div>
    </div>
  `;
}
