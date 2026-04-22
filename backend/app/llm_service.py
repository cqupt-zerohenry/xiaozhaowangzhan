"""LLM service: wraps OpenAI-compatible API for text generation.

Supports any OpenAI-compatible provider (OpenAI / DeepSeek / Moonshot / etc.)
by configuring LLM_BASE_URL and LLM_API_KEY in .env.
All calls have a rule-based fallback so the system still works without an API key.
"""

from __future__ import annotations

import json
import logging
import re

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
        '给出专业、有条理的回答。如果检索内容不足以回答，可以结合你的知识补充。'
        '回答要求：'
        '1) 使用中文自然语言，控制在 3~5 句；'
        '2) 总长度尽量不超过 220 字；'
        '3) 不要使用 Markdown 标题、表格、代码块、分隔线；'
        '4) 不要输出大段清单，只保留最关键建议。'
    )
    user = f'问题：{question}\n\n检索到的知识库内容：\n{retrieved_context}'
    return chat(sys, user, temperature=0.4, max_tokens=520)


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


def _extract_json_from_text(text: str) -> dict | None:
    """Extract and parse JSON object from free-form model output."""
    if not text:
        return None
    raw = text.strip()

    # Remove markdown fence if present
    if raw.startswith('```'):
        raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.IGNORECASE)
        raw = re.sub(r'\s*```$', '', raw)

    # Try whole text first
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # Find first JSON object by brace matching
    start = raw.find('{')
    if start == -1:
        return None
    depth = 0
    for idx in range(start, len(raw)):
        ch = raw[idx]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                candidate = raw[start:idx + 1]
                try:
                    data = json.loads(candidate)
                    if isinstance(data, dict):
                        return data
                except Exception:
                    return None
    return None


def evaluate_interview_answer(
    *,
    job_title: str,
    question: str,
    answer: str,
) -> dict | None:
    """Use LLM to evaluate one interview answer with score and feedback."""
    sys = (
        '你是一位资深技术面试官。你需要客观评分并给出可执行建议。'
        '仅输出 JSON，不要输出任何额外文字。'
    )
    user = (
        '请按以下标准给出 0-100 分：\n'
        '- 40%：问题匹配度（是否答到题目核心）\n'
        '- 25%：专业深度（是否体现技术原理/方法）\n'
        '- 20%：结构表达（条理、清晰度）\n'
        '- 15%：实践与结果（项目、数据、结果）\n\n'
        f'岗位：{job_title or "目标岗位"}\n'
        f'题目：{question}\n'
        f'回答：{answer}\n\n'
        '严格输出 JSON，格式如下：\n'
        '{\n'
        '  "score": 78,\n'
        '  "feedback": "一句总体反馈（30-80字）",\n'
        '  "strengths": ["优点1", "优点2"],\n'
        '  "improvements": ["改进建议1", "改进建议2"]\n'
        '}\n'
        '要求：score 必须是整数；strengths/improvements 至少各 1 条。'
    )
    text = chat(sys, user, temperature=0.2, max_tokens=500)
    if not text:
        return None
    data = _extract_json_from_text(text)
    if not data:
        return None

    try:
        score = int(data.get('score'))
    except Exception:
        return None
    score = max(0, min(100, score))

    feedback = str(data.get('feedback') or '').strip()
    strengths = data.get('strengths') if isinstance(data.get('strengths'), list) else []
    improvements = data.get('improvements') if isinstance(data.get('improvements'), list) else []

    strengths_clean = [str(item).strip() for item in strengths if str(item).strip()]
    improvements_clean = [str(item).strip() for item in improvements if str(item).strip()]
    if not feedback:
        return None
    if not strengths_clean:
        strengths_clean = ['回答覆盖了部分核心点']
    if not improvements_clean:
        improvements_clean = ['建议增加具体案例和量化结果']

    return {
        'score': score,
        'feedback': feedback,
        'strengths': strengths_clean[:3],
        'improvements': improvements_clean[:3],
    }


def evaluate_interview_session(
    *,
    job_title: str,
    qa_items: list[dict],
) -> dict | None:
    """Use LLM to provide final interview summary and dimension scores."""
    if not qa_items:
        return None

    qa_text = '\n\n'.join(
        [
            (
                f'Q{i + 1}: {item.get("question", "")}\n'
                f'A{i + 1}: {item.get("answer", "")}\n'
                f'当前单题分：{item.get("score", 0)}'
            )
            for i, item in enumerate(qa_items)
        ]
    )
    sys = (
        '你是一位面试委员会评估官，请基于整场问答做最终评估。'
        '仅输出 JSON，不要输出任何解释文本。'
    )
    user = (
        f'岗位：{job_title or "目标岗位"}\n'
        f'题目数量：{len(qa_items)}\n\n'
        f'问答记录：\n{qa_text}\n\n'
        '请输出 JSON，格式必须为：\n'
        '{\n'
        '  "total_score": 82,\n'
        '  "overall_feedback": "总体评价（80-160字）",\n'
        '  "dimension_scores": [\n'
        '    {"dimension":"表达完整度","score":80,"comment":"..."},\n'
        '    {"dimension":"专业深度","score":84,"comment":"..."},\n'
        '    {"dimension":"逻辑条理","score":79,"comment":"..."},\n'
        '    {"dimension":"实践经验","score":76,"comment":"..."},\n'
        '    {"dimension":"综合表现","score":82,"comment":"..."}\n'
        '  ]\n'
        '}\n'
        '要求：所有 score 为 0-100 的整数，dimension_scores 必须正好 5 项。'
    )
    text = chat(sys, user, temperature=0.2, max_tokens=1200)
    if not text:
        return None
    data = _extract_json_from_text(text)
    if not data:
        return None

    try:
        total_score = int(data.get('total_score'))
    except Exception:
        return None
    total_score = max(0, min(100, total_score))
    overall_feedback = str(data.get('overall_feedback') or '').strip()
    dims = data.get('dimension_scores')
    if not overall_feedback or not isinstance(dims, list):
        return None

    dim_result: list[dict] = []
    for item in dims:
        if not isinstance(item, dict):
            continue
        name = str(item.get('dimension') or '').strip()
        comment = str(item.get('comment') or '').strip()
        try:
            score = int(item.get('score'))
        except Exception:
            continue
        if not name:
            continue
        dim_result.append({
            'dimension': name,
            'score': max(0, min(100, score)),
            'comment': comment or '基于面试回答综合评估',
        })

    if len(dim_result) < 5:
        return None

    return {
        'total_score': total_score,
        'overall_feedback': overall_feedback,
        'dimension_scores': dim_result[:5],
    }
