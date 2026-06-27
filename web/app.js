const state = {
  tasks: [],
  selectedTaskId: null,
  selectedPayload: null,
  localWorkflows: null,
  locale: detectLocale(),
};

const messages = {
  zh: {
    appTitle: 'AI Office',
    appSubtitle: '本地多 AI 员工协同工作台。',
    connecting: '连接中',
    connected: '已连接',
    disconnected: '已断开',
    languageButton: 'English',
    newTask: '新建任务',
    title: '标题',
    titlePlaceholder: '搭建 AI Office MVP',
    sourceUrl: '工作项链接',
    sourceUrlPlaceholder: '粘贴工作项链接',
    description: '描述',
    descriptionPlaceholder: '目标、背景、验收标准',
    risk: '风险',
    riskNormal: '普通',
    riskLow: '低',
    riskHigh: '高',
    createTask: '创建任务',
    tasks: '任务',
    refresh: '刷新',
    selectTask: '选择一个任务',
    noTask: '无任务',
    emptyDetail: '创建或选择一个任务来查看协作流程。',
    runPlanner: '运行规划者',
    runExecutor: '运行执行者',
    runReviewer: '运行审查者',
    runValidator: '运行验收者',
    events: '事件',
    artifacts: '产物',
    localWorkflows: '本地工作流',
    workflowDetected: '已检测到本地工作流库',
    workflowMissing: '未检测到本地工作流库',
    workflowCommands: '命令索引',
    workItem: '工作项分析',
    source: '来源',
    type: '类型',
    externalId: '外部 ID',
    shortId: '短 ID',
    branchName: '计划分支',
    confidence: '置信度',
    noTasksYet: '暂无任务。',
    noDescription: '暂无描述。',
    noEvents: '暂无事件。',
    noArtifacts: '暂无产物。',
    owner: '负责人',
    planner: '规划者',
    developer: '执行者',
    reviewer: '审查者',
    validator: '验收者',
  },
  en: {
    appTitle: 'AI Office',
    appSubtitle: 'Local multi-agent workflow desk.',
    connecting: 'Connecting',
    connected: 'Connected',
    disconnected: 'Disconnected',
    languageButton: '中文',
    newTask: 'New Task',
    title: 'Title',
    titlePlaceholder: 'Build AI Office MVP',
    sourceUrl: 'Work Item URL',
    sourceUrlPlaceholder: 'Paste work item URL',
    description: 'Description',
    descriptionPlaceholder: 'Goal, context, acceptance criteria',
    risk: 'Risk',
    riskNormal: 'Normal',
    riskLow: 'Low',
    riskHigh: 'High',
    createTask: 'Create Task',
    tasks: 'Tasks',
    refresh: 'Refresh',
    selectTask: 'Select a task',
    noTask: 'No task',
    emptyDetail: 'Create or select a task to inspect the workflow.',
    runPlanner: 'Run Planner',
    runExecutor: 'Run Executor',
    runReviewer: 'Run Reviewer',
    runValidator: 'Run Validator',
    events: 'Events',
    artifacts: 'Artifacts',
    localWorkflows: 'Local Workflows',
    workflowDetected: 'Local workflow library detected',
    workflowMissing: 'Local workflow library not detected',
    workflowCommands: 'Command index',
    workItem: 'Work item analysis',
    source: 'Source',
    type: 'Type',
    externalId: 'External ID',
    shortId: 'Short ID',
    branchName: 'Planned branch',
    confidence: 'Confidence',
    noTasksYet: 'No tasks yet.',
    noDescription: 'No description.',
    noEvents: 'No events.',
    noArtifacts: 'No artifacts.',
    owner: 'owner',
    planner: 'planner',
    developer: 'executor',
    reviewer: 'reviewer',
    validator: 'validator',
  },
};

const els = {
  serverStatus: document.querySelector('#serverStatus'),
  languageButton: document.querySelector('#languageButton'),
  taskForm: document.querySelector('#taskForm'),
  titleInput: document.querySelector('#titleInput'),
  sourceUrlInput: document.querySelector('#sourceUrlInput'),
  descriptionInput: document.querySelector('#descriptionInput'),
  riskInput: document.querySelector('#riskInput'),
  refreshButton: document.querySelector('#refreshButton'),
  taskList: document.querySelector('#taskList'),
  detailTitle: document.querySelector('#detailTitle'),
  detailStatus: document.querySelector('#detailStatus'),
  detailDescription: document.querySelector('#detailDescription'),
  roleGrid: document.querySelector('#roleGrid'),
  workItemBox: document.querySelector('#workItemBox'),
  events: document.querySelector('#events'),
  artifacts: document.querySelector('#artifacts'),
  workflowRefreshButton: document.querySelector('#workflowRefreshButton'),
  workflowIndex: document.querySelector('#workflowIndex'),
};

function detectLocale() {
  const saved = localStorage.getItem('ai-office-locale');
  if (saved === 'zh' || saved === 'en') return saved;
  const languages = navigator.languages || [navigator.language || ''];
  const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone || '';
  const isChinaLocale = languages.some((language) => /^zh($|-|_)/i.test(language));
  return isChinaLocale || timeZone === 'Asia/Shanghai' ? 'zh' : 'en';
}

function t(key) {
  return messages[state.locale][key] || messages.en[key] || key;
}

function applyI18n() {
  document.documentElement.lang = state.locale === 'zh' ? 'zh-CN' : 'en';
  document.querySelectorAll('[data-i18n]').forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach((node) => {
    node.setAttribute('placeholder', t(node.dataset.i18nPlaceholder));
  });
  els.languageButton.textContent = t('languageButton');
}

function toggleLocale() {
  state.locale = state.locale === 'zh' ? 'en' : 'zh';
  localStorage.setItem('ai-office-locale', state.locale);
  applyI18n();
  renderTasks();
  renderWorkflowIndex();
  if (state.selectedPayload) renderDetail(state.selectedPayload);
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || response.statusText);
  }
  return response.json();
}

async function loadLocalWorkflows() {
  try {
    const data = await request('/api/local-workflows');
    state.localWorkflows = data.local_workflows;
    renderWorkflowIndex();
  } catch (error) {
    console.error(error);
  }
}

function renderWorkflowIndex() {
  if (!els.workflowIndex) return;
  const index = state.localWorkflows;
  if (!index) {
    els.workflowIndex.innerHTML = '<div class="task-meta">-</div>';
    return;
  }
  const title = index.enabled ? t('workflowDetected') : t('workflowMissing');
  const headings = (index.headings || []).map((heading) => `<li>${escapeHtml(heading)}</li>`).join('');
  els.workflowIndex.innerHTML = `
    <div class="workflow-item">
      <div class="artifact-title">${title}</div>
      <div class="artifact-path">${escapeHtml(index.root)}</div>
      <div class="event-body">${t('workflowCommands')}: ${index.commands_file_exists ? 'OK' : '-'}</div>
      <ul>${headings}</ul>
    </div>
  `;
}

async function loadTasks() {
  try {
    const data = await request('/api/tasks');
    state.tasks = data.tasks || [];
    els.serverStatus.textContent = t('connected');
    els.serverStatus.classList.remove('muted');
    renderTasks();
    if (!state.selectedTaskId && state.tasks.length > 0) {
      await selectTask(state.tasks[0].id);
    } else if (state.selectedTaskId) {
      await selectTask(state.selectedTaskId);
    }
  } catch (error) {
    els.serverStatus.textContent = t('disconnected');
    els.serverStatus.classList.add('muted');
    console.error(error);
  }
}

function renderTasks() {
  els.taskList.innerHTML = '';
  if (state.tasks.length === 0) {
    els.taskList.innerHTML = `<div class="task-meta">${t('noTasksYet')}</div>`;
    return;
  }
  for (const task of state.tasks) {
    const item = document.createElement('div');
    item.className = `task-item ${task.id === state.selectedTaskId ? 'active' : ''}`;
    item.innerHTML = `
      <div class="task-title">${escapeHtml(task.title)}</div>
      <div class="task-meta">${task.status} · ${t('owner')}: ${task.current_owner}</div>
    `;
    item.addEventListener('click', () => selectTask(task.id));
    els.taskList.appendChild(item);
  }
}

async function selectTask(taskId) {
  state.selectedTaskId = taskId;
  const payload = await request(`/api/tasks/${encodeURIComponent(taskId)}`);
  state.selectedPayload = payload;
  renderTasks();
  renderDetail(payload);
}

function renderDetail(payload) {
  const task = payload.task;
  els.detailTitle.textContent = task.title;
  els.detailStatus.textContent = task.status;
  els.detailDescription.textContent = task.description || t('noDescription');
  renderWorkItem(task.work_item, task.source_url);

  const roles = task.roles || {};
  els.roleGrid.innerHTML = ['planner', 'developer', 'reviewer', 'validator']
    .map((role) => `
      <div class="role-card">
        <div class="label">${t(role)}</div>
        <div class="worker">${escapeHtml(roles[role] || '-')}</div>
      </div>
    `)
    .join('');

  els.events.innerHTML = '';
  if (!payload.events || payload.events.length === 0) {
    els.events.innerHTML = `<div class="task-meta">${t('noEvents')}</div>`;
  } else {
    for (const event of payload.events.slice().reverse()) {
      const item = document.createElement('div');
      item.className = 'event';
      item.innerHTML = `
        <div class="event-title">${escapeHtml(event.type)} · ${escapeHtml(event.actor)}</div>
        <div class="event-body">${escapeHtml(event.time)}<br>${escapeHtml(JSON.stringify(event.payload || {}))}</div>
      `;
      els.events.appendChild(item);
    }
  }

  els.artifacts.innerHTML = '';
  if (!payload.artifacts || payload.artifacts.length === 0) {
    els.artifacts.innerHTML = `<div class="task-meta">${t('noArtifacts')}</div>`;
  } else {
    for (const artifact of payload.artifacts) {
      const item = document.createElement('div');
      item.className = 'artifact';
      item.innerHTML = `
        <div class="artifact-title">${escapeHtml(artifact.name)}</div>
        <div class="artifact-path">${escapeHtml(artifact.path)}</div>
      `;
      els.artifacts.appendChild(item);
    }
  }
}

function renderWorkItem(workItem, sourceUrl) {
  els.workItemBox.classList.toggle('visible', Boolean(workItem));
  if (!workItem) {
    els.workItemBox.innerHTML = '';
    return;
  }
  const rows = [
    [t('source'), sourceUrl || '-'],
    [t('type'), workItem.item_type || '-'],
    [t('externalId'), workItem.external_id || '-'],
    [t('shortId'), workItem.short_id || '-'],
    [t('branchName'), workItem.branch_name || '-'],
    [t('confidence'), workItem.confidence || '-'],
  ];
  els.workItemBox.innerHTML = `
    <div class="artifact-title">${t('workItem')}</div>
    <div class="kv-grid">
      ${rows.map(([key, value]) => `
        <div class="kv-key">${escapeHtml(key)}</div>
        <div class="kv-value">${escapeHtml(value)}</div>
      `).join('')}
    </div>
  `;
}

async function createTask(event) {
  event.preventDefault();
  const payload = {
    title: els.titleInput.value.trim(),
    source_url: els.sourceUrlInput.value.trim(),
    description: els.descriptionInput.value.trim(),
    risk: els.riskInput.value,
  };
  if (!payload.title) return;
  const data = await request('/api/tasks', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  els.taskForm.reset();
  await loadTasks();
  await selectTask(data.task.id);
}

async function runStep(actor) {
  if (!state.selectedTaskId) return;
  await request(`/api/tasks/${encodeURIComponent(state.selectedTaskId)}/step`, {
    method: 'POST',
    body: JSON.stringify({ actor }),
  });
  await loadTasks();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

els.taskForm.addEventListener('submit', createTask);
els.refreshButton.addEventListener('click', loadTasks);
els.workflowRefreshButton.addEventListener('click', loadLocalWorkflows);
els.languageButton.addEventListener('click', toggleLocale);
document.querySelectorAll('[data-actor]').forEach((button) => {
  button.addEventListener('click', () => runStep(button.dataset.actor));
});

applyI18n();
loadTasks();
loadLocalWorkflows();
