from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app import schemas
from app.cache import cache_get_json, cache_set_json
from app.db import get_db
from app.dependencies import get_current_user, require_roles
from app.models import (
    Application,
    CompanyProfile,
    Job,
    StudentIntention,
    StudentProfile,
    User,
    VerificationRequest,
    ViewHistory,
)
from app.notification_service import create_notification_sync

router = APIRouter(prefix='/companies', tags=['companies'])


def ensure_company_owner_or_admin(current_user: User, user_id: int) -> None:
    if current_user.role == 'admin':
        return
    if current_user.role == 'company' and current_user.id == user_id:
        return
    raise HTTPException(status_code=403, detail='Permission denied')


def _normalize_text_list(values: list[str] | None) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for value in values or []:
        text = str(value or '').strip()
        if text:
            normalized[text.lower()] = text
    return normalized


def _build_recommendation_reason(
    matched_skills: list[str],
    missing_skills: list[str],
    city_matched: bool,
    industry_matched: bool,
    accept_internship: bool,
) -> str:
    parts: list[str] = []
    if matched_skills:
        parts.append(f"技能命中 {', '.join(matched_skills[:3])}")
    else:
        parts.append('当前技能与岗位标签重合较少')
    if city_matched:
        parts.append('求职城市匹配')
    if industry_matched:
        parts.append('行业意向匹配')
    if accept_internship:
        parts.append('接受实习安排')
    if missing_skills:
        parts.append(f"待补技能 {', '.join(missing_skills[:2])}")
    return '；'.join(parts)


def _score_student_for_job(
    student: StudentProfile,
    intention: StudentIntention | None,
    company: CompanyProfile,
    job: Job,
) -> tuple[int, list[str], list[str], str]:
    student_skills_map = _normalize_text_list(student.skills)
    job_skills_map = _normalize_text_list(job.skill_tags)

    matched_skills = [
        original for key, original in job_skills_map.items()
        if key in student_skills_map
    ]
    missing_skills = [
        original for key, original in job_skills_map.items()
        if key not in student_skills_map
    ]

    skill_ratio = len(matched_skills) / max(len(job_skills_map), 1)
    skill_score = round(skill_ratio * 70)

    city_matched = bool(
        intention
        and intention.expected_city
        and job.city
        and intention.expected_city.strip().lower() == job.city.strip().lower()
    )
    industry_matched = bool(
        intention
        and intention.expected_industry
        and company.industry
        and intention.expected_industry.strip().lower() == company.industry.strip().lower()
    )
    internship_ok = bool(intention.accept_internship) if intention else True

    expected_job_text = (
        intention.expected_job.strip().lower()
        if intention and intention.expected_job
        else ''
    )
    expected_job_matched = bool(
        expected_job_text
        and (
            expected_job_text in (job.job_name or '').lower()
            or expected_job_text in (job.job_type or '').lower()
        )
    )

    score = skill_score
    if city_matched:
        score += 12
    if industry_matched:
        score += 8
    if internship_ok:
        score += 5
    if expected_job_matched:
        score += 5

    reason = _build_recommendation_reason(
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        city_matched=city_matched,
        industry_matched=industry_matched,
        accept_internship=internship_ok,
    )
    return min(score, 100), matched_skills, missing_skills, reason


@router.post('', response_model=schemas.CompanyProfile)
def upsert_company(
    payload: schemas.CompanyProfile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.CompanyProfile:
    ensure_company_owner_or_admin(current_user, payload.user_id)

    user = db.get(User, payload.user_id)
    if not user or user.role != 'company':
        raise HTTPException(status_code=404, detail='Company user not found')

    company = db.get(CompanyProfile, payload.user_id)
    data = payload.model_dump()
    if company:
        for key, value in data.items():
            setattr(company, key, value)
    else:
        company = CompanyProfile(**data)
        db.add(company)

    db.commit()
    db.refresh(company)
    return schemas.CompanyProfile.model_validate(company)


@router.put('/{user_id}', response_model=schemas.CompanyProfile)
def update_company(
    user_id: int,
    payload: schemas.CompanyProfile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.CompanyProfile:
    if user_id != payload.user_id:
        raise HTTPException(status_code=400, detail='User id mismatch')
    ensure_company_owner_or_admin(current_user, user_id)

    company = db.get(CompanyProfile, user_id)
    if not company:
        raise HTTPException(status_code=404, detail='Company not found')

    for key, value in payload.model_dump().items():
        setattr(company, key, value)

    db.commit()
    db.refresh(company)
    return schemas.CompanyProfile.model_validate(company)


@router.post('/{user_id}/certification', response_model=schemas.CompanyProfile)
def submit_certification(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.CompanyProfile:
    ensure_company_owner_or_admin(current_user, user_id)

    company = db.get(CompanyProfile, user_id)
    if not company:
        raise HTTPException(status_code=404, detail='Company not found')
    company.status = 'pending'
    db.commit()
    db.refresh(company)
    return schemas.CompanyProfile.model_validate(company)


@router.get('', response_model=list[schemas.CompanyProfile])
def list_companies(db: Session = Depends(get_db)) -> list[schemas.CompanyProfile]:
    rows = db.scalars(select(CompanyProfile).order_by(CompanyProfile.user_id.desc())).all()
    return [schemas.CompanyProfile.model_validate(item) for item in rows]


@router.get('/{user_id}', response_model=schemas.CompanyProfile)
def get_company(user_id: int, db: Session = Depends(get_db)) -> schemas.CompanyProfile:
    company = db.get(CompanyProfile, user_id)
    if not company:
        raise HTTPException(status_code=404, detail='Company not found')
    return schemas.CompanyProfile.model_validate(company)


@router.patch('/{user_id}/status', response_model=schemas.CompanyProfile)
def update_status(
    user_id: int,
    payload: schemas.CompanyStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin')),
) -> schemas.CompanyProfile:
    company = db.get(CompanyProfile, user_id)
    if not company:
        raise HTTPException(status_code=404, detail='Company not found')

    company.status = payload.status
    db.commit()
    db.refresh(company)
    return schemas.CompanyProfile.model_validate(company)


@router.get('/{user_id}/recommendations', response_model=schemas.TalentRecommendResponse)
def recommend_talents(
    user_id: int,
    job_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.TalentRecommendResponse:
    ensure_company_owner_or_admin(current_user, user_id)

    company = db.get(CompanyProfile, user_id)
    if not company:
        raise HTTPException(status_code=404, detail='Company not found')

    company_jobs = db.scalars(
        select(Job).where(Job.company_id == user_id, Job.status == 'active').order_by(Job.id.desc())
    ).all()
    if not company_jobs:
        return schemas.TalentRecommendResponse(results=[])

    if job_id is not None:
        target_job = next((item for item in company_jobs if item.id == job_id), None)
        if not target_job:
            raise HTTPException(status_code=404, detail='Job not found for this company')
        target_jobs = [target_job]
    else:
        target_jobs = company_jobs

    students = db.scalars(select(StudentProfile)).all()
    results: list[schemas.TalentRecommendResult] = []
    for student in students:
        intention = db.get(StudentIntention, student.user_id)
        best_match: tuple[Job, int, list[str], list[str], str] | None = None

        for job in target_jobs:
            score, matched_skills, missing_skills, reason = _score_student_for_job(
                student=student,
                intention=intention,
                company=company,
                job=job,
            )
            if best_match is None or score > best_match[1]:
                best_match = (job, score, matched_skills, missing_skills, reason)

        if best_match is None:
            continue

        best_job, score, matched_skills, missing_skills, reason = best_match
        results.append(
            schemas.TalentRecommendResult(
                student_id=student.user_id,
                name=student.name,
                major=student.major,
                grade=student.grade,
                accept_internship=bool(intention.accept_internship) if intention else True,
                skills=student.skills or [],
                target_job_id=best_job.id,
                target_job_name=best_job.job_name,
                city=best_job.city,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                match_score=score,
                reason=reason,
            )
        )

    results.sort(key=lambda item: (item.match_score, item.student_id), reverse=True)
    return schemas.TalentRecommendResponse(results=results)


@router.post('/{user_id}/verify-student', response_model=schemas.VerificationRequestOut)
def create_verification_request(
    user_id: int,
    payload: schemas.VerificationRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.VerificationRequestOut:
    ensure_company_owner_or_admin(current_user, user_id)

    company = db.get(CompanyProfile, user_id)
    if not company:
        raise HTTPException(status_code=404, detail='Company not found')
    student = db.get(StudentProfile, payload.student_id)
    if not student:
        raise HTTPException(status_code=404, detail='Student not found')
    if not payload.fields:
        raise HTTPException(status_code=400, detail='Please provide verification fields')

    existing_open = db.scalar(
        select(VerificationRequest)
        .where(
            VerificationRequest.company_id == user_id,
            VerificationRequest.student_id == payload.student_id,
            VerificationRequest.status.in_(['pending', 'pending_student', 'pending_admin']),
        )
    )
    if existing_open:
        raise HTTPException(status_code=409, detail='An open verification request already exists')

    record = VerificationRequest(
        company_id=user_id,
        student_id=payload.student_id,
        fields=payload.fields,
        status='pending_student',
        result='待学生确认授权',
    )
    db.add(record)
    db.flush()
    create_notification_sync(
        db,
        user_id=payload.student_id,
        title='新的核验申请',
        content=f'企业 {company.company_name} 申请核验你的信息，请在个人中心确认或拒绝。',
        notification_type='verification',
        related_id=record.id,
    )
    db.commit()
    db.refresh(record)
    return schemas.VerificationRequestOut.model_validate(record)


@router.get('/{user_id}/verify-requests', response_model=list[schemas.VerificationRequestOut])
def list_verification_requests(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[schemas.VerificationRequestOut]:
    ensure_company_owner_or_admin(current_user, user_id)

    rows = db.scalars(
        select(VerificationRequest)
        .where(VerificationRequest.company_id == user_id)
        .order_by(VerificationRequest.id.desc())
    ).all()
    return [schemas.VerificationRequestOut.model_validate(row) for row in rows]


# ---------------------------------------------------------------------------
# Company Analytics
# ---------------------------------------------------------------------------

@router.get('/{user_id}/analytics', response_model=schemas.CompanyAnalyticsResponse,
            summary='Company recruitment analytics')
def company_analytics(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.CompanyAnalyticsResponse:
    ensure_company_owner_or_admin(current_user, user_id)

    cache_key = f'company_analytics:{user_id}'
    cached = cache_get_json(cache_key)
    if cached:
        return schemas.CompanyAnalyticsResponse(**cached)

    company_jobs = db.scalars(select(Job).where(Job.company_id == user_id)).all()
    job_ids = [j.id for j in company_jobs]

    # Per-job stats: views, applications, conversion
    job_stats = []
    for job in company_jobs:
        view_count = db.scalar(
            select(func.count()).select_from(ViewHistory).where(ViewHistory.job_id == job.id)
        ) or 0
        app_count = db.scalar(
            select(func.count()).select_from(Application).where(Application.job_id == job.id)
        ) or 0
        job_stats.append({
            'job_id': job.id,
            'job_name': job.job_name,
            'views': view_count,
            'applications': app_count,
            'conversion_rate': round(app_count / max(view_count, 1) * 100, 1),
        })

    # Talent source: school and major distribution
    if job_ids:
        apps = db.scalars(select(Application).where(Application.job_id.in_(job_ids))).all()
        school_counter: Counter[str] = Counter()
        major_counter: Counter[str] = Counter()
        for app in apps:
            student = db.get(StudentProfile, app.student_id)
            if student:
                school_counter[student.school] += 1
                major_counter[student.major] += 1
        talent_source = [
            {'type': 'school', 'name': name, 'count': count}
            for name, count in school_counter.most_common(10)
        ] + [
            {'type': 'major', 'name': name, 'count': count}
            for name, count in major_counter.most_common(10)
        ]
    else:
        apps = []
        talent_source = []

    # Conversion funnel
    status_counter: Counter[str] = Counter(a.status for a in apps)
    funnel_order = ['submitted', 'viewed', 'reviewing', 'to_contact', 'interview_scheduled', 'interviewing', 'accepted', 'rejected']
    funnel = [
        schemas.ConversionFunnelItem(status=s, count=status_counter.get(s, 0))
        for s in funnel_order
    ]

    # Monthly trend (last 6 months)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    if job_ids:
        monthly_rows = db.execute(
            select(
                extract('year', Application.create_time).label('y'),
                extract('month', Application.create_time).label('m'),
                func.count(Application.id).label('cnt'),
            )
            .where(Application.job_id.in_(job_ids), Application.create_time >= six_months_ago)
            .group_by('y', 'm').order_by('y', 'm')
        ).all()
        trend = [
            schemas.MonthlyTrendItem(month=f'{int(r[0])}-{int(r[1]):02d}', application_count=r[2])
            for r in monthly_rows
        ]
    else:
        trend = []

    result = schemas.CompanyAnalyticsResponse(
        job_stats=job_stats, talent_source=talent_source, funnel=funnel, trend=trend,
    )
    cache_set_json(cache_key, result.model_dump(), ttl_seconds=60)
    return result
