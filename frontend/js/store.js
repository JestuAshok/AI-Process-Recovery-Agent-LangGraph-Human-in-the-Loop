/**
 * Reactive Central State Store
 */

class Store {
  constructor() {
    this.state = {
      activeTab: 'dashboard',
      workflows: [],
      workflowStats: {
        total_workflows: 0,
        active_workflows: 0,
        failed_workflows: 0,
        recovering_workflows: 0,
        completed_workflows: 0,
        pending_approvals: 0,
        recovered_failures: 0,
        recovery_success_rate: 100
      },
      selectedWorkflowId: null,
      selectedWorkflowDetail: null,
      approvals: [],
      failures: [],
      recoveryActions: [],
      auditLogs: [],
      servicesHealth: [],
      demoScenarios: [],
      settings: null,
      aiAgentState: 'Monitoring', // Monitoring, Analyzing, Planning, Recovering, Verifying, Idle
      isLoading: false,
      activeDemoRunning: false
    };

    this.listeners = new Set();
  }

  getState() {
    return this.state;
  }

  setState(partialState) {
    this.state = { ...this.state, ...partialState };
    this.notify();
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notify() {
    for (const listener of this.listeners) {
      try {
        listener(this.state);
      } catch (e) {
        console.error('Store subscriber error:', e);
      }
    }
  }

  setAIAgentState(state) {
    this.setState({ aiAgentState: state });
  }
}

export function formatINR(val) {
  const num = Number(val) || 0;
  return '₹' + num.toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

if (typeof window !== 'undefined') {
  window.formatINR = formatINR;
}

export const store = new Store();
