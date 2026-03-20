from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import schemas
from app.db import get_db
from app.dependencies import get_current_user, require_self_or_roles
from app.cache import cache_get_json, cache_set_json
from app.models import Application, CompanyProfile, Job, Resume, StudentIntention, StudentProfile, User, VerificationRequest, ViewHistory

router = APIRouter(prefix='/students', tags=['students'])


@router.post('', response_model=schemas.StudentProfile)
def upsert_student(
    payload: schemas.StudentProfile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.StudentProfile:
    require_self_or_roles(payload.user_id, current_user, {'admin'})

    user = db.get(User, payload.user_id)
    if not user or user.role != 'student':
        raise HTTPException(status_code=404, detail='Student user not found')

    profile = db.get(StudentProfile, payload.user_id)
    data = payload.model_dump()
    if profile:
        for key, value in data.items():
            setattr(profile, key, value)
    else:
        profile = StudentProfile(**data)
        db.add(profile)

    db.commit()
    db.refresh(profile)
    return schemas.StudentProfile.model_validate(profile)


@router.put('/{user_id}', response_model=schemas.StudentProfile)
def update_student(
    user_id: int,
    payload: schemas.StudentProfile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.StudentProfile:
    if user_id != payload.user_id:
        raise HTTPException(status_code=400, detail='User id mismatch')
    require_self_or_roles(user_id, current_user, {'admin'})

    profile = db.get(StudentProfile, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail='Student not found')

    for key, value in payload.model_dump().items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return schemas.StudentProfile.model_validate(profile)


@router.get('', response_model=list[schemas.StudentProfile])
def list_students(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[schemas.StudentProfile]:
    if current_user.role not in {'admin', 'company'}:
        raise HTTPException(status_code=403, detail='Permission denied')

    rows = db.scalars(select(StudentProfile).order_by(StudentProfile.user_id.desc())).all()
    return [schemas.StudentProfile.model_validate(item) for item in rows]


@router.get('/{user_id}', response_model=schemas.StudentProfile)
def get_student(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.StudentProfile:
    require_self_or_roles(user_id, current_user, {'admin', 'company'})

    profile = db.get(StudentProfile, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail='Student not found')
    return schemas.StudentProfile.model_validate(profile)


@router.get('/{user_id}/intention', response_model=schemas.StudentIntention)
def get_intention(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.StudentIntention:
    require_self_or_roles(user_id, current_user, {'admin', 'company'})

    intention = db.get(StudentIntention, user_id)
    if not intention:
        raise HTTPException(status_code=404, detail='Intention not found')
    return schemas.StudentIntention.model_validate(intention)


@router.put('/{user_id}/intention', response_model=schemas.StudentIntention)
def update_intention(
    user_id: int,
    payload: schemas.StudentIntention,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.StudentIntention:
    if user_id != payload.student_id:
        raise HTTPException(status_code=400, detail='Student id mismatch')
    require_self_or_roles(user_id, current_user, {'admin'})

    intention = db.get(StudentIntention, user_id)
    data = payload.model_dump()
    if intention:
        for key, value in data.items():
            setattr(intention, key, value)
    else:
        intention = StudentIntention(**data)
        db.add(intention)

    db.commit()
    db.refresh(intention)
    return schemas.StudentIntention.model_validate(intention)


@router.get('/{user_id}/resumes', response_model=list[schemas.Resume])
def list_resumes(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[schemas.Resume]:
    require_self_or_roles(user_id, current_user, {'admin', 'company'})

    rows = db.scalars(
        select(Resume).where(Resume.student_id == user_id).order_by(Resume.version_no.desc())
    ).all()
    return [schemas.Resume.model_validate(item) for item in rows]


@router.post('/{user_id}/resumes', response_model=schemas.Resume)
def create_resume(
    user_id: int,
    payload: schemas.Resume,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.Resume:
    if user_id != payload.student_id:
        raise HTTPException(status_code=400, detail='Student id mismatch')
    require_self_or_roles(user_id, current_user, {'admin'})

    profile = db.get(StudentProfile, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail='Student not found')

    max_version = db.scalar(
        select(func.max(Resume.version_no)).where(Resume.student_id == user_id)
    ) or 0
    data = payload.model_dump(exclude={'id', 'create_time'})
    data['version_no'] = max_version + 1
    record = Resume(**data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return schemas.Resume.model_validate(record)


# ---------------------------------------------------------------------------
# View History
# ---------------------------------------------------------------------------

@router.get('/{user_id}/view-history', response_model=list[schemas.ViewHistoryDetailOut], summary='Get view history')
def get_view_history(
    user_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[schemas.ViewHistoryDetailOut]:
    require_self_or_roles(user_id, current_user, {'admin'})
    rows = db.scalars(
        select(ViewHistory).where(ViewHistory.user_id == user_id)
        .order_by(ViewHistory.id.desc()).limit(limit)
    ).all()
    result = []
    for vh in rows:
        job = db.get(Job, vh.job_id)
        company_name = ''
        job_name = f'岗位{vh.job_id}'
        if job:
            job_name = job.job_name
            cp = db.get(CompanyProfile, job.company_id)
            company_name = cp.company_name if cp else ''
        result.append(schemas.ViewHistoryDetailOut(
            id=vh.id, job_id=vh.job_id, job_name=job_name,
            company_name=company_name, create_time=vh.create_time,
        ))
    return result


# ---------------------------------------------------------------------------
# Student Verification Requests
# ---------------------------------------------------------------------------

@router.get('/{user_id}/verification-requests', response_model=list[schemas.VerificationRequestOut],
            summary='Get student verification requests')
def get_student_verifications(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[schemas.VerificationRequestOut]:
    require_self_or_roles(user_id, current_user, {'admin'})
    rows = db.scalars(
        select(VerificationRequest).where(VerificationRequest.student_id == user_id)
        .order_by(VerificationRequest.id.desc())
    ).all()
    return [schemas.VerificationRequestOut.model_validate(row) for row in rows]


# ---------------------------------------------------------------------------
# Student Employment Analytics
# ---------------------------------------------------------------------------

@router.get('/{user_id}/analytics', response_model=schemas.StudentAnalyticsResponse,
            summary='Student employment analytics')
def student_analytics(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.StudentAnalyticsResponse:
    require_self_or_roles(user_id, current_user, {'admin'})

    cache_key = f'student_analytics:{user_id}'
    cached = cache_get_json(cache_key)
    if cached:
        return schemas.StudentAnalyticsResponse(**cached)

    student = db.get(StudentProfile, user_id)
    if not student:
        raise HTTPException(status_code=404, detail='Student not found')

    my_skills = set(s.lower() for s in (student.skills or []))

    # Skill competitiveness: for each skill, what % of students have it
    all_students = db.scalars(select(StudentProfile)).all()
    total_students = max(len(all_students), 1)
    skill_counts: Counter[str] = Counter()
    for s in all_students:
        for sk in (s.skills or []):
            skill_counts[sk.lower()] += 1

    skill_competitiveness = []
    for skill in (student.skills or []):
        count = skill_counts.get(skill.lower(), 0)
        rarity = round((1 - count / total_students) * 100)
        skill_competitiveness.append({'skill': skill, 'percentile': rarity, 'holders': count})

    # Salary benchmark: from jobs matching student's intention
    intention = db.get(StudentIntention, user_id)
    salary_query = select(Job.salary_min, Job.salary_max).where(Job.status == 'active')
    if intention and intention.expected_job:
        salary_query = salary_query.where(Job.job_name.contains(intention.expected_job))
    salary_rows = db.execute(salary_query).all()
    if salary_rows:
        mins = [r[0] for r in salary_rows]
        maxs = [r[1] for r in salary_rows]
        salary_benchmark = {
            'min': min(mins), 'max': max(maxs),
            'avg_min': round(sum(mins) / len(mins)),
            'avg_max': round(sum(maxs) / len(maxs)),
            'sample_count': len(salary_rows),
        }
    else:
        salary_benchmark = {'min': 0, 'max': 0, 'avg_min': 0, 'avg_max': 0, 'sample_count': 0}

    # Market trends: active jobs by type
    type_rows = db.execute(
        select(Job.job_type, func.count().label('cnt'))
        .where(Job.status == 'active')
        .group_by(Job.job_type)
        .order_by(func.count().desc())
        .limit(10)
    ).all()
    market_trends = [{'job_type': r[0], 'count': r[1]} for r in type_rows]

    # Application stats
    my_apps = db.scalars(select(Application).where(Application.student_id == user_id)).all()
    total_applied = len(my_apps)
    status_counts: Counter[str] = Counter(a.status for a in my_apps)
    interviewed = status_counts.get('interviewing', 0) + status_counts.get('interview_scheduled', 0)
    offered = status_counts.get('accepted', 0)
    application_stats = {
        'total_applied': total_applied,
        'viewed': status_counts.get('viewed', 0),
        'interviewing': interviewed,
        'offered': offered,
        'rejected': status_counts.get('rejected', 0),
        'interview_rate': round(interviewed / max(total_applied, 1) * 100, 1),
        'offer_rate': round(offered / max(total_applied, 1) * 100, 1),
    }

    result = schemas.StudentAnalyticsResponse(
        skill_competitiveness=skill_competitiveness,
        salary_benchmark=salary_benchmark,
        market_trends=market_trends,
        application_stats=application_stats,
    )
    cache_set_json(cache_key, result.model_dump(), ttl_seconds=60)
    return result
