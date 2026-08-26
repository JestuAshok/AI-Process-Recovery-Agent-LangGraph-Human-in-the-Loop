import { store } from '../store.js';

export function renderSettingsPage(container) {
  const state = store.getState();
  const settings = state.settings || {};

  container.innerHTML = `
    <div class="card-3d" style="margin-bottom: 20px;">
      <div class="card-head">
        <div class="card-title"><span>⚙️</span> System Settings</div>
      </div>

      <div class="grid-2">
        <!-- LLM Mode -->
        <div class="card-3d">
          <div style="font-weight: 800; font-size: 13.5px; color: var(--text-main); margin-bottom: 12px;">
            🤖 AI Reasoning Engine
          </div>

          <form id="settings-llm-form" style="display: flex; flex-direction: column; gap: 12px;">
            <div>
              <label style="font-size: 11.5px; font-weight: 700; color: var(--text-muted); display: block; margin-bottom: 4px;">
                Provider:
              </label>
              <select id="set-llm-provider" style="width: 100%; padding: 9px 12px; border-radius: var(--r-sm); border: 1px solid var(--border); font-size: 12.5px; outline: none;">
                <option value="heuristic" ${settings.llm_provider === 'heuristic' ? 'selected' : ''}>Heuristic (Deterministic Structured Engine, No API Key Required)</option>
                <option value="openai" ${settings.llm_provider === 'openai' ? 'selected' : ''}>OpenAI (GPT-4o)</option>
                <option value="gemini" ${settings.llm_provider === 'gemini' ? 'selected' : ''}>Google Gemini</option>
                <option value="anthropic" ${settings.llm_provider === 'anthropic' ? 'selected' : ''}>Anthropic Claude</option>
              </select>
            </div>

            <div>
              <label style="font-size: 11.5px; font-weight: 700; color: var(--text-muted); display: block; margin-bottom: 4px;">
                API Key (Optional):
              </label>
              <input
                type="password"
                id="set-llm-key"
                placeholder="${settings.llm_api_key_status || 'Enter API Key...'}"
                style="width: 100%; padding: 9px 12px; border-radius: var(--r-sm); border: 1px solid var(--border); font-size: 12.5px; outline: none;"
              />
            </div>

            <button type="submit" class="btn btn-primary btn-sm" style="margin-top: 6px;">
              💾 Save Engine
            </button>
          </form>
        </div>

        <!-- Policies -->
        <div class="card-3d">
          <div style="font-weight: 800; font-size: 13.5px; color: var(--text-main); margin-bottom: 12px;">
            🛡️ Recovery Policies
          </div>

          <form id="settings-policy-form" style="display: flex; flex-direction: column; gap: 12px;">
            <div>
              <label style="font-size: 11.5px; font-weight: 700; color: var(--text-muted); display: block; margin-bottom: 4px;">
                Max Retries:
              </label>
              <input
                type="number"
                id="set-max-retries"
                value="${settings.max_recovery_retries || 3}"
                min="1" max="10"
                style="width: 100%; padding: 9px 12px; border-radius: var(--r-sm); border: 1px solid var(--border); font-size: 12.5px; outline: none;"
              />
            </div>

            <div style="background: var(--bg-subtle); padding: 12px; border-radius: var(--r-sm); border: 1px solid var(--border-subtle);">
              <label style="display: flex; align-items: center; gap: 10px; cursor: pointer; font-size: 12px; font-weight: 600; color: var(--text-main);">
                <input type="checkbox" id="set-require-replacements" ${settings.require_approval_for_replacements !== false ? 'checked' : ''} />
                Require Human Approval for Substitutions
              </label>
            </div>

            <div style="background: var(--bg-subtle); padding: 12px; border-radius: var(--r-sm); border: 1px solid var(--border-subtle);">
              <label style="display: flex; align-items: center; gap: 10px; cursor: pointer; font-size: 12px; font-weight: 600; color: var(--text-main);">
                <input type="checkbox" id="set-auto-recovery" ${settings.auto_recovery_enabled !== false ? 'checked' : ''} />
                Enable Autonomous Execution
              </label>
            </div>

            <button type="submit" class="btn btn-primary btn-sm" style="margin-top: 6px;">
              💾 Save Policies
            </button>
          </form>
        </div>
      </div>
    </div>
  `;

  // Submit handlers
  document.getElementById('settings-llm-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const provider = document.getElementById('set-llm-provider').value;
    const key = document.getElementById('set-llm-key').value;
    const payload = { llm_provider: provider };
    if (key.trim()) payload.llm_api_key = key.trim();

    try {
      await window.app.updateSettings(payload);
      window.app.showToast('Settings saved.');
    } catch (err) {
      window.app.showToast(`Error: ${err.message}`, 'error');
    }
  });

  document.getElementById('settings-policy-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const retries = parseInt(document.getElementById('set-max-retries').value, 10);
    const replac = document.getElementById('set-require-replacements').checked;
    const autoRec = document.getElementById('set-auto-recovery').checked;

    try {
      await window.app.updateSettings({
        max_recovery_retries: retries,
        require_approval_for_replacements: replac,
        auto_recovery_enabled: autoRec
      });
      window.app.showToast('Policies saved.');
    } catch (err) {
      window.app.showToast(`Error: ${err.message}`, 'error');
    }
  });
}
