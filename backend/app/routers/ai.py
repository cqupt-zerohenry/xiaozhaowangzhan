from __future__ import annotations

import math
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.db import get_db
from app.dependencies import get_current_user
from app.models import (
    AIInterviewSession,
    AIInterviewTemplate,
    Application,
    CompanyProfile,
    Job,
    RecommendConfig,
    StudentIntention,
    StudentProfile,
    User,
)

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


def build_interview_questions(
    job_title: str,
    question_types: list[str],
    question_count: int,
    focus_points: list[str],
) -> list[str]:
    points = focus_points or ['岗位核心能力']
    prompts = {
        '技术基础': lambda point: f'请解释你对 {point} 的理解，以及它在 {job_title} 中的应用。',
        '项目经验': lambda point: f'请分享一个你在 {point} 相关项目中的具体贡献与结果。',
        '场景分析': lambda point: f'如果在 {job_title} 中遇到 {point} 的复杂问题，你会如何拆解和推进？',
        '沟通协作': lambda point: f'请举例说明你如何与团队协作解决 {point} 相关分歧。',
        '行为面试': lambda point: f'你曾遇到过与 {point} 相关的压力情境吗？你是如何处理的？',
        '系统设计': lambda point: f'请设计一个与 {point} 相关的小型方案，并说明关键取舍。',
        '业务理解': lambda point: f'如果 {point} 直接影响业务指标，你会优先关注哪些数据？',
    }

    normalized = normalize_question_types(question_types)
    questions: list[str] = []
    for index in range(question_count):
        q_type = normalized[index % len(normalized)]
        point = points[index % len(points)]
        builder = prompts.get(q_type, prompts['技术基础'])
        questions.append(f'[{q_type}] {builder(point)}')
    return questions


def build_user_job_map(applications: list[Application]) -> dict[int, set[int]]:
    matrix: dict[int, set[int]] = {}
    for app in applications:
        matrix.setdefault(app.student_id, set()).add(app.job_id)
    return matrix


def cosine_similarity(a: set[int], b: set[int]) -> float:
    if not a or not b:
        return 0.0
    common = len(a.intersection(b))
    if common == 0:
        return 0.0
    return common / math.sqrt(len(a) * len(b))


def compute_collaborative_scores(
    applications: list[Application], jobs: list[Job], target_student_id: int | None
) -> dict[int, int]:
    scores: dict[int, float] = {job.id: 0.0 for job in jobs}
    if not applications:
        return {job.id: 0 for job in jobs}

    user_job_map = build_user_job_map(applications)
    if target_student_id and target_student_id in user_job_map:
        target_jobs = user_job_map.get(target_student_id, set())
        for student_id, applied_jobs in user_job_map.items():
            if student_id == target_student_id:
                continue
            sim = cosine_similarity(target_jobs, applied_jobs)
            if sim <= 0:
                continue
            for job_id in applied_jobs:
                if job_id not in target_jobs:
                    scores[job_id] += sim * 100
    else:
        counts: dict[int, int] = {}
        for app in applications:
            counts[app.job_id] = counts.get(app.job_id, 0) + 1
        max_count = max(counts.values()) if counts else 1
        return {job_id: int((count / max_count) * 100) for job_id, count in counts.items()}

    max_score = max(scores.values()) if scores else 0
    if max_score <= 0:
        return {job.id: 0 for job in jobs}
    return {job_id: int((score / max_score) * 100) for job_id, score in scores.items()}


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
    questions = build_interview_questions(
        job_title=template.job_title,
        question_types=template.question_types or default_question_types(),
        question_count=template.question_count,
        focus_points=focus_points,
    )

    score = 45
    score += min(35, len(candidate_skills) * 7)
    score += 10 if len(summary) >= 80 else 5 if len(summary) >= 30 else 0
    score += 8 if len(experience) >= 80 else 4 if len(experience) >= 30 else 0
    score = max(0, min(98, score))

    if score >= 80:
        recommendation = '建议进入下一轮面试'
    elif score >= 65:
        recommendation = '建议人工复核后再决定'
    else:
        recommendation = '建议暂不推进'

    focus_areas: list[str] = []
    if len(candidate_skills) < 2:
        focus_areas.append('补充核心技能与项目细节')
    if len(summary) < 30:
        focus_areas.append('完善候选人背景与亮点总结')
    if len(experience) < 30:
        focus_areas.append('补充可量化的项目成果')
    if not focus_areas:
        focus_areas.append('重点核验复杂场景下的问题拆解能力')

    evaluation = (
        f'基于模板题型与候选信息生成 {len(questions)} 道初筛问题，'
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
    focus_points = payload.learning_focus or extract_keywords(content)
    question_types = normalize_question_types(payload.question_types)
    questions = build_interview_questions(
        job_title=payload.job_title,
        question_types=question_types,
        question_count=payload.question_count,
        focus_points=focus_points,
    )

    content_score = min(45, len(content) // 25)
    focus_score = min(25, len(focus_points) * 5)
    depth_score = 10 if payload.difficulty == 'hard' else 5 if payload.difficulty == 'medium' else 0
    score = max(0, min(95, 35 + content_score + focus_score + depth_score))

    strengths = [
        '能够围绕学习内容提炼核心知识点',
        '问题生成覆盖技术、场景与表达能力',
    ]
    improvements = [
        '补充项目中的具体指标和结果数据',
        '准备 1-2 个高压场景下的决策案例',
        '练习将复杂问题分步讲清楚',
    ]
    next_actions = [
        '按题目顺序录制 10 分钟自我回答并复盘',
        '针对薄弱项补充 2 个项目故事',
        '48 小时后重复一次模拟并对比进步',
    ]
    feedback = f'模拟评分 {score} 分。建议优先加强可量化成果表达与场景化回答。'

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
    collab_scores = compute_collaborative_scores(applications, jobs, payload.student_id)

    rec_config = db.scalar(select(RecommendConfig).order_by(RecommendConfig.id.desc()))
    collab_w = rec_config.collaborative_weight if rec_config else 0.4
    content_w = rec_config.content_weight if rec_config else 0.6

    results: list[schemas.JobRecommendResult] = []

    for job in jobs:
        job_skills = job.skill_tags or []
        matched = [skill for skill in job_skills if skill in skills]
        missing = [skill for skill in job_skills if skill not in skills]

        skill_score = int((len(matched) / max(len(job_skills), 1)) * 70)
        city_bonus = 15 if intention and intention.expected_city == job.city else 0
        industry_bonus = 0

        company = db.get(CompanyProfile, job.company_id)
        if intention and company and intention.expected_industry:
            industry_bonus = 15 if company.industry == intention.expected_industry else 0

        content_score = min(100, skill_score + city_bonus + industry_bonus)
        collaborative_score = collab_scores.get(job.id, 0)
        final_score = int(collab_w * collaborative_score + content_w * content_score)

        results.append(
            schemas.JobRecommendResult(
                job_id=job.id,
                job_name=job.job_name,
                final_score=final_score,
                content_score=content_score,
                collaborative_score=collaborative_score,
                matched_skills=matched,
                missing_skills=missing,
                reason='Hybrid score from collaborative behavior and content similarity.',
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


@router.post('/interview', response_model=schemas.InterviewResponse)
def interview(
    payload: schemas.InterviewRequest,
    _: User = Depends(get_current_user),
) -> schemas.InterviewResponse:
    skill_focus = payload.skills or ['system design', 'debugging', 'communication']
    questions = [
        f'Explain a core concept in {skill_focus[0]}.',
        f'Describe a challenging incident you handled related to {skill_focus[-1]}.',
        f'How would you approach on-call triage for a {payload.job_title} role?',
        'Walk through a recent project and the trade-offs you made.',
    ]
    evaluation = 'Focus on clarity, ownership, and reliability mindset.'
    return schemas.InterviewResponse(questions=questions, evaluation=evaluation)


@router.post('/rag', response_model=schemas.RagResponse)
def rag(payload: schemas.RagRequest, _: User = Depends(get_current_user)) -> schemas.RagResponse:
    answer = (
        'Start with Linux fundamentals, then containerization, then observability. '
        'Build a small project and document your learnings.'
    )
    learning_path = [
        'Linux fundamentals',
        'Networking basics',
        'Docker and containers',
        'Kubernetes workloads',
        'Observability tooling',
    ]
    skill_tree = ['Linux -> Networking -> Containers', 'Kubernetes -> SRE Practices']
    return schemas.RagResponse(answer=answer, learning_path=learning_path, skill_tree=skill_tree)


@router.post('/mock-interview', response_model=schemas.MockInterviewResponse)
def mock_interview(
    payload: schemas.MockInterviewRequest,
    _: User = Depends(get_current_user),
) -> schemas.MockInterviewResponse:
    questions = [
        f'What does reliability mean for a {payload.job_title}?',
        'Describe how you would set SLOs and SLIs.',
        'Explain how you would handle a production incident.',
    ]
    feedback = 'Be concise, quantify impact, and outline mitigation steps.'
    return schemas.MockInterviewResponse(questions=questions, feedback=feedback)
