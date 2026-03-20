from __future__ import annotations

import hashlib
import math
import re

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.config import settings
from app.db import get_db
from app.dependencies import get_current_user
from app.models import (
    AIInterviewSession,
    AIInterviewTemplate,
    Application,
    CompanyProfile,
    Favorite,
    Job,
    KnowledgeBase,
    KnowledgeChunk,
    KnowledgeDocument,
    RecommendConfig,
    StudentIntention,
    StudentProfile,
    User,
    ViewHistory,
)
from app import llm_service
from app.rag_service import chunk_and_embed, retrieve_chunks

router = APIRouter(prefix='/ai', tags=['ai'])


def ensure_company_owner_or_admin(current_user: User, company_id: int) -> None:
    if current_user.role == 'admin':
        return
    if current_user.role == 'company' and current_user.id == company_id:
        return
    raise HTTPException(status_code=403, detail='Permission denied')


def default_question_types() -> list[str]:
    return ['技术基础', '项目经验', '场景分析', '沟通协作']


def normalize_question_types(question_types: list[str] | None) -> list[str]:
    cleaned = [item.strip() for item in (question_types or []) if item and item.strip()]
    return cleaned or default_question_types()


def extract_keywords(text: str, limit: int = 5) -> list[str]:
    english = re.findall(r'[A-Za-z][A-Za-z0-9+#.-]{1,}', text)
    chinese = re.findall(r'[\u4e00-\u9fff]{2,8}', text)
    merged = english + chinese
    seen: set[str] = set()
    result: list[str] = []
    for token in merged:
        normalized = token.strip()
        if normalized.lower() in seen:
            continue
        seen.add(normalized.lower())
        result.append(normalized)
        if len(result) >= limit:
            break
    return result


def _stable_shuffle(items: list, seed: str) -> list:
    """Deterministic shuffle based on seed for reproducible but varied output."""
    digest = hashlib.md5(seed.encode()).hexdigest()
    decorated = [(int(digest[i * 2:(i + 1) * 2], 16) if i < 16 else hash((digest, i)), v) for i, v in enumerate(items)]
    decorated.sort(key=lambda x: x[0])
    return [v for _, v in decorated]


def build_interview_questions(
    job_title: str,
    question_types: list[str],
    question_count: int,
    focus_points: list[str],
) -> list[str]:
    points = focus_points or ['岗位核心能力']
    prompts = {
        '技术基础': [
            lambda point, jt: f'请解释你对 {point} 的理解，以及它在 {jt} 中的应用。',
            lambda point, jt: f'在 {jt} 的日常工作中，{point} 最常遇到哪些技术挑战？请举例说明。',
            lambda point, jt: f'{point} 的核心原理是什么？如果向非技术人员解释，你会怎么说？',
        ],
        '项目经验': [
            lambda point, jt: f'请分享一个你在 {point} 相关项目中的具体贡献与结果。',
            lambda point, jt: f'在涉及 {point} 的项目中，你遇到过最大的技术难点是什么？如何解决的？',
            lambda point, jt: f'描述一个你主导的与 {point} 相关的项目，你做了哪些关键决策？',
        ],
        '场景分析': [
            lambda point, jt: f'如果在 {jt} 中遇到 {point} 的复杂问题，你会如何拆解和推进？',
            lambda point, jt: f'假设线上环境中 {point} 出现异常，你的排查思路是什么？',
            lambda point, jt: f'当 {point} 的需求与现有架构产生冲突时，作为 {jt} 你会如何权衡？',
        ],
        '沟通协作': [
            lambda point, jt: f'请举例说明你如何与团队协作解决 {point} 相关分歧。',
            lambda point, jt: f'在跨部门协作中，你如何向其他团队解释 {point} 的技术方案？',
            lambda point, jt: f'如果团队成员对 {point} 的实现方案意见不一致，你会如何推动达成共识？',
        ],
        '行为面试': [
            lambda point, jt: f'你曾遇到过与 {point} 相关的压力情境吗？你是如何处理的？',
            lambda point, jt: f'描述一次你在 {point} 相关任务中犯的错误，以及你从中学到了什么。',
            lambda point, jt: f'你曾在 {point} 相关的紧急任务中主动承担过额外责任吗？请具体说明。',
        ],
        '系统设计': [
            lambda point, jt: f'请设计一个与 {point} 相关的小型方案，并说明关键取舍。',
            lambda point, jt: f'如果要从零搭建一个涉及 {point} 的系统，你会如何规划技术选型与架构分层？',
            lambda point, jt: f'针对 {point}，如何设计一个兼顾可扩展性和可维护性的方案？',
        ],
        '业务理解': [
            lambda point, jt: f'如果 {point} 直接影响业务指标，你会优先关注哪些数据？',
            lambda point, jt: f'从 {jt} 的角度来看，{point} 对业务价值的核心贡献是什么？',
            lambda point, jt: f'如何衡量 {point} 相关功能的上线效果？你会设计哪些指标？',
        ],
    }

    normalized = normalize_question_types(question_types)
    seed = f'{job_title}:{"_".join(points)}:{question_count}'
    all_candidates: list[str] = []
    for index in range(max(question_count, len(normalized) * len(points))):
        q_type = normalized[index % len(normalized)]
        point = points[index % len(points)]
        builders = prompts.get(q_type, prompts['技术基础'])
        builder = builders[index % len(builders)]
        all_candidates.append(f'[{q_type}] {builder(point, job_title)}')

    shuffled = _stable_shuffle(all_candidates, seed)
    seen: set[str] = set()
    questions: list[str] = []
    for q in shuffled:
        if q not in seen:
            seen.add(q)
            questions.append(q)
            if len(questions) >= question_count:
                break

    while len(questions) < question_count:
        q_type = normalized[len(questions) % len(normalized)]
        point = points[len(questions) % len(points)]
        fallback = f'[{q_type}] 请结合你对 {point} 的理解，谈谈你能为 {job_title} 岗位带来什么价值。'
        questions.append(fallback)

    return questions


def build_user_job_map(
    applications: list,
    views: list | None = None,
    favorites: list | None = None,
) -> dict[int, dict[int, float]]:
    """Build user-job weighted interaction matrix.

    Weights: application=1.0, favorite=0.6, view=0.3 (diminishing implicit signals).
    """
    matrix: dict[int, dict[int, float]] = {}
    for app in applications:
        matrix.setdefault(app.student_id, {})
        matrix[app.student_id][app.job_id] = 1.0
    if favorites:
        for fav in favorites:
            matrix.setdefault(fav.user_id, {})
            if fav.job_id not in matrix[fav.user_id]:
                matrix[fav.user_id][fav.job_id] = 0.6
    if views:
        seen: set[tuple[int, int]] = set()
        for v in views:
            key = (v.user_id, v.job_id)
            if key in seen:
                continue
            seen.add(key)
            matrix.setdefault(v.user_id, {})
            if v.job_id not in matrix[v.user_id]:
                matrix[v.user_id][v.job_id] = 0.3
    return matrix


def cosine_similarity_weighted(a: dict[int, float], b: dict[int, float]) -> float:
    """Cosine similarity on weighted interaction vectors."""
    if not a or not b:
        return 0.0
    common_keys = set(a.keys()) & set(b.keys())
    if not common_keys:
        return 0.0
    dot = sum(a[k] * b[k] for k in common_keys)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def compute_collaborative_scores(
    applications: list,
    jobs: list[Job],
    target_student_id: int | None,
    views: list | None = None,
    favorites: list | None = None,
) -> dict[int, int]:
    """Compute collaborative filtering scores using weighted implicit + explicit signals."""
    scores: dict[int, float] = {job.id: 0.0 for job in jobs}
    if not applications and not views and not favorites:
        return {job.id: 0 for job in jobs}

    user_job_map = build_user_job_map(applications, views, favorites)

    if target_student_id and target_student_id in user_job_map:
        target_prefs = user_job_map[target_student_id]
        for student_id, prefs in user_job_map.items():
            if student_id == target_student_id:
                continue
            sim = cosine_similarity_weighted(target_prefs, prefs)
            if sim <= 0:
                continue
            for job_id, weight in prefs.items():
                if job_id not in target_prefs:
                    scores[job_id] += sim * weight * 100
    else:
        # Cold start fallback: global popularity
        counts: dict[int, float] = {}
        for app in applications:
            counts[app.job_id] = counts.get(app.job_id, 0) + 1.0
        if favorites:
            for fav in favorites:
                counts[fav.job_id] = counts.get(fav.job_id, 0) + 0.6
        max_count = max(counts.values()) if counts else 1
        return {job_id: int((count / max_count) * 100) for job_id, count in counts.items()}

    max_score = max(scores.values()) if scores else 0
    if max_score <= 0:
        return {job.id: 0 for job in jobs}
    return {job_id: int((score / max_score) * 100) for job_id, score in scores.items()}


# ---------------------------------------------------------------------------
# Knowledge Base CRUD
# ---------------------------------------------------------------------------

def _ensure_kb_owner(kb: KnowledgeBase, current_user: User) -> None:
    if current_user.role == 'admin':
        return
    if kb.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail='Permission denied')


def _load_kb_chunks(db: Session, kb_id: int) -> tuple[list[str], list[list[float] | None], list[KnowledgeChunk]]:
    """Load all chunk texts, embeddings, and ORM objects for a knowledge base."""
    chunks = db.scalars(
        select(KnowledgeChunk).where(KnowledgeChunk.kb_id == kb_id).order_by(KnowledgeChunk.id)
    ).all()
    texts = [c.content for c in chunks]
    embeddings = [c.embedding for c in chunks]
    return texts, embeddings, chunks


def _retrieve_from_kb(
    query: str, db: Session, kb_id: int, top_k: int = 5,
) -> list[schemas.RagSourceItem]:
    """Retrieve relevant chunks from a knowledge base and return as source items."""
    texts, embeddings, chunks = _load_kb_chunks(db, kb_id)
    if not texts:
        return []
    results = retrieve_chunks(query, texts, embeddings, top_k=top_k)
    sources: list[schemas.RagSourceItem] = []
    for idx, score in results:
        chunk = chunks[idx]
        doc = db.get(KnowledgeDocument, chunk.document_id)
        sources.append(schemas.RagSourceItem(
            chunk_content=chunk.content,
            document_title=doc.title if doc else '',
            relevance_score=round(score, 3),
        ))
    return sources


@router.post('/knowledge-bases', response_model=schemas.KnowledgeBaseOut)
def create_knowledge_base(
    payload: schemas.KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.KnowledgeBaseOut:
    if current_user.role not in {'student', 'company', 'admin'}:
        raise HTTPException(status_code=403, detail='Permission denied')

    record = KnowledgeBase(
        owner_id=current_user.id,
        owner_role=current_user.role,
        name=payload.name,
        description=payload.description,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return schemas.KnowledgeBaseOut.model_validate(record)


@router.get('/knowledge-bases', response_model=list[schemas.KnowledgeBaseOut])
def list_knowledge_bases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[schemas.KnowledgeBaseOut]:
    stmt = select(KnowledgeBase)
    if current_user.role != 'admin':
        stmt = stmt.where(KnowledgeBase.owner_id == current_user.id)
    rows = db.scalars(stmt.order_by(KnowledgeBase.id.desc())).all()
    return [schemas.KnowledgeBaseOut.model_validate(r) for r in rows]


@router.delete('/knowledge-bases/{kb_id}')
def delete_knowledge_base(
    kb_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    kb = db.get(KnowledgeBase, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail='Knowledge base not found')
    _ensure_kb_owner(kb, current_user)

    # Delete chunks → documents → KB (order matters for FK constraints)
    for chunk in db.scalars(select(KnowledgeChunk).where(KnowledgeChunk.kb_id == kb_id)).all():
        db.delete(chunk)
    for doc in db.scalars(select(KnowledgeDocument).where(KnowledgeDocument.kb_id == kb_id)).all():
        db.delete(doc)
    db.delete(kb)
    db.commit()
    return {'status': 'deleted'}


@router.post('/knowledge-bases/{kb_id}/documents', response_model=schemas.KnowledgeDocumentOut)
def add_document_paste(
    kb_id: int,
    payload: schemas.KnowledgeDocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.KnowledgeDocumentOut:
    kb = db.get(KnowledgeBase, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail='Knowledge base not found')
    _ensure_kb_owner(kb, current_user)

    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail='Content cannot be empty')

    doc = KnowledgeDocument(
        kb_id=kb_id,
        title=payload.title,
        source_type='paste',
        raw_content=content,
        status='processing',
    )
    db.add(doc)
    db.flush()

    # Chunk and embed
    pairs = chunk_and_embed(content, settings.rag_chunk_size, settings.rag_chunk_overlap)
    for i, (chunk_text_content, embedding) in enumerate(pairs):
        db.add(KnowledgeChunk(
            document_id=doc.id,
            kb_id=kb_id,
            chunk_index=i,
            content=chunk_text_content,
            embedding=embedding,
            token_count=len(chunk_text_content),
        ))
    doc.chunk_count = len(pairs)
    doc.status = 'ready'
    db.commit()
    db.refresh(doc)
    return schemas.KnowledgeDocumentOut.model_validate(doc)


@router.post('/knowledge-bases/{kb_id}/documents/upload', response_model=schemas.KnowledgeDocumentOut)
async def upload_document(
    kb_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.KnowledgeDocumentOut:
    kb = db.get(KnowledgeBase, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail='Knowledge base not found')
    _ensure_kb_owner(kb, current_user)

    if not file.filename:
        raise HTTPException(status_code=400, detail='No file provided')
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in {'txt', 'md', 'text'}:
        raise HTTPException(status_code=400, detail='Only .txt and .md files are supported')

    raw_bytes = await file.read()
    content = raw_bytes.decode('utf-8', errors='ignore').strip()
    if not content:
        raise HTTPException(status_code=400, detail='File is empty')

    doc = KnowledgeDocument(
        kb_id=kb_id,
        title=file.filename,
        source_type='upload',
        raw_content=content,
        status='processing',
    )
    db.add(doc)
    db.flush()

    pairs = chunk_and_embed(content, settings.rag_chunk_size, settings.rag_chunk_overlap)
    for i, (chunk_text_content, embedding) in enumerate(pairs):
        db.add(KnowledgeChunk(
            document_id=doc.id,
            kb_id=kb_id,
            chunk_index=i,
            content=chunk_text_content,
            embedding=embedding,
            token_count=len(chunk_text_content),
        ))
    doc.chunk_count = len(pairs)
    doc.status = 'ready'
    db.commit()
    db.refresh(doc)
    return schemas.KnowledgeDocumentOut.model_validate(doc)


@router.get('/knowledge-bases/{kb_id}/documents', response_model=list[schemas.KnowledgeDocumentOut])
def list_documents(
    kb_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[schemas.KnowledgeDocumentOut]:
    kb = db.get(KnowledgeBase, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail='Knowledge base not found')
    _ensure_kb_owner(kb, current_user)

    rows = db.scalars(
        select(KnowledgeDocument).where(KnowledgeDocument.kb_id == kb_id).order_by(KnowledgeDocument.id.desc())
    ).all()
    return [schemas.KnowledgeDocumentOut.model_validate(r) for r in rows]


@router.delete('/knowledge-bases/{kb_id}/documents/{doc_id}')
def delete_document(
    kb_id: int,
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    kb = db.get(KnowledgeBase, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail='Knowledge base not found')
    _ensure_kb_owner(kb, current_user)

    doc = db.get(KnowledgeDocument, doc_id)
    if not doc or doc.kb_id != kb_id:
        raise HTTPException(status_code=404, detail='Document not found')

    for chunk in db.scalars(select(KnowledgeChunk).where(KnowledgeChunk.document_id == doc_id)).all():
        db.delete(chunk)
    db.delete(doc)
    db.commit()
    return {'status': 'deleted'}


# ---------------------------------------------------------------------------
# AI Job Assistant (floating ball chat)
# ---------------------------------------------------------------------------

@router.post('/job-assistant', response_model=schemas.JobAssistantResponse)
def job_assistant(
    payload: schemas.JobAssistantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.JobAssistantResponse:
    """Conversational AI job recommendation assistant backed by RAG on the jobs KB."""
    if current_user.role not in {'student', 'admin'}:
        raise HTTPException(status_code=403, detail='Only students can use job assistant')

    # 1. Load student profile + intention
    profile = db.get(StudentProfile, current_user.id)
    intention = db.get(StudentIntention, current_user.id)

    profile_text = ''
    if profile:
        profile_text = (
            f'姓名：{profile.name}，学校：{profile.school}，专业：{profile.major}，'
            f'年级：{profile.grade}，技能：{", ".join(profile.skills or [])}'
        )
    if intention:
        parts = []
        if intention.expected_job:
            parts.append(f'期望岗位={intention.expected_job}')
        if intention.expected_city:
            parts.append(f'期望城市={intention.expected_city}')
        if intention.expected_salary:
            parts.append(f'期望薪资={intention.expected_salary}')
        if intention.expected_industry:
            parts.append(f'期望行业={intention.expected_industry}')
        if parts:
            profile_text += '\n求职意向：' + '，'.join(parts)

    # 2. Retrieve relevant job chunks from system jobs KB
    from app.job_indexer import SYSTEM_JOBS_KB_NAME
    jobs_kb = db.scalar(
        select(KnowledgeBase).where(
            KnowledgeBase.name == SYSTEM_JOBS_KB_NAME,
            KnowledgeBase.owner_role == 'system',
        )
    )

    sources: list[tuple[str, float, int]] = []  # (content, score, document_id)
    if jobs_kb:
        texts, embeddings, chunks = _load_kb_chunks(db, jobs_kb.id)
        if texts:
            search_query = payload.message
            if profile and profile.skills:
                search_query += ' ' + ' '.join(profile.skills[:5])
            if intention and intention.expected_job:
                search_query += ' ' + intention.expected_job

            results = retrieve_chunks(search_query, texts, embeddings, top_k=8)
            for idx, score in results:
                chunk = chunks[idx]
                sources.append((chunk.content, score, chunk.document_id))

    # 3. Extract job details from matched chunks
    matched_doc_ids = list(dict.fromkeys(s[2] for s in sources))  # preserve order, deduplicate
    recommended_jobs: list[schemas.JobAssistantJobItem] = []
    job_context_parts: list[str] = []

    for doc_id in matched_doc_ids[:6]:
        doc = db.get(KnowledgeDocument, doc_id)
        if not doc or not doc.title.startswith('job:'):
            continue
        try:
            job_id = int(doc.title.split(':')[1])
        except (ValueError, IndexError):
            continue
        job = db.get(Job, job_id)
        if not job or job.status != 'active':
            continue
        company = db.get(CompanyProfile, job.company_id)
        company_name = company.company_name if company else ''
        recommended_jobs.append(schemas.JobAssistantJobItem(
            job_id=job.id,
            job_name=job.job_name,
            company_name=company_name,
            city=job.city,
            salary=f'{job.salary_min}-{job.salary_max}',
        ))
        job_context_parts.append(
            f'【{job.job_name}】{company_name} · {job.city} · {job.salary_min}-{job.salary_max}元\n'
            f'技能要求：{"、".join(job.skill_tags or [])}\n'
            f'{(job.description or "")[:150]}'
        )

    jobs_context = '\n\n'.join(job_context_parts) if job_context_parts else '暂未检索到匹配职位。'

    # 4. Build LLM conversation
    system_prompt = (
        '你是「AI校园招聘」平台的智能求职助手。根据学生个人信息和平台职位数据，'
        '为学生提供个性化的职位推荐和求职建议。回答要简洁、友好、专业。'
        '如果推荐了职位，请说明推荐理由。语言使用中文。\n\n'
        f'【学生信息】\n{profile_text or "未完善个人信息"}\n\n'
        f'【平台匹配职位】\n{jobs_context}'
    )

    messages = [{'role': 'system', 'content': system_prompt}]
    for h in (payload.history or [])[-6:]:
        messages.append({'role': h.get('role', 'user'), 'content': h.get('content', '')})
    messages.append({'role': 'user', 'content': payload.message})

    reply = llm_service.chat_multi(messages, temperature=0.7, max_tokens=1500)
    if not reply:
        if recommended_jobs:
            job_lines = '\n'.join(
                f'- {j.job_name}（{j.company_name}，{j.city}，{j.salary}元）'
                for j in recommended_jobs
            )
            reply = f'根据您的信息，为您推荐以下职位：\n{job_lines}\n\n您可以告诉我更具体的需求，我来帮您进一步筛选。'
        else:
            reply = '您好！我是AI求职助手。请告诉我您的求职需求，比如期望的岗位类型、城市或技能方向，我来为您推荐合适的职位。'

    return schemas.JobAssistantResponse(reply=reply, recommended_jobs=recommended_jobs)


# ---------------------------------------------------------------------------
# Interview Templates
# ---------------------------------------------------------------------------

@router.post('/interview-templates', response_model=schemas.AIInterviewTemplateOut)
def create_interview_template(
    payload: schemas.AIInterviewTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.AIInterviewTemplateOut:
    if current_user.role not in {'company', 'admin'}:
        raise HTTPException(status_code=403, detail='Permission denied')

    company_id = payload.company_id or current_user.id
    ensure_company_owner_or_admin(current_user, company_id)

    company_user = db.get(User, company_id)
    if not company_user or company_user.role != 'company':
        raise HTTPException(status_code=404, detail='Company user not found')

    record = AIInterviewTemplate(
        company_id=company_id,
        name=payload.name,
        job_title=payload.job_title,
        question_types=normalize_question_types(payload.question_types),
        difficulty=payload.difficulty,
        question_count=payload.question_count,
        scoring_rules=payload.scoring_rules,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return schemas.AIInterviewTemplateOut.model_validate(record)


@router.get('/interview-templates', response_model=list[schemas.AIInterviewTemplateOut])
def list_interview_templates(
    company_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[schemas.AIInterviewTemplateOut]:
    stmt = select(AIInterviewTemplate)
    if current_user.role == 'company':
        stmt = stmt.where(AIInterviewTemplate.company_id == current_user.id)
    elif current_user.role == 'admin':
        if company_id:
            stmt = stmt.where(AIInterviewTemplate.company_id == company_id)
    else:
        raise HTTPException(status_code=403, detail='Permission denied')

    rows = db.scalars(stmt.order_by(AIInterviewTemplate.id.desc())).all()
    return [schemas.AIInterviewTemplateOut.model_validate(item) for item in rows]


@router.put('/interview-templates/{template_id}', response_model=schemas.AIInterviewTemplateOut)
def update_interview_template(
    template_id: int,
    payload: schemas.AIInterviewTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.AIInterviewTemplateOut:
    record = db.get(AIInterviewTemplate, template_id)
    if not record:
        raise HTTPException(status_code=404, detail='Interview template not found')

    ensure_company_owner_or_admin(current_user, record.company_id)

    updates = payload.model_dump(exclude_none=True)
    if 'question_types' in updates:
        updates['question_types'] = normalize_question_types(payload.question_types)

    for key, value in updates.items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return schemas.AIInterviewTemplateOut.model_validate(record)


@router.delete('/interview-templates/{template_id}')
def delete_interview_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    record = db.get(AIInterviewTemplate, template_id)
    if not record:
        raise HTTPException(status_code=404, detail='Interview template not found')
    ensure_company_owner_or_admin(current_user, record.company_id)

    db.delete(record)
    db.commit()
    return {'status': 'deleted'}


@router.post('/screening-interview', response_model=schemas.ScreeningInterviewResponse)
def screening_interview(
    payload: schemas.ScreeningInterviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.ScreeningInterviewResponse:
    if current_user.role not in {'company', 'admin'}:
        raise HTTPException(status_code=403, detail='Permission denied')

    template = db.get(AIInterviewTemplate, payload.template_id)
    if not template:
        raise HTTPException(status_code=404, detail='Interview template not found')
    ensure_company_owner_or_admin(current_user, template.company_id)

    candidate_skills = [item.strip() for item in payload.candidate_skills if item.strip()]
    summary = payload.candidate_summary.strip()
    experience = payload.candidate_experience.strip()

    focus_points = candidate_skills or extract_keywords(summary + '\n' + experience)

    # Enrich focus points with knowledge base if provided
    if payload.kb_id:
        kb = db.get(KnowledgeBase, payload.kb_id)
        if kb:
            kb_sources = _retrieve_from_kb(
                template.job_title + ' ' + ' '.join(candidate_skills),
                db, payload.kb_id, top_k=3,
            )
            kb_keywords = []
            for src in kb_sources:
                kb_keywords.extend(extract_keywords(src.chunk_content, limit=3))
            # Deduplicate and append KB-derived focus points
            existing = {fp.lower() for fp in focus_points}
            for kw in kb_keywords:
                if kw.lower() not in existing:
                    focus_points.append(kw)
                    existing.add(kw.lower())

    # Gather KB context for LLM enrichment
    kb_context = ''
    if payload.kb_id:
        kb_sources = _retrieve_from_kb(
            template.job_title + ' ' + ' '.join(candidate_skills), db, payload.kb_id, top_k=3,
        )
        kb_context = '\n'.join(s.chunk_content for s in kb_sources)

    # --- Try LLM for question generation, fallback to rule-based ---
    llm_questions = llm_service.generate_interview_questions(
        job_title=template.job_title,
        focus_points=focus_points,
        question_types=template.question_types or default_question_types(),
        question_count=template.question_count,
        context=kb_context,
    )
    questions = llm_questions or build_interview_questions(
        job_title=template.job_title,
        question_types=template.question_types or default_question_types(),
        question_count=template.question_count,
        focus_points=focus_points,
    )

    # --- Scoring (deterministic, not LLM-dependent) ---
    score = 30
    job_keywords = set(extract_keywords(template.job_title + ' ' + (template.scoring_rules or ''), limit=10))
    candidate_skill_set = {s.lower() for s in candidate_skills}
    job_keyword_lower = {k.lower() for k in job_keywords}
    matched_skill_count = len(candidate_skill_set.intersection(job_keyword_lower))
    relevance_ratio = (matched_skill_count / len(job_keyword_lower)) if job_keyword_lower else (min(1.0, len(candidate_skills) / 5) if candidate_skills else 0)
    score += int(relevance_ratio * 30)
    score += min(10, len(candidate_skills) * 2)
    summary_len = len(summary)
    score += 15 if summary_len >= 120 else 10 if summary_len >= 60 else 5 if summary_len >= 20 else 0
    experience_len = len(experience)
    score += 15 if experience_len >= 120 else 10 if experience_len >= 60 else 5 if experience_len >= 20 else 0
    score = max(0, min(98, score))

    if score >= 80:
        recommendation = '建议进入下一轮面试'
    elif score >= 65:
        recommendation = '建议人工复核后再决定'
    elif score >= 50:
        recommendation = '建议补充信息后再评估'
    else:
        recommendation = '建议暂不推进'

    # --- Try LLM for evaluation text, fallback to rule-based ---
    llm_eval = llm_service.generate_screening_evaluation(
        job_title=template.job_title,
        candidate_name=payload.candidate_name,
        candidate_skills=candidate_skills,
        candidate_summary=summary,
        candidate_experience=experience,
        score=score,
        questions=questions,
        context=kb_context,
    )
    if llm_eval:
        evaluation = llm_eval.get('evaluation', '')
        recommendation = llm_eval.get('recommendation', recommendation)
        focus_areas = llm_eval.get('focus_areas', [])
    else:
        focus_areas: list[str] = []
        unmatched = job_keyword_lower - candidate_skill_set
        if unmatched:
            focus_areas.append(f'候选人尚未覆盖的岗位关键词：{", ".join(list(unmatched)[:5])}')
        if len(candidate_skills) < 3:
            focus_areas.append('候选人技能标签偏少，建议深入了解其实际技术栈')
        if summary_len < 30:
            focus_areas.append('候选人自我概述过于简短，建议面试中重点考察表达能力')
        if experience_len < 30:
            focus_areas.append('项目经历描述不够充分，建议要求补充可量化成果')
        if not focus_areas:
            focus_areas.append('基本信息较完整，重点核验复杂场景下的问题拆解与落地能力')
        evaluation = (
            f'基于模板「{template.name}」与候选信息生成 {len(questions)} 道初筛问题。'
            f'技能岗位匹配度 {int(relevance_ratio * 100)}%，'
            f'综合得分 {score} 分。{recommendation}。'
        )

    session = AIInterviewSession(
        template_id=template.id,
        company_id=template.company_id,
        student_id=None,
        session_type='screening',
        learning_content=f'candidate={payload.candidate_name}\nsummary={summary}\nexperience={experience}',
        generated_questions=questions,
        evaluation_json={
            'score': score,
            'recommendation': recommendation,
            'focus_areas': focus_areas,
            'candidate_skills': candidate_skills,
        },
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return schemas.ScreeningInterviewResponse(
        session_id=session.id,
        template=schemas.AIInterviewTemplateOut.model_validate(template),
        questions=questions,
        evaluation=evaluation,
        score=score,
        recommendation=recommendation,
        focus_areas=focus_areas,
    )


@router.post('/student-mock-upload', response_model=schemas.StudentMockUploadResponse)
def student_mock_upload(
    payload: schemas.StudentMockUploadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.StudentMockUploadResponse:
    if current_user.role not in {'student', 'admin'}:
        raise HTTPException(status_code=403, detail='Permission denied')

    content = payload.learning_content.strip()
    focus_points = list(payload.learning_focus) if payload.learning_focus else extract_keywords(content)

    # Enrich focus points with knowledge base if provided
    if payload.kb_id:
        kb = db.get(KnowledgeBase, payload.kb_id)
        if kb and (kb.owner_id == current_user.id or current_user.role == 'admin'):
            kb_sources = _retrieve_from_kb(
                payload.job_title + ' ' + content[:200],
                db, payload.kb_id, top_k=3,
            )
            existing = {fp.lower() for fp in focus_points}
            for src in kb_sources:
                for kw in extract_keywords(src.chunk_content, limit=3):
                    if kw.lower() not in existing:
                        focus_points.append(kw)
                        existing.add(kw.lower())

    question_types = normalize_question_types(payload.question_types)

    # Gather KB context
    kb_context = ''
    if payload.kb_id:
        kb = db.get(KnowledgeBase, payload.kb_id)
        if kb and (kb.owner_id == current_user.id or current_user.role == 'admin'):
            kb_sources = _retrieve_from_kb(payload.job_title + ' ' + content[:200], db, payload.kb_id, top_k=3)
            kb_context = '\n'.join(s.chunk_content for s in kb_sources)

    # --- Try LLM for question generation, fallback to rule-based ---
    llm_questions = llm_service.generate_interview_questions(
        job_title=payload.job_title,
        focus_points=focus_points,
        question_types=question_types,
        question_count=payload.question_count,
        context=kb_context or content[:300],
    )
    questions = llm_questions or build_interview_questions(
        job_title=payload.job_title,
        question_types=question_types,
        question_count=payload.question_count,
        focus_points=focus_points,
    )

    # --- Scoring (deterministic) ---
    content_keywords = extract_keywords(content, limit=20)
    content_len = len(content)
    content_score = min(45, (40 if content_len >= 500 else 30 if content_len >= 200 else 20 if content_len >= 80 else max(5, content_len // 10)) + min(5, len(content_keywords) // 3))
    focus_in_content = sum(1 for fp in focus_points if fp.lower() in content.lower())
    focus_score = min(25, focus_in_content * 8 + len(focus_points) * 2)
    depth_score = 10 if payload.difficulty == 'hard' else 5 if payload.difficulty == 'medium' else 0
    score = max(0, min(95, 35 + content_score + focus_score + depth_score))

    # --- Try LLM for feedback, fallback to rule-based ---
    llm_fb = llm_service.generate_mock_feedback(
        job_title=payload.job_title,
        learning_content=content,
        questions=questions,
        score=score,
    )
    if llm_fb:
        feedback = llm_fb.get('feedback', f'模拟评分 {score} 分。')
        strengths = llm_fb.get('strengths', ['已完成模拟面试练习'])
        improvements = llm_fb.get('improvements', ['建议持续练习'])
        next_actions = llm_fb.get('next_actions', ['复盘本次面试题目'])
    else:
        # Rule-based fallback
        unfound_focus = [fp for fp in focus_points if fp.lower() not in content.lower()]
        strengths: list[str] = []
        if len(content_keywords) >= 5:
            strengths.append(f'学习内容涵盖多个技术关键词（{", ".join(content_keywords[:5])}），知识面较广')
        if content_len >= 200:
            strengths.append('学习笔记内容充实，体现了持续学习的投入')
        if not strengths:
            strengths.append('已迈出模拟面试的第一步，持续练习将快速提升')
        improvements: list[str] = []
        if content_len < 100:
            improvements.append('学习笔记内容偏短，建议补充更多细节')
        if unfound_focus:
            improvements.append(f'以下学习重点在内容中未充分体现：{", ".join(unfound_focus[:3])}')
        if not improvements:
            improvements.append('整体表现良好，可尝试更高难度')
        next_actions = [f'针对 {len(questions)} 道题目逐题复盘', f'阅读 {payload.job_title} 岗位 JD 对齐差距']
        feedback_parts = [f'模拟评分 {score} 分。']
        feedback_parts.append('整体掌握较好，建议专项突破。' if score >= 80 else '基础尚可，加强量化表达。' if score >= 60 else '建议补充学习后重新模拟。')
        feedback = ''.join(feedback_parts)

    student_id = current_user.id if current_user.role == 'student' else None
    session = AIInterviewSession(
        template_id=None,
        company_id=None,
        student_id=student_id,
        session_type='mock',
        learning_content=content,
        generated_questions=questions,
        evaluation_json={
            'score': score,
            'feedback': feedback,
            'strengths': strengths,
            'improvements': improvements,
            'next_actions': next_actions,
            'focus_points': focus_points,
        },
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return schemas.StudentMockUploadResponse(
        session_id=session.id,
        questions=questions,
        feedback=feedback,
        strengths=strengths,
        improvements=improvements,
        next_actions=next_actions,
    )


@router.get('/interview-sessions', response_model=list[schemas.AIInterviewSessionOut])
def list_interview_sessions(
    session_type: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[schemas.AIInterviewSessionOut]:
    stmt = select(AIInterviewSession)
    if current_user.role == 'student':
        stmt = stmt.where(AIInterviewSession.student_id == current_user.id)
    elif current_user.role == 'company':
        stmt = stmt.where(AIInterviewSession.company_id == current_user.id)
    elif current_user.role != 'admin':
        raise HTTPException(status_code=403, detail='Permission denied')

    if session_type:
        stmt = stmt.where(AIInterviewSession.session_type == session_type)

    rows = db.scalars(stmt.order_by(AIInterviewSession.id.desc()).limit(limit)).all()
    return [schemas.AIInterviewSessionOut.model_validate(item) for item in rows]


@router.post('/job-recommend', response_model=schemas.JobRecommendResponse)
def job_recommend(
    payload: schemas.JobMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.JobRecommendResponse:
    if payload.student_id and current_user.role == 'student' and current_user.id != payload.student_id:
        raise HTTPException(status_code=403, detail='Permission denied')

    student = db.get(StudentProfile, payload.student_id) if payload.student_id else None
    skills = (student.skills if student else None) or payload.skills
    intention = db.get(StudentIntention, payload.student_id) if payload.student_id else None

    jobs = db.scalars(select(Job).where(Job.status == 'active')).all()
    applications = db.scalars(select(Application)).all()
    views = db.scalars(select(ViewHistory)).all()
    favorites = db.scalars(select(Favorite)).all()
    collab_scores = compute_collaborative_scores(
        applications, jobs, payload.student_id,
        views=views, favorites=favorites,
    )

    rec_config = db.scalar(select(RecommendConfig).order_by(RecommendConfig.id.desc()))
    collab_w = rec_config.collaborative_weight if rec_config else 0.4
    content_w = rec_config.content_weight if rec_config else 0.6

    results: list[schemas.JobRecommendResult] = []

    # Normalize student skills to lowercase for case-insensitive matching
    skills_lower = {s.lower() for s in skills}

    for job in jobs:
        job_skills = job.skill_tags or []
        job_skills_lower = {s.lower() for s in job_skills}
        matched = [s for s in job_skills if s.lower() in skills_lower]
        missing = [s for s in job_skills if s.lower() not in skills_lower]

        # Content score: skill (0-50) + city (0-20) + industry (0-15) + salary (0-15)
        skill_score = int((len(matched) / max(len(job_skills), 1)) * 50)

        city_bonus = 0
        if intention and intention.expected_city:
            city_bonus = 20 if intention.expected_city in (job.city or '') or (job.city or '') in intention.expected_city else 0

        industry_bonus = 0
        company = db.get(CompanyProfile, job.company_id)
        if intention and company and intention.expected_industry:
            industry_bonus = 15 if company.industry == intention.expected_industry else 0

        salary_bonus = 0
        if intention and intention.expected_salary:
            try:
                expected = int(re.sub(r'[^\d]', '', intention.expected_salary) or '0')
                if expected and job.salary_min <= expected <= job.salary_max:
                    salary_bonus = 15
                elif expected and job.salary_max >= expected:
                    salary_bonus = 8
            except (ValueError, TypeError):
                pass

        content_score = min(100, skill_score + city_bonus + industry_bonus + salary_bonus)
        collaborative_score = collab_scores.get(job.id, 0)
        final_score = int(collab_w * collaborative_score + content_w * content_score)

        # Build explainable reason
        reasons = []
        if matched:
            reasons.append(f'技能匹配 {len(matched)}/{len(job_skills)}')
        if city_bonus:
            reasons.append('城市匹配')
        if industry_bonus:
            reasons.append('行业匹配')
        if salary_bonus:
            reasons.append('薪资范围匹配')
        reason = '、'.join(reasons) + f'，综合得分 {final_score}' if reasons else f'综合得分 {final_score}'

        results.append(
            schemas.JobRecommendResult(
                job_id=job.id,
                job_name=job.job_name,
                final_score=final_score,
                content_score=content_score,
                collaborative_score=collaborative_score,
                matched_skills=matched,
                missing_skills=missing,
                reason=reason,
            )
        )

    results.sort(key=lambda item: item.final_score, reverse=True)
    return schemas.JobRecommendResponse(matches=results)


@router.post('/job-match', response_model=schemas.JobRecommendResponse)
def job_match(
    payload: schemas.JobMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.JobRecommendResponse:
    return job_recommend(payload, db, current_user)


@router.post('/resume-optimize')
def resume_optimize(
    payload: schemas.ResumeOptimizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.ResumeOptimizeResponse:
    """Generate AI-powered resume optimization suggestions based on a target job."""
    profile = db.get(StudentProfile, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail='Student profile not found')

    skills = profile.skills or []
    projects = profile.projects or []
    bio = profile.bio or ''
    resume_text = (
        f'技能：{", ".join(skills)}\n'
        f'项目经历：{", ".join(projects)}\n'
        f'自我评价：{bio}'
    )

    llm_result = llm_service.chat(
        system_prompt=(
            '你是一位资深的简历优化顾问。请根据学生的简历信息和目标岗位，给出具体的优化建议。\n'
            '输出格式（每项一行）：\n'
            '总评：（一句话总评）\n'
            '优势：（逗号分隔）\n'
            '改进建议：（逗号分隔，每条要具体可操作）\n'
            '缺失技能：（逗号分隔，建议补充的技能）\n'
            '话术优化：（对自我评价的改写建议）'
        ),
        user_prompt=f'目标岗位：{payload.job_title}\n\n当前简历：\n{resume_text}',
        temperature=0.5,
        max_tokens=1200,
    )

    if llm_result:
        result: dict = {'summary': '', 'strengths': [], 'suggestions': [], 'missing_skills': [], 'bio_rewrite': ''}
        for line in llm_result.strip().splitlines():
            line = line.strip()
            val = line.split('：', 1)[-1].split(':', 1)[-1].strip() if '：' in line or ':' in line else ''
            if line.startswith('总评'):
                result['summary'] = val
            elif line.startswith('优势'):
                result['strengths'] = [s.strip() for s in val.replace('，', ',').split(',') if s.strip()]
            elif line.startswith('改进建议'):
                result['suggestions'] = [s.strip() for s in val.replace('，', ',').split(',') if s.strip()]
            elif line.startswith('缺失技能'):
                result['missing_skills'] = [s.strip() for s in val.replace('，', ',').split(',') if s.strip()]
            elif line.startswith('话术优化'):
                result['bio_rewrite'] = val
        return schemas.ResumeOptimizeResponse(**result)

    # Rule-based fallback
    job_kw = set(extract_keywords(payload.job_title, limit=8))
    skill_lower = {s.lower() for s in skills}
    missing = [k for k in job_kw if k.lower() not in skill_lower]
    return schemas.ResumeOptimizeResponse(
        summary=f'你的简历包含 {len(skills)} 项技能，与目标岗位「{payload.job_title}」有一定匹配度。',
        strengths=[f'已具备 {len(skills)} 项技能'] if skills else ['建议先完善技能标签'],
        suggestions=['在项目经历中添加量化指标（如提升了 XX% 性能）', '将自我评价与目标岗位关键词对齐', '补充实习或竞赛经历增强竞争力'],
        missing_skills=missing or ['建议查看目标岗位 JD 补充技能'],
        bio_rewrite='',
    )


@router.post('/interview', response_model=schemas.InterviewResponse)
def interview(
    payload: schemas.InterviewRequest,
    _: User = Depends(get_current_user),
) -> schemas.InterviewResponse:
    skill_focus = payload.skills or ['系统设计', '问题排查', '团队协作']
    jt = payload.job_title or '目标岗位'
    count = max(4, len(skill_focus) + 1)

    llm_questions = llm_service.generate_interview_questions(
        job_title=jt,
        focus_points=skill_focus,
        question_types=['技术基础', '项目经验', '场景分析', '沟通协作'],
        question_count=count,
    )
    questions = llm_questions or build_interview_questions(
        job_title=jt,
        question_types=['技术基础', '项目经验', '场景分析', '沟通协作'],
        question_count=count,
        focus_points=skill_focus,
    )
    evaluation = (
        f'针对「{jt}」岗位，围绕 {", ".join(skill_focus[:3])} 等方向生成了 {len(questions)} 道面试题。'
        f'建议重点关注候选人的技术深度、项目落地能力和团队协作表达。'
    )
    return schemas.InterviewResponse(questions=questions, evaluation=evaluation)


# Knowledge base for RAG responses, keyed by domain keywords
_RAG_KNOWLEDGE: dict[str, dict] = {
    'sre': {
        'answer': 'SRE（站点可靠性工程）是将软件工程方法应用于运维的实践。核心目标是通过自动化和工程化手段保障系统可靠性。建议从 Linux 基础开始，逐步掌握容器化、编排和可观测性技术栈，同时培养故障排查和容量规划能力。',
        'learning_path': ['Linux 系统基础', '计算机网络', 'Shell 脚本与自动化', 'Docker 容器技术', 'Kubernetes 集群管理', 'Prometheus + Grafana 监控', 'CI/CD 流水线', '故障排查与 SLO 体系'],
        'skill_tree': ['Linux → 网络 → Shell → 自动化', 'Docker → Kubernetes → Service Mesh', 'Prometheus → Grafana → OpenTelemetry → 告警体系'],
    },
    'devops': {
        'answer': 'DevOps 强调开发与运维的协同融合，核心是通过自动化交付流水线实现快速、可靠的软件发布。建议掌握 CI/CD 工具链、基础设施即代码（IaC）和容器编排技术。',
        'learning_path': ['Git 版本管理', 'CI/CD 工具（Jenkins/GitHub Actions）', 'Docker 容器化', 'Kubernetes 编排', 'Terraform/Ansible IaC', '日志与监控体系', '安全扫描与合规'],
        'skill_tree': ['Git → CI/CD → 自动化测试', 'Docker → K8s → Helm → ArgoCD', 'Terraform → Ansible → 基础设施自动化'],
    },
    '后端': {
        'answer': '后端开发需要扎实的编程基础和系统设计能力。建议从一门主力语言（Java/Python/Go）出发，掌握 Web 框架、数据库设计、缓存和消息队列，逐步深入分布式系统和微服务架构。',
        'learning_path': ['编程语言基础（Java/Python/Go）', 'Web 框架（Spring Boot/FastAPI/Gin）', 'MySQL 数据库设计与优化', 'Redis 缓存与数据结构', 'RESTful API 设计', '消息队列（RabbitMQ/Kafka）', '微服务与分布式系统', '性能调优与压测'],
        'skill_tree': ['编程基础 → Web 框架 → ORM → API 设计', 'MySQL → Redis → 消息队列 → 分布式', '单体架构 → 微服务 → 容器化部署'],
    },
    '前端': {
        'answer': '前端开发需要掌握 HTML/CSS/JavaScript 三大基础，然后深入现代框架和工程化体系。建议选择 Vue 或 React 作为主力框架，同时关注性能优化和用户体验。',
        'learning_path': ['HTML5 + CSS3 基础', 'JavaScript ES6+ 核心', 'Vue 3 / React 框架', '组件化与状态管理', '前端工程化（Webpack/Vite）', 'TypeScript', '性能优化与体验', '移动端适配'],
        'skill_tree': ['HTML/CSS → JavaScript → TypeScript', 'Vue/React → 状态管理 → 路由 → SSR', '工程化 → 构建优化 → 监控 → 性能'],
    },
    'ai': {
        'answer': 'AI/机器学习工程师需要数学基础、编程能力和算法理论兼备。建议从 Python 和数学基础开始，掌握经典机器学习算法，再深入深度学习和特定领域（NLP/CV）。',
        'learning_path': ['Python 编程与数据处理', '线性代数与概率统计', '经典机器学习算法', 'PyTorch / TensorFlow', '深度学习（CNN/RNN/Transformer）', 'NLP 或计算机视觉', '模型部署与 MLOps', '大语言模型应用'],
        'skill_tree': ['Python → NumPy/Pandas → 数据分析', 'ML 基础 → 深度学习 → Transformer', '模型训练 → 评估 → 部署 → 迭代'],
    },
}

_RAG_DEFAULT = {
    'answer': '建议从岗位核心技能出发，结合行业需求制定学习路径。先打好理论基础，再通过项目实践巩固，最后关注行业前沿动态持续提升。',
    'learning_path': ['岗位核心技能梳理', '基础理论学习', '动手项目实践', '开源项目参与', '技术博客输出', '模拟面试训练'],
    'skill_tree': ['基础理论 → 核心技能 → 项目实践', '学习输入 → 实践输出 → 持续迭代'],
}


@router.post('/rag', response_model=schemas.RagResponse)
def rag(
    payload: schemas.RagRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.RagResponse:
    question = payload.question.strip()
    question_lower = question.lower()
    top_k = payload.top_k or settings.rag_top_k

    # --- 1. Try knowledge base retrieval ---
    sources: list[schemas.RagSourceItem] = []
    if payload.kb_id:
        kb = db.get(KnowledgeBase, payload.kb_id)
        if kb:
            _ensure_kb_owner(kb, current_user)
            sources = _retrieve_from_kb(question, db, payload.kb_id, top_k=top_k)
    else:
        # Search across all user's knowledge bases
        user_kbs = db.scalars(
            select(KnowledgeBase).where(KnowledgeBase.owner_id == current_user.id)
        ).all()
        for kb in user_kbs:
            sources.extend(_retrieve_from_kb(question, db, kb.id, top_k=top_k))
        sources.sort(key=lambda s: s.relevance_score, reverse=True)
        sources = sources[:top_k]

    # --- 2. Build answer ---
    # Fallback knowledge for learning_path/skill_tree
    fallback = _RAG_DEFAULT
    for keyword, knowledge in _RAG_KNOWLEDGE.items():
        if keyword.lower() in question_lower:
            fallback = knowledge
            break

    if sources:
        retrieved_text = '\n\n'.join(f'【{s.document_title}】{s.chunk_content}' for s in sources[:5])
        llm_answer = llm_service.generate_rag_answer(question, retrieved_text)
        answer = llm_answer or (
            f'根据知识库检索到 {len(sources)} 条相关内容：\n\n{retrieved_text}'
        )
    else:
        llm_answer = llm_service.chat(
            '你是校园招聘平台的职业规划顾问，请用中文回答用户的职业相关问题。',
            question,
            max_tokens=1000,
        )
        answer = llm_answer or fallback['answer']

    # Try LLM to generate personalized learning path from KB + question
    learning_path = fallback['learning_path']
    skill_tree = fallback['skill_tree']
    if sources:
        path_text = llm_service.chat(
            '你是职业规划顾问。请根据知识库内容和问题，生成学习路径和技能树。\n'
            '输出格式（严格按行）：\n学习路径：步骤1,步骤2,步骤3,...\n技能树：分支1,分支2,...',
            f'问题：{question}\n知识库内容：\n' + '\n'.join(s.chunk_content[:200] for s in sources[:3]),
            max_tokens=400,
        )
        if path_text:
            for line in path_text.strip().splitlines():
                line = line.strip()
                if line.startswith('学习路径'):
                    items = [x.strip() for x in line.split('：', 1)[-1].replace('，', ',').split(',') if x.strip()]
                    if items:
                        learning_path = items
                elif line.startswith('技能树'):
                    items = [x.strip() for x in line.split('：', 1)[-1].replace('，', ',').split(',') if x.strip()]
                    if items:
                        skill_tree = items

    return schemas.RagResponse(
        answer=answer,
        learning_path=learning_path,
        skill_tree=skill_tree,
        sources=sources,
    )


@router.post('/mock-interview', response_model=schemas.MockInterviewResponse)
def mock_interview(
    payload: schemas.MockInterviewRequest,
    _: User = Depends(get_current_user),
) -> schemas.MockInterviewResponse:
    jt = payload.job_title or '目标岗位'
    focus = extract_keywords(jt, limit=3) or ['岗位核心能力']

    llm_questions = llm_service.generate_interview_questions(
        job_title=jt,
        focus_points=focus,
        question_types=['技术基础', '场景分析', '行为面试'],
        question_count=4,
    )
    questions = llm_questions or build_interview_questions(
        job_title=jt,
        question_types=['技术基础', '场景分析', '行为面试'],
        question_count=4,
        focus_points=focus,
    )
    feedback = (
        f'以上为针对「{jt}」的模拟面试题目。'
        f'回答时建议：(1) 使用 STAR 法则组织项目经验；'
        f'(2) 用具体数据量化成果；'
        f'(3) 场景题先明确问题边界再给出方案。'
    )
    return schemas.MockInterviewResponse(questions=questions, feedback=feedback)
