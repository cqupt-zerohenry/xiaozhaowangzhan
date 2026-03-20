"""Auto-index job postings into a system-level knowledge base for RAG retrieval.

When a company creates or updates a job, this module chunks the job text,
embeds it via the local sentence-transformers model, and stores the chunks
in a dedicated system KB so the AI job assistant can retrieve them.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import CompanyProfile, Job, KnowledgeBase, KnowledgeChunk, KnowledgeDocument
from app.rag_service import chunk_and_embed

logger = logging.getLogger(__name__)

SYSTEM_JOBS_KB_NAME = '__jobs_kb__'


def _get_or_create_jobs_kb(db: Session) -> KnowledgeBase:
    """Get the system-level jobs knowledge base, creating it if needed."""
    kb = db.scalar(
        select(KnowledgeBase).where(
            KnowledgeBase.name == SYSTEM_JOBS_KB_NAME,
            KnowledgeBase.owner_role == 'system',
        )
    )
    if not kb:
        kb = KnowledgeBase(
            owner_id=0,
            owner_role='system',
            name=SYSTEM_JOBS_KB_NAME,
            description='系统岗位知识库（自动生成，用于 AI 求职助手检索）',
        )
        db.add(kb)
        db.flush()
    return kb


def index_job_to_kb(job: Job, db: Session) -> None:
    """Chunk and embed a job posting into the system jobs KB.

    If the job was previously indexed, old chunks are replaced.
    """
    kb = _get_or_create_jobs_kb(db)
    doc_title = f'job:{job.id}'

    # Remove old document + chunks for this job
    old_doc = db.scalar(
        select(KnowledgeDocument).where(
            KnowledgeDocument.kb_id == kb.id,
            KnowledgeDocument.title == doc_title,
        )
    )
    if old_doc:
        for chunk in db.scalars(
            select(KnowledgeChunk).where(KnowledgeChunk.document_id == old_doc.id)
        ).all():
            db.delete(chunk)
        db.delete(old_doc)
        db.flush()

    # Build full text for the job
    skills_str = '、'.join(job.skill_tags or [])
    company = db.get(CompanyProfile, job.company_id)
    company_name = company.company_name if company else ''
    company_industry = company.industry if company else ''

    full_text = (
        f'职位名称：{job.job_name}\n'
        f'公司：{company_name}\n'
        f'行业：{company_industry}\n'
        f'类型：{job.job_type}\n'
        f'城市：{job.city}\n'
        f'薪资：{job.salary_min}-{job.salary_max}元\n'
        f'学历要求：{job.education}\n'
        f'技能要求：{skills_str}\n\n'
        f'职位描述：\n{job.description or ""}\n\n'
        f'任职要求：\n{job.requirement or ""}'
    )

    # Create document and chunks
    doc = KnowledgeDocument(
        kb_id=kb.id,
        title=doc_title,
        source_type='auto',
        raw_content=full_text,
        status='processing',
    )
    db.add(doc)
    db.flush()

    pairs = chunk_and_embed(full_text, settings.rag_chunk_size, settings.rag_chunk_overlap)
    for i, (chunk_content, embedding) in enumerate(pairs):
        db.add(KnowledgeChunk(
            document_id=doc.id,
            kb_id=kb.id,
            chunk_index=i,
            content=chunk_content,
            embedding=embedding,
            token_count=len(chunk_content),
        ))
    doc.chunk_count = len(pairs)
    doc.status = 'ready'

    logger.info('Indexed job %s (%s) into KB: %d chunks', job.id, job.job_name, len(pairs))


def remove_job_from_kb(job_id: int, db: Session) -> None:
    """Remove a job's chunks from the system KB (called on job deletion)."""
    kb = db.scalar(
        select(KnowledgeBase).where(
            KnowledgeBase.name == SYSTEM_JOBS_KB_NAME,
            KnowledgeBase.owner_role == 'system',
        )
    )
    if not kb:
        return
    doc_title = f'job:{job_id}'
    doc = db.scalar(
        select(KnowledgeDocument).where(
            KnowledgeDocument.kb_id == kb.id,
            KnowledgeDocument.title == doc_title,
        )
    )
    if doc:
        for chunk in db.scalars(
            select(KnowledgeChunk).where(KnowledgeChunk.document_id == doc.id)
        ).all():
            db.delete(chunk)
        db.delete(doc)
