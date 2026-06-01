#!/usr/bin/env python3
"""
LLM 答案合成模块
将 skill_engine 的搜索结果通过 LLM 组织成结构化诊断方案
支持任何 OpenAI-compatible API（DeepSeek, 智谱, 通义千问等）
"""
import json, os

class LLMSynthesizer:
    """LLM 答案合成器"""
    
    def __init__(self, provider='deepseek', api_key='', model='deepseek-chat', 
                 api_base='https://api.deepseek.com'):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.api_base = api_base
        
        # Provider-specific endpoints
        self.endpoints = {
            'deepseek': 'https://api.deepseek.com/v1/chat/completions',
            'openai': 'https://api.openai.com/v1/chat/completions',
            'zhipu': 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
            'qwen': 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
        }
        if api_base:
            self.endpoints[provider] = f'{api_base}/v1/chat/completions'
    
    def synthesize(self, question: str, search_answer: str, sources: list) -> str:
        """将搜索结果合成为结构化诊断方案"""
        if not self.api_key:
            return search_answer
        
        endpoint = self.endpoints.get(self.provider, self.endpoints['deepseek'])
        
        # Build source summary
        source_summary = '\n'.join([f"- {s.get('name','')}: {s.get('detail','')} (权重: {s.get('weight','')})" 
                                    for s in sources[:5]]) if sources else "无"
        
        system_prompt = """你是一名 WPS 办公软件技术支持专家。你的任务是根据搜索到参考资料，将用户的问题诊断方案重新组织为清晰、专业的结构化回答。

要求：
1. 【根因分析】用通俗语言解释问题根本原因，1-3句话
2. 【排查步骤】列出具体的排查操作，每步可执行
3. 【解决方案】给出可直接执行的解决步骤
4. 【参考来源】列出参考资料的来源

注意：
- 只基于提供的资料回答，不编造
- 不要输出文档原始标题或文件名（如 "崩溃或者卡死时收集日志.otl"）
- 提炼核心信息，不复制整段文档
- 如果资料中明确提到某工单案例，可以引用
- 如果资料不足以给出完整方案，诚实说明"""
        
        user_prompt = f"""## 用户问题
{question}

## 搜索到的参考资料
{search_answer[:3000]}

## 来源摘要
{source_summary}

请基于以上资料，生成结构化的诊断方案回答。"""
        
        try:
            import requests
            r = requests.post(endpoint, json={
                'model': self.model,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                'temperature': 0.3,
                'max_tokens': 1500,
            }, headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            }, timeout=30)
            
            if r.status_code == 200:
                data = r.json()
                content = data['choices'][0]['message']['content']
                # Add source footer
                if sources:
                    footer = '\n\n---\n**参考来源**: ' + ', '.join([s.get('name','') for s in sources[:3]])
                    content += footer
                return content
            else:
                print(f'[LLM] API error: {r.status_code} {r.text[:200]}')
                return search_answer
        except Exception as e:
            print(f'[LLM] Error: {e}')
            return search_answer