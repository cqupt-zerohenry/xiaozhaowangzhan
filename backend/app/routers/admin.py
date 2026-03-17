from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import schemas
from app.cache import cache_delete_prefix, cache_get_json, cache_set_json
from app.db import get_db
from app.dependencies import require_roles
from app.models import (
    Announcement,
    Application,
    AuditRecord,
    CompanyProfile,
    Job,
    OperationLog,
    RecommendConfig,
    StudentProfile,
    User,
    VerificationRequest,
)
from app.security import hash_password

router = APIRouter(prefix='/admin', tags=['admin'])


@router.get('/audits', response_model=list[schemas.AuditRecord])
def list_audits(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin')),
) -> list[schemas.AuditRecord]:
    rows = db.scalars(select(AuditRecord).order_by(AuditRecord.id.desc())).all()
    return [schemas.AuditRecord.model_validate(item) for item in rows]


@router.post('/audits', response_model=schemas.AuditRecord)
def create_audit(
    payload: schemas.AuditRecord,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin')),
) -> schemas.AuditRecord:
    record = AuditRecord(**payload.model_dump(exclude={'id', 'create_time'}))
    db.add(record)
    db.commit()
    db.refresh(record)
    return schemas.AuditRecord.model_validate(record)


@router.get('/announcements', response_model=list[schemas.Announcement])
def list_announcements(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin')),
) -> list[schemas.Announcement]:
    rows = db.scalars(select(Announcement).order_by(Announcement.pinned.desc(), Announcement.id.desc())).all()
    return [schemas.Announcement.model_validate(item) for item in rows]


@router.post('/announcements', response_model=schemas.Announcement)
def create_announcement(
    payload: schemas.Announcement,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin')),
) -> schemas.Announcement:
    record = Announcement(**payload.model_dump(exclude={'id', 'create_time', 'update_time'}))
    db.add(record)
    db.commit()
    db.refresh(record)
    cache_delete_prefix('stats:')
    return schemas.Announcement.model_validate(record)


@router.put('/announcements/{announcement_id}', response_model=schemas.Announcement)
def update_announcement(
    announcement_id: int,
    payload: schemas.Announcement,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin')),
) -> schemas.Announcement:
    record = db.get(Announcement, announcement_id)
    if not record:
        raise HTTPException(status_code=404, detail='Announcement not found')

    data = payload.model_dump(exclude={'id', 'create_time', 'update_time'})
    for key, value in data.items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return schemas.Announcement.model_validate(record)


@router.delete('/announcements/{announcement_id}')
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin')),
) -> dict:
    record = db.get(Announcement, announcement_id)
    if not record:
        raise HTTPException(status_code=404, detail='Announcement not found')
    db.delete(record)
    db.commit()
    return {'status': 'deleted'}


@router.get('/stats', response_model=schemas.StatsResponse)
def stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin')),
) -> schemas.StatsResponse:
    cache_key = 'stats:overview'
    cached = cache_get_json(cache_key)
    if cached:
        return schemas.StatsResponse(**cached)

    result = schemas.StatsResponse(
        student_total=db.scalar(select(func.count()).select_from(StudentProfile)) or 0,
        company_total=db.scalar(select(func.count()).select_from(CompanyProfile)) or 0,
        job_total=db.scalar(select(func.count()).select_from(Job)) or 0,
        application_total=db.scalar(select(func.count()).select_from(Application)) or 0,
    )
    cache_set_json(cache_key, result.model_dump(), ttl_seconds=30)
    return result


@router.patch('/users/{user_id}/status', response_model=schemas.UserOut)
def update_user_status(
    user_id: int,
    payload: schemas.UserStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin')),
) -> schemas.UserOut:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    user.status = payload.status
    db.commit()
    db.refresh(user)
    return schemas.UserOut.model_validate(user)


@router.get('/verification-requests', response_model=list[schemas.VerificationRequestOut])
def list_verification_requests(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin')),
) -> list[schemas.VerificationRequestOut]:
    rows = db.scalars(select(VerificationRequest).order_by(VerificationRequest.id.desc())).all()
    return [schemas.VerificationRequestOut.model_validate(row) for row in rows]


@router.patch('/verification-requests/{request_id}', response_model=schemas.VerificationRequestOut)
def update_verification_request(
    request_id: int,
    payload: schemas.VerificationRequestUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin')),
) -> schemas.VerificationRequestOut:
    record = db.get(VerificationRequest, request_id)
    if not record:
        raise HTTPException(status_code=404, detail='Verification request not found')

    record.status = payload.status
    record.result = payload.result

    student = db.get(StudentProfile, record.student_id)
    if student and payload.status == 'approved':
        student.verified = True

    db.commit()
    db.refresh(record)
    return schemas.VerificationRequestOut.model_validate(record)


@router.get('/enhanced-stats', response_model=schemas.EnhancedStatsResponse)
def enhanced_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin')),
) -> schemas.EnhancedStatsResponse:
    cache_key = 'stats:enhanced'
    cached = cache_get_json(cache_key)
    if cached:
        return schemas.EnhancedStatsResponse(**cached)

    student_total = db.scalar(select(func.count()).select_from(StudentProfile)) or 0
    company_total = db.scalar(select(func.count()).select_from(CompanyProfile)) or 0
    job_total = db.scalar(select(func.count()).select_from(Job)) or 0
    application_total = db.scalar(select(func.count()).select_from(Application)) or 0

    # Hot job types
    job_type_rows = db.execute(
        select(Job.job_type, func.count().label('cnt'))
        .where(Job.status == 'active')
        .group_by(Job.job_type)
        .order_by(func.count().desc())
        .limit(5)
    ).all()
    hot_job_types = [{'type': row[0], 'count': row[1]} for row in job_type_rows]

    # Active companies (by job count)
    company_rows = db.execute(
        select(CompanyProfile.company_name, func.count(Job.id).label('cnt'))
        .join(Job, Job.company_id == CompanyProfile.user_id)
        .where(Job.status == 'active')
        .group_by(CompanyProfile.company_name)
        .order_by(func.count(Job.id).desc())
        .limit(5)
    ).all()
    active_companies = [{'name': row[0], 'job_count': row[1]} for row in company_rows]

    result = schemas.EnhancedStatsResponse(
        student_total=student_total,
        company_total=company_total,
        job_total=job_total,
        application_total=application_total,
        hot_job_types=hot_job_types,
        active_companies=active_companies,
        recommendation_stats={'algorithm': 'hybrid', 'collaborative_weight': 0.4, 'content_weight': 0.6},
    )
    cache_set_json(cache_key, result.model_dump(), ttl_seconds=30)
    return result


@router.post('/users/{user_id}/reset-password')
def reset_password(
    user_id: int,
    payload: schemas.PasswordResetRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin')),
) -> dict:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {'status': 'password_reset'}


@router.get('/operation-logs', response_model=list[schemas.OperationLogOut])
def list_operation_logs(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin')),
) -> list[schemas.OperationLogOut]:
    rows = db.scalars(select(OperationLog).order_by(OperationLog.id.desc()).limit(100)).all()
    return [schemas.OperationLogOut.model_validate(item) for item in rows]


@router.get('/recommend-config', response_model=schemas.RecommendConfigOut)
def get_recommend_config(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin')),
) -> schemas.RecommendConfigOut:
    config = db.scalar(select(RecommendConfig).order_by(RecommendConfig.id.desc()))
    if not config:
        config = RecommendConfig(collaborative_weight=0.4, content_weight=0.6)
        db.add(config)
        db.commit()
        db.refresh(config)
    return schemas.RecommendConfigOut.model_validate(config)


@router.put('/recommend-config', response_model=schemas.RecommendConfigOut)
def update_recommend_config(
    payload: schemas.RecommendConfigUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin')),
) -> schemas.RecommendConfigOut:
    config = db.scalar(select(RecommendConfig).order_by(RecommendConfig.id.desc()))
    if not config:
        config = RecommendConfig()
        db.add(config)
    config.collaborative_weight = payload.collaborative_weight
    config.content_weight = payload.content_weight
    db.commit()
    db.refresh(config)
    cache_delete_prefix('stats:')
    return schemas.RecommendConfigOut.model_validate(config)
