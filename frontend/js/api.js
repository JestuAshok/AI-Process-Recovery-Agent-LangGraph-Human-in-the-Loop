/**
 * API Client for AI Business Process Recovery Agent
 */

const API_BASE = '';

export const api = {
  // Workflows
  async getWorkflows(status = null, search = null) {
    let url = `${API_BASE}/api/workflows?limit=100`;
    if (status) url += `&status=${encodeURIComponent(status)}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to fetch workflows: ${res.statusText}`);
    return res.json();
  },

  async getWorkflowStats() {
    const res = await fetch(`${API_BASE}/api/workflows/stats`);
    if (!res.ok) throw new Error('Failed to fetch workflow stats');
    return res.json();
  },

  async getWorkflow(workflowId) {
    const res = await fetch(`${API_BASE}/api/workflows/${encodeURIComponent(workflowId)}`);
    if (!res.ok) throw new Error(`Failed to fetch workflow ${workflowId}`);
    return res.json();
  },

  async createWorkflow(payload) {
    const res = await fetch(`${API_BASE}/api/workflows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Failed to create workflow');
    return res.json();
  },

  async startWorkflow(workflowId) {
    const res = await fetch(`${API_BASE}/api/workflows/${encodeURIComponent(workflowId)}/start`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error(`Failed to start workflow ${workflowId}`);
    return res.json();
  },

  async recoverWorkflow(workflowId) {
    const res = await fetch(`${API_BASE}/api/workflows/${encodeURIComponent(workflowId)}/recover`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error(`Failed to trigger recovery for ${workflowId}`);
    return res.json();
  },

  async getWorkflowTimeline(workflowId) {
    const res = await fetch(`${API_BASE}/api/workflows/${encodeURIComponent(workflowId)}/timeline`);
    if (!res.ok) throw new Error('Failed to fetch workflow timeline');
    return res.json();
  },

  // Approvals
  async getApprovals(status = null) {
    let url = `${API_BASE}/api/approvals`;
    if (status) url += `?status=${encodeURIComponent(status)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch approvals');
    return res.json();
  },

  async approveRecovery(approvalId, approvedBy = 'Senior Operations Manager', comments = 'Approved by operator') {
    const res = await fetch(`${API_BASE}/api/approvals/${approvalId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approved_by: approvedBy, comments })
    });
    if (!res.ok) throw new Error(`Approval failed: ${res.statusText}`);
    return res.json();
  },

  async rejectRecovery(approvalId, rejectedBy = 'Senior Operations Manager', comments = 'Rejected by operator') {
    const res = await fetch(`${API_BASE}/api/approvals/${approvalId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approved_by: rejectedBy, comments })
    });
    if (!res.ok) throw new Error(`Rejection failed: ${res.statusText}`);
    return res.json();
  },

  // Failures & Recovery Actions
  async getFailures(status = null) {
    let url = `${API_BASE}/api/failures`;
    if (status) url += `?status=${encodeURIComponent(status)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch failures');
    return res.json();
  },

  async getRecoveryActions(status = null) {
    let url = `${API_BASE}/api/recovery-actions`;
    if (status) url += `?status=${encodeURIComponent(status)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch recovery actions');
    return res.json();
  },

  // Audit Logs
  async getAuditLogs(workflowId = null, actor = null, limit = 100) {
    let url = `${API_BASE}/api/audit-logs?limit=${limit}`;
    if (workflowId) url += `&workflow_id=${encodeURIComponent(workflowId)}`;
    if (actor) url += `&actor=${encodeURIComponent(actor)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch audit logs');
    return res.json();
  },

  // Services & Chaos
  async getServicesHealth() {
    const res = await fetch(`${API_BASE}/api/services/health`);
    if (!res.ok) throw new Error('Failed to fetch service health');
    return res.json();
  },

  async injectChaos(serviceName, faultType, durationSeconds = 60) {
    const res = await fetch(`${API_BASE}/api/services/chaos/inject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        service_name: serviceName,
        fault_type: faultType,
        duration_seconds: durationSeconds
      })
    });
    if (!res.ok) throw new Error('Failed to inject chaos fault');
    return res.json();
  },

  async resetChaos() {
    const res = await fetch(`${API_BASE}/api/services/chaos/reset`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to reset chaos faults');
    return res.json();
  },

  // Demo Scenarios
  async getDemoScenarios() {
    const res = await fetch(`${API_BASE}/api/demo/scenarios`);
    if (!res.ok) throw new Error('Failed to fetch demo scenarios');
    return res.json();
  },

  async runDemoScenario(scenarioId, autoApprove = false) {
    const res = await fetch(`${API_BASE}/api/demo/run-scenario`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario_id: scenarioId, auto_approve: autoApprove })
    });
    if (!res.ok) throw new Error(`Demo scenario failed to execute: ${res.statusText}`);
    return res.json();
  },

  // Settings
  async getSettings() {
    const res = await fetch(`${API_BASE}/api/settings`);
    if (!res.ok) throw new Error('Failed to fetch settings');
    return res.json();
  },

  async updateSettings(payload) {
    const res = await fetch(`${API_BASE}/api/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Failed to update settings');
    return res.json();
  },

  // Real-time SSE Stream
  initEventStream(onMessage, onError) {
    try {
      const eventSource = new EventSource(`${API_BASE}/api/events`);
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (onMessage) onMessage(data);
        } catch (e) {
          console.warn('SSE parse error', e);
        }
      };
      eventSource.onerror = (err) => {
        if (onError) onError(err);
      };
      return eventSource;
    } catch (e) {
      console.warn('SSE not supported or failed to connect:', e);
      return null;
    }
  }
};
