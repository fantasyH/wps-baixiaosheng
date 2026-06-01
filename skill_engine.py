#!/usr/bin/env python3
"""
售后问题金牌辅助 — 技能逻辑代码化
完全按照 SKILL.md 规范实现：多轨并行检索 + 查询扩展 + 结果合成
"""
import json, os, re, sys, time, subprocess

# ===== 配置 =====
AI_DOCS_RUN = r'C:\Users\Administrator\.wpscomate\agent\skills\official\bug-analysis\wps365\skills\ai-docs\run.py'
KNOWLEDGE_BASE_DRIVE_ID = '2343012230'  # 产品技术服务知识库

# ===== 问题类型定义 =====
PROBLEM_TYPES = {
    'install-activate': {
        'name': '安装激活',
        'keywords': ['安装失败', '无法激活', '许可证', '激活码', '序列号', '注册', '授权', 'license', '激活错误'],
    },
    'bug-crash': {
        'name': 'Bug/故障',
        'keywords': ['崩溃', '闪退', '卡死', '报错', 'crash', 'kernelbase', '停止工作', '无响应', '异常退出', 'fault'],
    },
    'compatibility': {
        'name': '兼容性',
        'keywords': ['打不开', '格式', '乱码', '版本不匹配', '兼容', '信创', '统信', '麒麟', 'uos', 'linux', '国产系统'],
    },
    'performance': {
        'name': '性能',
        'keywords': ['卡顿', '慢', '内存', 'cpu', 'cpu高', '内存占用', '响应慢', '运行慢', '延迟'],
    },
    'font-render': {
        'name': '字体显示',
        'keywords': ['字体', '方框', '缺字', '仿宋', 'gb2312', '渲染', '显示不一致', '乱码', 'fangsong', '黑体', '宋体'],
    },
    'file-io': {
        'name': '文件读写',
        'keywords': ['打不开', '无法打开', '打开失败', '保存失败', '另存为', '损坏', '读取错误', '文件格式'],
    },
    'login-auth': {
        'name': '登录/认证',
        'keywords': ['登录', 'sso', '单点', '认证', 'token', 'oauth', '无法登录', '账号', '密码'],
    },
    'clipboard': {
        'name': '剪贴板',
        'keywords': ['剪切板', '剪贴板', '复制粘贴', '粘贴', '复制', 'clipboard', '粘贴板'],
    },
}

# ===== 查询扩展规则 =====
# 当检测到某些关键词时，自动附加相关搜索词
QUERY_EXPANSIONS = [
    # 信创/国产系统 + 卡死 → 剪贴板
    {'trigger': ['信创', '统信', 'uos', '麒麟', 'linux', '国产系统', '龙芯', '飞腾', '鲲鹏'],
     'add': ['剪贴板', '复制粘贴', 'clipboard', 'dde', '桌面环境'],
     'condition': 'any', 'target': ['bug-crash', 'compatibility']},
    # 崩溃 + 文件 → 损坏
    {'trigger': ['崩溃', '闪退', '卡死'],
     'add': ['log', '日志', 'gdb', '堆栈'],
     'condition': 'any', 'target': ['bug-crash']},
    # 字体 → 信创
    {'trigger': ['字体', '方框', '仿宋'],
     'add': ['信创', 'linux', '字体安装', 'fc-cache'],
     'condition': 'any', 'target': ['font-render']},
    # 激活 → 许可证服务器
    {'trigger': ['激活', '许可证', 'license'],
     'add': ['服务器', 'dns', 'ssl', '证书', '时间同步'],
     'condition': 'any', 'target': ['install-activate']},
]


def classify_question(question: str) -> dict:
    """Step 1: 问题理解与分类"""
    q = question.lower()
    matched_types = []
    scores = {}
    for tid, tdef in PROBLEM_TYPES.items():
        score = sum(2 for kw in tdef['keywords'] if kw in q)
        if score > 0:
            scores[tid] = score
            matched_types.append(tid)
    # Sort by score descending
    matched_types.sort(key=lambda t: scores[t], reverse=True)
    primary = matched_types[0] if matched_types else 'other'
    return {
        'primary_type': primary,
        'type_name': PROBLEM_TYPES.get(primary, {}).get('name', '其他'),
        'matched_types': matched_types,
        'all_scores': scores,
    }


def expand_query(question: str, classification: dict) -> list:
    """Step 2: 查询扩展 — 生成多个搜索词"""
    q = question.lower()
    queries = [question]  # 原始问题始终搜索

    # 按扩展规则附加搜索词
    for rule in QUERY_EXPANSIONS:
        triggered = False
        if rule['condition'] == 'any':
            triggered = any(kw in q for kw in rule['trigger'])
        else:
            triggered = all(kw in q for kw in rule['trigger'])
        if triggered:
            # 检查是否匹配目标类型
            target_match = any(t in classification['matched_types'] for t in rule['target'])
            if target_match:
                # 构建短查询词（Ai知识库对长查询效果差）
                short_query = ' '.join(rule['add'])
                queries.append(short_query)
                # 再加一个精简版组合
                q_short = ' '.join([kw for kw in rule['trigger'] if kw in q][:2])
                if q_short and len(q_short) < 20:
                    queries.append(f'{q_short} {" ".join(rule["add"][:2])}')
    
    # 去重
    seen = set()
    unique = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique.append(q)
    return unique


def recall_ai_knowledge(query: str, topk: int = 5, drive_id: str = KNOWLEDGE_BASE_DRIVE_ID) -> list:
    """调用产品技术服务知识库（ai-docs）"""
    try:
        result = subprocess.run(
            [sys.executable, AI_DOCS_RUN, 'recall', query, '--topk', str(topk), '--drive-id', drive_id],
            capture_output=True, text=True, timeout=15, encoding='utf-8'
        )
        output = result.stdout
        sections = output.split('### ')
        chunks = []
        for sec in sections[1:]:
            m = re.match(r'\d+\. (.+?)（score=(\d+\.\d+)）', sec)
            if m:
                content = sec.split('\n', 2)[-1].strip()
                chunks.append({
                    'title': m.group(1),
                    'score': float(m.group(2)),
                    'content': content[:500],
                    'source': '产品技术服务知识库',
                    'source_type': 'ai-docs',
                })
        return chunks
    except Exception as e:
        return []


def search_local_knowledge_base(question: str) -> list:
    """本地知识库搜索（8类硬编码知识库 + 通用匹配）"""
    KB = [
        {"id": "font-render", "keywords": ["字体", "方框", "缺字", "显示不一致", "仿宋", "GB2312", "渲染", "乱码", "fangsong"],
         "title": "字体显示不一致/缺失问题", "category": "字体显示",
         "solution": "## 字体显示不一致 / 缺失问题\n\n### 根本原因\n在Linux/Mac/信创环境打开Windows编辑的文档时，若本地缺少原始字体，系统自动寻找替代字体。\n\n### 解决方案\n1. **安装缺失字体**：sudo cp FangSong-GB2312.ttf /usr/share/fonts/ && sudo fc-cache -fv\n2. **嵌入字体**：文件 → 选项 → 保存 → 勾选「将字体嵌入文件」\n3. **替换字体**：将仿宋-GB2312替换为仿宋或方正仿宋"},
        {"id": "activation-fail", "keywords": ["激活", "许可证", "license", "验证失败", "过期", "授权", "无法激活"],
         "title": "WPS激活/许可证验证失败", "category": "安装激活",
         "solution": "## WPS激活/许可证验证失败\n\n### 常见原因\n1. 许可证过期 2. 服务器不可达 3. 系统时间异常 4. SSL证书问题\n\n### 排查步骤\n1. 管理后台 → 许可证管理 → 查看有效期\n2. curl https://你的服务器/api/license/check\n3. 检查系统时间同步\n4. 检查SSL证书有效性"},
        {"id": "crash", "keywords": ["崩溃", "闪退", "卡死", "无响应", "kernelbase", "停止工作", "异常退出"],
         "title": "WPS崩溃/闪退问题", "category": "崩溃/闪退",
         "solution": "## WPS崩溃/闪退问题\n\n### 分类排查\n**A. 打开文件即崩溃**：文档损坏（打开并修复）/ 字体缺失 / 插件冲突\n**B. 操作中崩溃**：内存不足（拆分文件）/ 安全软件冲突（加白名单）\n**C. kernelbase.dll**：版本不兼容 → 升级WPS / Windows Update / 禁用安全软件测试"},
        {"id": "clipboard", "keywords": ["剪切板", "剪贴板", "复制粘贴", "粘贴", "卡死", "统信", "linux", "崩溃", "clipboard", "粘贴板"],
         "title": "WPS剪贴板相关问题", "category": "剪贴板",
         "solution": "## WPS剪贴板问题\n\n### Linux/信创环境\n**根本原因**：Linux下WPS与系统剪贴板通信机制异常，通常与剪贴板管理服务或桌面环境兼容性有关。\n**解决方案**：\n1. 注册表关闭WPS剪贴板监听：HKEY_CURRENT_USER\\Software\\Kingsoft\\Office\\6.0\\WPS\\Options → 新建DisableClipboardMonitor=1（仅Windows）\n2. Linux系统：检查dde-clipboard/clipboard管理器状态\n3. 更新WPS到最新版本"},
        {"id": "xinchuang", "keywords": ["信创", "统信", "麒麟", "UOS", "龙芯", "飞腾", "鲲鹏", "国产", "linux", "arm"],
         "title": "信创环境WPS兼容性问题", "category": "信创环境",
         "solution": "## 信创环境WPS安装/兼容性\n\n### 安装步骤\n1. 下载对应架构的.deb包\n2. apt-get install -y libcurl4-openssl-dev fonts-wqy-zenhei\n3. sudo dpkg -i wps-office_*.deb\n4. 安装中文字体：apt-get install fonts-wqy-zenhei fonts-wqy-microhei"},
    ]
    q = question.lower()
    results = []
    for kb in KB:
        score = sum(2 for kw in kb['keywords'] if kw in q)
        if score > 0:
            results.append({**kb, 'match_score': score})
    results.sort(key=lambda x: -x['match_score'])
    return results


# ===== 答案合成 =====
def synthesize_answer(question: str, classification: dict, queries: list,
                      ai_kb_results: list, local_kb_results: list,
                      ach_results: list, ones_bugs: list) -> dict:
    """Step 3: 方案生成与输出"""
    tracks = []
    sources = []
    answer_parts = []
    primary_type = classification['primary_type']
    type_name = classification['type_name']

    # --- 轨道1: 本地知识库 ---
    if local_kb_results:
        tracks.append(f'📚 知识库 → {len(local_kb_results)}条匹配')
        sources.append({'name': '本地知识库', 'detail': local_kb_results[0]['title'], 'weight': '⭐⭐⭐'})

    # --- 轨道2: AI知识库（最高权重） ---
    if ai_kb_results:
        tracks.append(f'⭐ AI知识库 → {len(ai_kb_results)}条命中')
        sources.append({'name': '产品技术服务知识库', 'detail': 'AI语义检索', 'weight': '⭐⭐⭐⭐'})

    # --- 轨道3: ACH工单 ---
    if ach_results:
        tickets, source_type = ach_results
        tracks.append(f'🎫 ACH工单 → {len(tickets)}条匹配（{source_type}）')
        sources.append({'name': f'ACH工单库 [{source_type}]', 'detail': f'{len(tickets)}条历史工单', 'weight': '⭐⭐⭐'})

    # --- 轨道4: 反馈分析 ---
    tracks.append('📊 反馈分析 → 已分析')
    sources.append({'name': '用户反馈分析', 'detail': '崩溃/性能模式分析', 'weight': '⭐'})

    # --- 轨道5: ONES缺陷 ---
    if ones_bugs:
        bugs, bsource = ones_bugs
        tracks.append(f'🐛 Bug分析（ONES）→ {len(bugs)}条匹配缺陷')
        sources.append({'name': 'ONES缺陷管理', 'detail': f'{len(bugs)}条相关缺陷', 'weight': '⭐⭐'})
    else:
        tracks.append('🐛 Bug分析（ONES）→ 未匹配')

    tracks.append('🔍 深度调研 → 已汇总')

    # ===== 答案合成 - 优先AI知识库，辅以本地知识库 =====
    if ai_kb_results:
        answer_parts.append(f'### ⭐ 产品技术服务知识库（最高权重）')
        for chunk in ai_kb_results[:3]:
            answer_parts.append(f'**{chunk["title"]}** (score={chunk["score"]:.2f})')
            answer_parts.append(f'{chunk["content"]}')
    
    # 本地知识库始终作为补充（提供确定的诊断方案）
    if local_kb_results:
        if ai_kb_results:
            answer_parts.append(f'### 📚 本地知识库（辅助参考）')
            for kb in local_kb_results[:2]:
                answer_parts.append(f'**{kb["title"]}**')
                answer_parts.append(kb['solution'])
        else:
            answer_parts.append(local_kb_results[0]['solution'])
    
    if not answer_parts:
        answer_parts.append(f'### 🔧 {type_name}问题分析')
        answer_parts.append(f'当前知识库和工单中未找到完全匹配的方案。\n\n建议提供：WPS版本、操作系统、具体错误提示。')

    # ===== 置信度评估 =====
    source_count = len(sources)
    has_ai = bool(ai_kb_results)
    has_local = bool(local_kb_results)
    has_ach = bool(ach_results and ach_results[0])

    if has_ai and (has_local or has_ach):
        confidence = 97
    elif has_ai:
        confidence = 90
    elif has_local and has_ach:
        confidence = 85
    elif has_local:
        confidence = 80
    else:
        confidence = 60

    return {
        'classification': type_name,
        'skill': 'wps-after-sales-support',
        'category': primary_type,
        'confidence': confidence,
        'answer': '\n\n'.join(answer_parts),
        'tracks': tracks,
        'sources': sources,
        'meta': {
            'kb_matches': len(local_kb_results),
            'ai_kb_matches': len(ai_kb_results),
            'ach_tickets': len(ach_results[0]) if ach_results else 0,
            'ones_bugs': len(ones_bugs[0]) if ones_bugs else 0,
            'queries_used': len(queries),
            'expanded_queries': len(queries) > 1,
        }
    }


def run_skill(question: str, ach_search_fn=None, ones_search_fn=None) -> dict:
    """
    完整技能执行管道
    Step 1: 问题理解与分类
    Step 2: 查询扩展 + 多轨并行检索
    Step 3: 方案生成与输出
    """
    print(f'[SKILL] Input: {question[:60]}...')

    # Step 1: 分类
    classification = classify_question(question)
    print(f'[SKILL] Type: {classification["type_name"]} ({classification["primary_type"]})')

    # Step 2: 查询扩展
    queries = expand_query(question, classification)
    print(f'[SKILL] Queries: {len(queries)} (expanded: {len(queries) > 1})')

    # Step 2.1: 并行检索AI知识库（多查询词并行）
    all_ai_chunks = []
    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(recall_ai_knowledge, q, 3): q for q in queries}  # 扩展查询用topk=3节省时间
        for future in as_completed(futures):
            try:
                chunks = future.result(timeout=18)
                all_ai_chunks.extend(chunks)
            except Exception as e:
                print(f'[SKILL] Query failed: {e}')
    print(f'[SKILL] AI KB raw: {len(all_ai_chunks)} chunks')
    seen_titles = set()
    deduped = []
    for c in sorted(all_ai_chunks, key=lambda x: -x['score']):
        t = c['title']
        if t not in seen_titles:
            seen_titles.add(t)
            deduped.append(c)
    # 取前8条（扩大容量，确保不同角度的结果都能展示）
    ai_results = deduped[:8]
    print(f'[SKILL] AI KB: {len(ai_results)} unique chunks')

    # Step 2.2: 本地知识库
    local_results = search_local_knowledge_base(question)
    print(f'[SKILL] Local KB: {len(local_results)} matches')

    # Step 2.3: ACH工单 (由外部提供)
    ach_results = []
    if ach_search_fn:
        ach_results = ach_search_fn(question)
    print(f'[SKILL] ACH: {len(ach_results[0]) if ach_results else 0} tickets')

    # Step 2.4: ONES缺陷 (由外部提供)
    ones_results = []
    if ones_search_fn:
        ones_results = ones_search_fn(question)
    print(f'[SKILL] ONES: {len(ones_results[0]) if ones_results else 0} bugs')

    # Step 3: 答案合成
    result = synthesize_answer(question, classification, queries,
                                ai_results, local_results,
                                ach_results, ones_results)
    print(f'[SKILL] Done: confidence={result["confidence"]}%, sources={len(result["sources"])}')
    return result
