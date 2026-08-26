/**
 * Main Frontend Application Orchestrator
 */

import { api } from './api.js';
import { store } from './store.js';
import { renderDashboardPage } from './pages/dashboard.js';
import { renderWorkflowsPage } from './pages/workflows.js';
import { renderWorkflowDetailPage } from './pages/workflowDetail.js';
import { renderFailuresPage } from './pages/failures.js';
import { renderApprovalsPage } from './pages/approvals.js';
import { renderAuditPage } from './pages/audit.js';
import { renderServicesPage } from './pages/services.js';
import { renderSettingsPage } from './pages/settings.js';

class App {
  constructor() {
    this.container = document.getElementById('view-container');
    this.init();
  }

  async init() {
    this.setupNavigation();
    this.setupDemoBar();
    await this.refreshAllData();

    // Initialize Real-time Server-Sent Events (SSE)
    api.initEventStream(
      (event) => {
        console.log('[SSE Event]', event);
        this.refreshAllData(false);
      },
      (err) => {
        console.warn('SSE stream disconnected, fallback polling active.');
      }
    );

    // Periodic telemetry poll every 10s as robust fallback
    setInterval(() => this.refreshAllData(false), 10000);

    // Initial render
    this.render();

    // Subscribe store to render
    store.subscribe(() => {
      this.render();
      this.updateBadges();
    });
  }

  setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const tab = link.getAttribute('data-tab');
        this.navigate(tab);
      });
    });

    window.addEventListener('hashchange', () => {
      const hash = window.location.hash.replace('#', '');
      if (hash.startsWith('workflow/')) {
        const wfid = hash.split('/')[1];
        this.navigateToWorkflow(wfid);
      } else if (hash) {
        this.navigate(hash);
      }
    });

    // Handle initial hash if present
    const hash = window.location.hash.replace('#', '');
    if (hash) {
      if (hash.startsWith('workflow/')) {
        this.navigateToWorkflow(hash.split('/')[1]);
      } else {
        store.setState({ activeTab: hash });
      }
    }
  }

  setupDemoBar() {
    const demoSelect = document.getElementById('demo-scenario-select');
    const runDemoBtn = document.getElementById('btn-run-demo-topbar');

    runDemoBtn?.addEventListener('click', async () => {
      const selected = demoSelect ? demoSelect.value : 'inventory_out_of_stock';
      await this.triggerDemoScenario(selected);
    });
  }

  navigate(tab) {
    window.location.hash = tab;
    store.setState({ activeTab: tab });
  }

  async navigateToWorkflow(workflowId) {
    try {
      store.setState({ isLoading: true });
      const detail = await api.getWorkflow(workflowId);
      store.setState({
        selectedWorkflowId: workflowId,
        selectedWorkflowDetail: detail,
        activeTab: 'workflow-detail',
        isLoading: false
      });
      window.location.hash = `workflow/${workflowId}`;
    } catch (e) {
      store.setState({ isLoading: false });
      this.showToast(`Failed to load workflow ${workflowId}: ${e.message}`, 'error');
    }
  }

  async refreshAllData(showSpinner = true) {
    try {
      if (showSpinner) store.setState({ isLoading: true });

      const [workflows, stats, approvals, failures, recActions, logs, services, settings, demoScenarios] = await Promise.all([
        api.getWorkflows(),
        api.getWorkflowStats(),
        api.getApprovals(),
        api.getFailures(),
        api.getRecoveryActions(),
        api.getAuditLogs(null, null, 80),
        api.getServicesHealth(),
        api.getSettings(),
        api.getDemoScenarios()
      ]);

      // If viewing detail, refresh it as well
      let currentDetail = store.getState().selectedWorkflowDetail;
      if (store.getState().selectedWorkflowId) {
        try {
          currentDetail = await api.getWorkflow(store.getState().selectedWorkflowId);
        } catch (e) {}
      }

      store.setState({
        workflows,
        workflowStats: stats,
        approvals,
        failures,
        recoveryActions: recActions,
        auditLogs: logs,
        servicesHealth: services,
        settings,
        demoScenarios,
        selectedWorkflowDetail: currentDetail,
        isLoading: false
      });
    } catch (e) {
      store.setState({ isLoading: false });
      console.error('Data refresh error:', e);
    }
  }

  updateBadges() {
    const state = store.getState();
    const pendingApprovalsCount = state.approvals.filter(a => a.approval_status === 'PENDING').length;
    const failuresCount = state.failures.filter(f => f.status === 'ACTIVE').length;

    const apprBadge = document.getElementById('badge-pending-approvals');
    if (apprBadge) {
      apprBadge.textContent = pendingApprovalsCount;
      apprBadge.style.display = pendingApprovalsCount > 0 ? 'inline-block' : 'none';
    }

    const failBadge = document.getElementById('badge-active-failures');
    if (failBadge) {
      failBadge.textContent = failuresCount;
      failBadge.style.display = failuresCount > 0 ? 'inline-block' : 'none';
    }

    // Update nav link active state
    document.querySelectorAll('.nav-link').forEach(link => {
      const tab = link.getAttribute('data-tab');
      if (tab === state.activeTab || (state.activeTab === 'workflow-detail' && tab === 'workflows')) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });

    // Update Topbar Title
    const titleMap = {
      dashboard: 'Command Center',
      workflows: 'Order Workflows',
      'workflow-detail': 'Order Workflow Inspector',
      failures: 'Incident & Error Logs',
      approvals: 'Human Approval Gate',
      audit: 'AI Audit Timeline',
      services: 'Services & Chaos Studio',
      settings: 'AI Engine Settings'
    };
    const titleEl = document.getElementById('topbar-page-title');
    if (titleEl) {
      titleEl.textContent = titleMap[state.activeTab] || 'Command Center';
    }

    // Update Sidebar AI Chip
    const chip = document.getElementById('sidebar-ai-chip');
    if (chip) {
      chip.textContent = `Agent: ${state.aiAgentState}`;
    }
  }

  render() {
    if (!this.container) return;
    const state = store.getState();

    switch (state.activeTab) {
      case 'dashboard':
        renderDashboardPage(this.container);
        break;
      case 'workflows':
        renderWorkflowsPage(this.container);
        break;
      case 'workflow-detail':
        renderWorkflowDetailPage(this.container);
        break;
      case 'failures':
        renderFailuresPage(this.container);
        break;
      case 'approvals':
        renderApprovalsPage(this.container);
        break;
      case 'audit':
        renderAuditPage(this.container);
        break;
      case 'services':
        renderServicesPage(this.container);
        break;
      case 'settings':
        renderSettingsPage(this.container);
        break;
      default:
        renderDashboardPage(this.container);
    }
  }

  // User Actions
  async triggerDemoScenario(scenarioId) {
    try {
      this.showToast(`Starting scenario '${scenarioId}'...`);
      store.setAIAgentState('Analyzing');

      const wf = await api.runDemoScenario(scenarioId, false);
      this.showToast(`Scenario executed. Workflow ${wf.workflow_id} created.`);

      // Update AI Agent State
      if (wf.status === 'WAITING_FOR_APPROVAL') {
        store.setAIAgentState('Planning');
      } else if (wf.status === 'COMPLETED') {
        store.setAIAgentState('Verifying');
      } else {
        store.setAIAgentState('Monitoring');
      }

      await this.refreshAllData();
      await this.navigateToWorkflow(wf.workflow_id);
    } catch (e) {
      this.showToast(`Demo scenario error: ${e.message}`, 'error');
      store.setAIAgentState('Monitoring');
    }
  }

  async startWorkflow(workflowId) {
    try {
      store.setAIAgentState('Monitoring');
      const wf = await api.startWorkflow(workflowId);
      this.showToast(`Workflow ${workflowId} advanced to status: ${wf.status}`);
      await this.refreshAllData();
      await this.navigateToWorkflow(workflowId);
    } catch (e) {
      this.showToast(`Execution error: ${e.message}`, 'error');
    }
  }

  async triggerWorkflowRecovery(workflowId) {
    try {
      store.setAIAgentState('Recovering');
      const wf = await api.recoverWorkflow(workflowId);
      this.showToast(`Recovery executed on ${workflowId}: ${wf.status}`);
      await this.refreshAllData();
      await this.navigateToWorkflow(workflowId);
    } catch (e) {
      this.showToast(`Recovery error: ${e.message}`, 'error');
    }
  }

  async approveRecovery(approvalId) {
    try {
      store.setAIAgentState('Recovering');
      const wf = await api.approveRecovery(approvalId);
      this.showToast(`Approval granted! Workflow ${wf.workflow_id} completed.`);
      store.setAIAgentState('Verifying');
      setTimeout(() => store.setAIAgentState('Monitoring'), 3000);
      await this.refreshAllData();
      if (store.getState().activeTab === 'workflow-detail') {
        await this.navigateToWorkflow(wf.workflow_id);
      }
    } catch (e) {
      this.showToast(`Approval error: ${e.message}`, 'error');
      store.setAIAgentState('Monitoring');
    }
  }

  async rejectRecovery(approvalId) {
    try {
      const wf = await api.rejectRecovery(approvalId);
      this.showToast(`Recovery rejected. Workflow ${wf.workflow_id} cancelled.`, 'warning');
      await this.refreshAllData();
      if (store.getState().activeTab === 'workflow-detail') {
        await this.navigateToWorkflow(wf.workflow_id);
      }
    } catch (e) {
      this.showToast(`Rejection error: ${e.message}`, 'error');
    }
  }

  async createNewWorkflow(payload = {}) {
    const defaultPayload = {
      customer_id: 'CUST-NEW-' + Math.floor(1000 + Math.random() * 9000),
      product_id: 'PROD-LAPTOP-X1',
      quantity: 1,
      unit_price: 1299.99,
      delivery_address: '100 Silicon Way, Palo Alto, CA',
      delivery_carrier: 'FedEx Express',
      force_failure_scenario: 'OUT_OF_STOCK'
    };
    const created = await api.createWorkflow({ ...defaultPayload, ...payload });
    await this.refreshAllData();
    return created;
  }

  async injectChaos(service, fault) {
    await api.injectChaos(service, fault);
    await this.refreshAllData();
  }

  async resetChaos() {
    await api.resetChaos();
    await this.refreshAllData();
  }

  async updateSettings(payload) {
    await api.updateSettings(payload);
    await this.refreshAllData();
  }

  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast-msg';
    if (type === 'error') {
      toast.style.borderLeftColor = 'var(--danger)';
    } else if (type === 'warning') {
      toast.style.borderLeftColor = 'var(--warning)';
    } else if (type === 'success') {
      toast.style.borderLeftColor = 'var(--success)';
    }

    toast.innerHTML = `
      <span>${type === 'error' ? '❌' : (type === 'warning' ? '⚠️' : '⚡')}</span>
      <span>${message}</span>
    `;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
}

// Global bootstrap
document.addEventListener('DOMContentLoaded', () => {
  window.app = new App();
});
