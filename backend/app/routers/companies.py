from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
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
    StudentProfile,
    User,
    VerificationRequest,
    ViewHistory,
)

router = APIRouter(prefix='/companies', tags=['companies'])


def ensure_company_owner_or_admin(current_user: User, user_id: int) -> None:
    if current_user.role == 'admin':
        return
    if current_user.role == 'company' and current_user.id == user_id:
        return
    raise HTTPException(status_code=403, detail='Permission denied')


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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.TalentRecommendResponse:
    ensure_company_owner_or_admin(current_user, user_id)

    company_jobs = db.scalars(select(Job).where(Job.company_id == user_id, Job.status == 'active')).all()
    required_skills: set[str] = set()
    for job in company_jobs:
        required_skills.update(job.skill_tags or [])

    students = db.scalars(select(StudentProfile)).all()
    results: list[schemas.TalentRecommendResult] = []
    for student in students:
        skills = set(student.skills or [])
        matched = required_skills.intersection(skills)
        score = int((len(matched) / max(len(required_skills), 1)) * 100)
        results.append(
            schemas.TalentRecommendResult(
                student_id=student.user_id,
                name=student.name,
                major=student.major,
                grade=student.grade,
                skills=list(skills),
                match_score=score,
                reason='Based on overlap between job skills and student skills.',
            )
        )

    results.sort(key=lambda item: item.match_score, reverse=True)
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

    record = VerificationRequest(
        company_id=user_id,
        student_id=payload.student_id,
        fields=payload.fields,
        status='pending',
        result='',
    )
    db.add(record)
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
