/**
 * 3D Interactive Pipeline Visualizer
 */

export function renderWorkflowMap(containerId, activeStepName = 'ORDER_CREATED', workflowStatus = 'RUNNING') {
  const container = document.getElementById(containerId);
  if (!container) return;

  const stages = [
    { id: 'ORDER_CREATED', label: 'Order', icon: '📦' },
    { id: 'PAYMENT_PROCESSING', label: 'Payment', icon: '💳' },
    { id: 'INVENTORY_CHECK', label: 'Inventory', icon: '🏬' },
    { id: 'ORDER_CONFIRMATION', label: 'Confirm', icon: '📄' },
    { id: 'DELIVERY_SCHEDULING', label: 'Delivery', icon: '🚚' }
  ];

  let activeIndex = stages.findIndex(s => s.id === activeStepName);
  if (workflowStatus === 'COMPLETED') activeIndex = 5;
  if (activeIndex === -1) activeIndex = 0;

  const progressPercent = Math.min(100, Math.max(0, (activeIndex / (stages.length - 1)) * 100));

  let nodesHtml = '';
  stages.forEach((stage, idx) => {
    let nodeClass = '';
    let badgeText = 'Pending';

    if (workflowStatus === 'COMPLETED' || idx < activeIndex) {
      nodeClass = 'completed';
      badgeText = 'OK';
    } else if (idx === activeIndex) {
      if (workflowStatus === 'FAILED') {
        nodeClass = 'failed';
        badgeText = 'Failed';
      } else if (workflowStatus === 'RECOVERING') {
        nodeClass = 'active';
        badgeText = 'Healing';
      } else if (workflowStatus === 'WAITING_FOR_APPROVAL') {
        nodeClass = 'failed';
        badgeText = 'Approval';
      } else {
        nodeClass = 'active';
        badgeText = 'Active';
      }
    }

    nodesHtml += `
      <div class="pipe-node ${nodeClass}" data-step="${stage.id}">
        <div class="pipe-node-disc">
          <span>${stage.icon}</span>
        </div>
        <div class="pipe-node-title">${stage.label}</div>
        <div class="pipe-node-badge">${badgeText}</div>
      </div>
    `;
  });

  container.innerHTML = `
    <div class="pipeline-card">
      <div class="pipeline-line-bg">
        <div class="pipeline-line-fill" style="width: ${progressPercent}%;"></div>
      </div>
      <div class="pipeline-track">
        ${nodesHtml}
      </div>
    </div>
  `;
}
