#!/usr/bin/env python3
"""
WPS百晓生 — 售后问题金牌辅助 (云端版)
架构：Flask + WPS V7 API + LLM 合成
"""
import os, json, sys, re, time, threading
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from skill_engine import run_skill, classify_question, expand_query, search_local_knowledge_base, synthesize_answer, recall_ai_knowledge
from llm_synthesis import LLMSynthesizer

app = Flask(__name__)
CORS(app)

# ===== Config from Environment =====
WPS_SID = os.environ.get('WPS_SID', '')
ACH_TOKEN = os.environ.get('ACH_TOKEN', '')
ACH_TOKEN_LOCAL = ''  # loaded from .ach_token.json
ACH_USER = ''

# Load local ACH token if available
_ach_token_path = os.path.join(os.path.dirname(__file__), '.ach_token.json')
if os.path.exists(_ach_token_path):
    try:
        with open(_ach_token_path, 'r') as f:
            _td = json.load(f)
            ACH_TOKEN_LOCAL = (_td.get('access_token') or _td.get('token') or '')
            if _td.get('user_info'):
                ACH_USER = _td.get('user_info', {}).get('nickName', '')
            elif _td.get('userName'):
                ACH_USER = _td.get('userName', '')
            else:
                ACH_USER = '付树晖'
        if ACH_TOKEN_LOCAL:
            print(f'[ACH] 已从本地加载Token, 用户: {ACH_USER}')
    except Exception as e:
        print(f'[ACH] 加载本地Token失败: {e}')

_has_real_token = bool(ACH_TOKEN or ACH_TOKEN_LOCAL)
ACH_CLIENT_ID = os.environ.get('ACH_CLIENT_ID', '2238f5902cf06e2e30317de35b8c432f')
ACH_BASE = os.environ.get('ACH_BASE', 'https://wpsservice-sys.wps.cn/achserver')
AI_DOCS_DRIVE_ID = os.environ.get('AI_DOCS_DRIVE_ID', '2343012230')
LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'deepseek')  # deepseek, openai, etc.
LLM_API_KEY = os.environ.get('LLM_API_KEY', '')
LLM_MODEL = os.environ.get('LLM_MODEL', 'deepseek-chat')
LLM_API_BASE = os.environ.get('LLM_API_BASE', 'https://api.deepseek.com')
PORT = int(os.environ.get('PORT', 5099))

# ===== Initialize =====
llm = LLMSynthesizer(provider=LLM_PROVIDER, api_key=LLM_API_KEY, 
                     model=LLM_MODEL, api_base=LLM_API_BASE)

# ===== Knowledge Base Recall (via kb-retriever subprocess) =====
def recall_knowledge_base(query: str, drive_id: str = None, topk: int = 5) -> list:
    """通过 kb-retriever 召回知识库"""
    if not WPS_SID:
        return []
    try:
        results = recall_ai_knowledge(query, topk=topk, drive_id=drive_id or AI_DOCS_DRIVE_ID)
        return results
    except Exception as e:
        print(f'[KB] Recall error: {e}')
        return []


# ===== ACH Search =====
ACH_CACHE = []  # Loaded at boot from data/

def _load_ach_cache():
    global ACH_CACHE
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    if not os.path.isdir(data_dir):
        print('[ACH] No data directory')
        return
    for month in ['dec-2025', 'jan-2026', 'feb-2026', 'march-2026', 'april-2026']:
        fpath = os.path.join(data_dir, month, 'tickets_analysis.json')
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                ACH_CACHE.extend(data)
    print(f'[ACH] Loaded {len(ACH_CACHE)} tickets')

def search_ach(question: str) -> tuple:
    """搜索 ACH 工单"""
    if not question:
        return [], 'none'
    lower_q = question.lower()
    scores = {}
    for i, t in enumerate(ACH_CACHE):
        text = (t.get('customer', '') + ' ' + t.get('chat_name', '') + ' ' + ' '.join(t.get('problems', []))).lower()
        score = sum(10 for cjk in re.findall(r'[\u4e00-\u9fff]{2,8}', lower_q) if cjk in text)
        if score > 0:
            scores[i] = score
    top = sorted(scores.items(), key=lambda x: -x[1])[:5]
    results = []
    for idx, _ in top:
        t = ACH_CACHE[idx]
        results.append({
            'ticket_number': t.get('ticket_number', t.get('chat_name', '')),
            'chat_name': t.get('chat_name', ''),
            'customer': t.get('customer', ''),
            'problems': t.get('problems', []),
            'has_solution': t.get('has_solution', False),
        })
    return results, 'cache'


# ===== ONES Search =====
ONES_CACHE = []

def _load_ones_cache():
    global ONES_CACHE
    try:
        sys.path.insert(0, r'C:\Users\Administrator\.wpscomate\agent\skills\official\bug-analysis\ones\scripts')
        from ones_client import OnesClient
        client = OnesClient(config_path=r'C:\Users\Administrator\.wpscomate\agent\skills\official\bug-analysis\ones\config\ones.properties')
        results = client.get_tasks_by_page(issue_type_uuid='Tk5ypVS8', columns=['number', 'name', 'status {name}'])
        items = results.get('list', [])
        for item in items:
            s = item.get('status', {})
            ONES_CACHE.append({
                'title': item.get('name', '') or '',
                'id': str(item.get('number', '') or ''),
                'status': str(s.get('name', '?')) if isinstance(s, dict) else '?',
            })
        print(f'[ONES] Loaded {len(ONES_CACHE)} defects')
    except Exception as e:
        print(f'[ONES] Load failed: {e}')

def search_ones(question: str) -> tuple:
    if not ONES_CACHE:
        return [], 'empty'
    keywords = re.findall(r'[\u4e00-\u9fff]{2,8}', question)
    if not keywords:
        return [], 'no-keywords'
    matched = []
    for item in ONES_CACHE:
        title = item.get('title', '')
        score = sum(10 for kw in keywords if kw in title)
        if score > 0:
            matched.append(item)
    matched.sort(key=lambda x: -sum(10 for kw in keywords if kw in x.get('title', '')))
    return matched[:5], 'ones-cache'


# ===== API Routes =====

# ----- React Frontend (v2) -----
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), 'frontend', 'dist')

@app.route('/')
def index():
    """Serve React frontend"""
    idx = os.path.join(FRONTEND_DIR, 'index.html')
    if os.path.exists(idx):
        resp = send_from_directory(FRONTEND_DIR, 'index.html')
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        return resp
    # Fallback to old index.html
    fallback = os.path.join(os.path.dirname(__file__), 'index.html')
    if os.path.exists(fallback):
        with open(fallback, 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
    return jsonify({'error': 'frontend not found'}), 404


@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve React build assets"""
    resp = send_from_directory(os.path.join(FRONTEND_DIR, 'assets'), filename)
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp


@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'cached_tickets': len(ACH_CACHE),
        'ones_bugs': len(ONES_CACHE),
        'llm_configured': bool(LLM_API_KEY),
        'kb_available': bool(WPS_SID),
        'token_valid': _has_real_token,
        'version': '5.0.0-cloud',
    })


@app.route('/api/skill/after-sales', methods=['POST'])
def after_sales():
    """售后问题诊断 — 完整管道
    使用 skill_engine.run_skill() 实现多查询词并行检索
    """
    question = request.json.get('question', '')
    if not question:
        return jsonify({'error': 'missing question'}), 400

    t0 = time.time()
    
    # 使用 skill_engine 的 run_skill 完整管道
    # 传入 ach_search / ones_search 作为回调
    result = run_skill(
        question,
        ach_search_fn=search_ach,
        ones_search_fn=search_ones
    )
    
    # 不再调用 recall_knowledge_base (已由 run_skill 内部处理)
    # 不再手动 dedup (已由 run_skill 内部处理)
    # 不再手动 synthesize (已由 run_skill 内部处理)
    
    # Step 5: LLM polish (if configured) — 在 run_skill 结果之上再增强
    if LLM_API_KEY and result.get('answer'):
        try:
            polished = llm.synthesize(question, result['answer'], result.get('sources', []))
            if polished:
                result['answer'] = polished
                result['llm_enhanced'] = True
        except Exception as e:
            print(f'[LLM] Synthesis error: {e}')
            result['llm_enhanced'] = False
    else:
        result['llm_enhanced'] = False
    
    result['elapsed'] = round(time.time() - t0, 1)
    return jsonify(result)


@app.route('/api/stats')
def stats():
    return jsonify({
        'ach_tickets': len(ACH_CACHE),
        'ones_bugs': len(ONES_CACHE),
    })


# Stub routes for frontend compatibility
@app.route('/api/auth/status')
def auth_status():
    return jsonify({
        'authorized': _has_real_token,
        'user': {'nickName': ACH_USER} if ACH_USER else {},
        'cached_tickets': len(ACH_CACHE),
        'token_saved_at': os.path.getmtime('.ach_token.json') if os.path.exists('.ach_token.json') else None,
        'mode': 'local' if _has_real_token else 'cloud',
    })


@app.route('/api/ach-data')
def ach_data():
    keyword_index = {}
    for i, t in enumerate(ACH_CACHE):
        text = f"{t.get('customer', '')} {t.get('group', '')} {t.get('problem', '')}"
        for kw in text.split():
            kw = kw.strip()
            if len(kw) >= 2:
                keyword_index.setdefault(kw, []).append(i)
    tickets = [{'i': t.get('id', ''), 'c': t.get('customer', ''), 'g': t.get('group', '')} for t in ACH_CACHE]
    return jsonify({'t': tickets, 'k': keyword_index, 'count': len(ACH_CACHE)})


@app.route('/api/kb/search', methods=['GET', 'POST'])
def kb_search():
    if request.method == 'POST':
        q = request.json.get('question', '')
    else:
        q = request.args.get('q', '')
    if not q:
        return jsonify({'solutions': []})
    results = search_local_knowledge_base(q)
    return jsonify({'solutions': [r['solution'] for r in results[:3]]})


@app.route('/api/health')
def health_api():
    return health()


# ===== Boot =====
if __name__ == '__main__':
    print(f'[BOOT] WPS百晓生 v5.0 (云端版)')
    print(f'[BOOT] LLM: {LLM_PROVIDER} {"✅ 已配置" if LLM_API_KEY else "❌ 未配置"}')
    print(f'[BOOT] 知识库: {"✅ " + AI_DOCS_DRIVE_ID if WPS_SID else "❌ 需配置 WPS_SID"}')
    
    # Load caches
    _load_ach_cache()
    threading.Thread(target=_load_ones_cache, daemon=True).start()
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
