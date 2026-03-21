"""LLM service: wraps OpenAI-compatible API for text generation.

Supports any OpenAI-compatible provider (OpenAI / DeepSeek / Moonshot / etc.)
by configuring LLM_BASE_URL and LLM_API_KEY in .env.
All calls have a rule-based fallback so the system still works without an API key.
"""

from __future__ import annotations

import logging

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI | None:
    global _client
    if _client is not None:
        return _client
    if not settings.llm_api_key:
        logger.warning('LLM_API_KEY not set – LLM features will use rule-based fallback')
        return None
    _client = OpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )
    return _client


def chat(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str | None:
    """Send a chat completion request. Returns the text or None on failure."""
    client = _get_client()
    if client is None:
        return None
    try:
        resp = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content
    except Exception as exc:
        logger.error('LLM call failed: %s', exc)
        return None


def chat_multi(
    messages: list[dict],
    *,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str | None:
    """Send a multi-turn chat completion request. Returns text or None."""
    client = _get_client()
    if client is None:
        return None
    try:
        resp = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content
    except Exception as exc:
        logger.error('LLM multi-turn call failed: %s', exc)
        return None


# ---------------------------------------------------------------------------
# Higher-level helpers used by AI router
# ---------------------------------------------------------------------------

def generate_interview_questions(
    job_title: str,
    focus_points: list[str],
    question_types: list[str],
    question_count: int,
    context: str = '',
) -> list[str] | None:
    """Use LLM to generate interview questions. Returns None on failure."""
    sys = (
        '你是一位资深的技术面试官。请根据用户提供的岗位、题型、知识要点生成面试题目。'
        '每道题单独一行，以"1. 2. 3."编号，不需要给出答案。语言使用中文。'
    )
    ctx_part = f'\n\n参考知识：\n{context}' if context else ''
    user = (
        f'岗位：{job_title}\n'
        f'题型要求：{", ".join(question_types)}\n'
        f'重点知识/技能：{", ".join(focus_points)}\n'
        f'题目数量：{question_count}'
        f'{ctx_part}'
    )
    text = chat(sys, user, temperature=0.8)
    if not text:
        return None
    lines = [line.strip().lstrip('0123456789.、) ').strip() for line in text.strip().splitlines()]
    return [q for q in lines if len(q) > 5][:question_count] or None


def generate_rag_answer(
    question: str,
    retrieved_context: str,
) -> str | None:
    """Use LLM to synthesize an answer from retrieved context."""
    sys = (
        '你是一位校园招聘平台的职业规划顾问。请根据用户的问题和检索到的知识库内容，'
        '给出专业、有条理的回答。如果检索内容不足以回答，可以结合你的知识补充，但要标注哪些来自知识库。'
        '语言使用中文。'
    )
    user = f'问题：{question}\n\n检索到的知识库内容：\n{retrieved_context}'
    return chat(sys, user, temperature=0.5, max_tokens=1500)


def generate_screening_evaluation(
    job_title: str,
    candidate_name: str,
    candidate_skills: list[str],
    candidate_summary: str,
    candidate_experience: str,
    score: int,
    questions: list[str],
    context: str = '',
) -> dict | None:
    """Use LLM to generate screening evaluation. Returns parsed dict or None."""
    sys = (
        '你是一位招聘 HR 助手。请根据候选人信息和面试题目，给出简明的评估意见。'
        '请按以下格式输出（每项一行）：\n'
        '评估：（一段评估总结）\n'
        '建议：（录用建议）\n'
        '关注点：（逗号分隔的关注领域）'
    )
    ctx_part = f'\n参考知识库：\n{context}' if context else ''
    user = (
        f'岗位：{job_title}\n'
        f'候选人：{candidate_name}\n'
        f'技能：{", ".join(candidate_skills)}\n'
        f'概述：{candidate_summary}\n'
        f'经历：{candidate_experience}\n'
        f'算法评分：{score} 分\n'
        f'面试题目：\n' + '\n'.join(f'{i+1}. {q}' for i, q in enumerate(questions))
        + ctx_part
    )
    text = chat(sys, user, temperature=0.4, max_tokens=800)
    if not text:
        return None

    result: dict = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if line.startswith('评估：') or line.startswith('评估:'):
            result['evaluation'] = line.split('：', 1)[-1].split(':', 1)[-1].strip()
        elif line.startswith('建议：') or line.startswith('建议:'):
            result['recommendation'] = line.split('：', 1)[-1].split(':', 1)[-1].strip()
        elif line.startswith('关注点：') or line.startswith('关注点:'):
            raw = line.split('：', 1)[-1].split(':', 1)[-1].strip()
            result['focus_areas'] = [a.strip() for a in raw.split('，') if a.strip()] or [a.strip() for a in raw.split(',') if a.strip()]
    return result if result else None


def generate_mock_feedback(
    job_title: str,
    learning_content: str,
    questions: list[str],
    score: int,
) -> dict | None:
    """Use LLM to generate mock interview feedback. Returns parsed dict or None."""
    sys = (
        '你是一位面试辅导教练。请根据学生的学习内容和模拟面试题目，给出个性化反馈。'
        '请按以下格式输出（每项一行）：\n'
        '反馈：（整体评价）\n'
        '优势：（逗号分隔）\n'
        '改进：（逗号分隔）\n'
        '下一步：（逗号分隔的行动建议）'
    )
    user = (
        f'目标岗位：{job_title}\n'
        f'评分：{score} 分\n'
        f'学习内容摘要（前500字）：\n{learning_content[:500]}\n\n'
        f'生成的面试题目：\n' + '\n'.join(f'{i+1}. {q}' for i, q in enumerate(questions))
    )
    text = chat(sys, user, temperature=0.6, max_tokens=800)
    if not text:
        return None

    result: dict = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if line.startswith('反馈：') or line.startswith('反馈:'):
            result['feedback'] = line.split('：', 1)[-1].split(':', 1)[-1].strip()
        elif line.startswith('优势：') or line.startswith('优势:'):
            raw = line.split('：', 1)[-1].split(':', 1)[-1].strip()
            result['strengths'] = [a.strip() for a in raw.replace('，', ',').split(',') if a.strip()]
        elif line.startswith('改进：') or line.startswith('改进:'):
            raw = line.split('：', 1)[-1].split(':', 1)[-1].strip()
            result['improvements'] = [a.strip() for a in raw.replace('，', ',').split(',') if a.strip()]
        elif line.startswith('下一步：') or line.startswith('下一步:'):
            raw = line.split('：', 1)[-1].split(':', 1)[-1].strip()
            result['next_actions'] = [a.strip() for a in raw.replace('，', ',').split(',') if a.strip()]
    return result if result.get('feedback') else None


def generate_dimension_comments(
    dimensions: list[dict],
    context_description: str,
) -> dict[str, str] | None:
    """Use LLM to generate brief comments for each scoring dimension.

    *dimensions* is a list of dicts like ``{"dimension": "...", "score": 80}``.
    Returns a mapping ``{dimension_name: comment}`` or ``None`` on failure.
    """
    sys = (
        '你是一位专业的面试评估助手。请根据各维度名称和评分，为每个维度写一句简短评语（不超过30字）。'
        '格式：每行一条，"维度名：评语"。语言使用中文。'
    )
    dim_lines = '\n'.join(f'{d["dimension"]}：{d["score"]}分' for d in dimensions)
    user = f'场景：{context_description}\n\n维度评分：\n{dim_lines}'
    text = chat(sys, user, temperature=0.5, max_tokens=600)
    if not text:
        return None
    result: dict[str, str] = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if '：' in line or ':' in line:
            sep = '：' if '：' in line else ':'
            name, comment = line.split(sep, 1)
            name = name.strip().lstrip('0123456789.、) -')
            if name and comment.strip():
                result[name] = comment.strip()
    return result if result else None
