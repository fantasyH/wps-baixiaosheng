const LOCAL_API = 'http://localhost:5099/api';

function getApiBase() {
  // If running inside Vite dev server proxy
  if (window.location.port === '5173') return '/api';
  // Otherwise try same-origin first
  return window.location.origin + '/api';
}

const API = getApiBase();

export async function healthCheck() {
  try {
    const r = await fetch(`${API}/health`, { signal: AbortSignal.timeout(3000) });
    if (!r.ok) throw new Error('Not OK');
    return await r.json();
  } catch {
    // fallback to local
    try {
      const r = await fetch(`${LOCAL_API}/health`, { signal: AbortSignal.timeout(3000) });
      if (!r.ok) throw new Error('Not OK');
      return await r.json();
    } catch {
      return null;
    }
  }
}

export async function fetchAuthStatus() {
  try {
    const r = await fetch(`${API}/auth/status`, { signal: AbortSignal.timeout(3000) });
    return await r.json();
  } catch {
    return { authorized: false };
  }
}

export async function fetchAchData() {
  try {
    const r = await fetch(`${API}/ach-data`, { signal: AbortSignal.timeout(10000) });
    return await r.json();
  } catch {
    return { count: 0 };
  }
}

export async function sendQuestion(question) {
  const cls = classifyQuestion(question);
  const isAfterSales = ['file_open','activation','crash','font','login','print','perf','compat'].includes(cls.category);
  const path = isAfterSales ? '/skill/after-sales' 
    : cls.category === 'deploy' ? '/skill/deploy'
    : cls.category === 'feedback' ? '/skill/feedback'
    : cls.category === 'bug' ? '/skill/bug'
    : '/kb/search';
  
  try {
    const r = await fetch(`${API}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
      signal: AbortSignal.timeout(90000),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return { data: await r.json(), category: cls };
  } catch (e) {
    return { error: e.message, category: cls };
  }
}

function classifyQuestion(q) {
  const rules = [
    { keys: ['打不开','无法打开','格式不支持','损坏','文件损坏'], cat: 'file_open', skill: '文件打不开' },
    { keys: ['激活','许可证','license','试用','过期','验证失败'], cat: 'activation', skill: '激活/许可证' },
    { keys: ['崩溃','闪退','crash','停止工作','异常退出'], cat: 'crash', skill: '崩溃/闪退' },
    { keys: ['字体','仿宋','GB2312','字体缺失','字体不一致'], cat: 'font', skill: '字体问题' },
    { keys: ['部署','服务器','安装','配置','POC','生产环境'], cat: 'deploy', skill: '部署规划' },
    { keys: ['反馈','崩溃趋势','堆栈','用户反馈'], cat: 'feedback', skill: '反馈分析' },
    { keys: ['bug','缺陷','根因','代码','影响面'], cat: 'bug', skill: 'Bug分析' },
    { keys: ['登录','单点','SSO','LDAP'], cat: 'login', skill: '登录问题' },
    { keys: ['打印','导出','PDF'], cat: 'print', skill: '打印/导出' },
    { keys: ['卡顿','卡死','慢','性能','响应'], cat: 'perf', skill: '性能问题' },
    { keys: ['兼容','wps365','信创','linux'], cat: 'compat', skill: '兼容性' },
  ];
  for (const rule of rules) {
    for (const key of rule.keys) {
      if (q.includes(key)) return { category: rule.cat, skill: rule.skill };
    }
  }
  return { category: 'general', skill: '知识库检索' };
}

export function getAuthUrl() {
  return `${API}/auth/start`;
}
