from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, extract, func, select
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
    Favorite,
    Job,
    Notification,
    OperationLog,
    RecommendConfig,
    StudentProfile,
    User,
    VerificationRequest,
    ViewHistory,
)
from app.notification_service import create_notification_sync
from app.routers.ai import compute_collaborative_scores
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


@router.get('/announcements/published', response_model=list[schemas.Announcement])
def list_published_announcements(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin', 'student', 'company')),
) -> list[schemas.Announcement]:
    rows = db.scalars(
        select(Announcement)
        .where(Announcement.status == 'published')
        .order_by(Announcement.pinned.desc(), Announcement.id.desc())
    ).all()
    return [schemas.Announcement.model_validate(item) for item in rows]


@router.post('/announcements', response_model=schemas.Announcement)
def create_announcement(
    payload: schemas.Announcement,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin')),
) -> schemas.Announcement:
    record = Announcement(**payload.model_dump(exclude={'id', 'create_time', 'update_time'}))
    db.add(record)
    db.flush()

    # Notify all users about new published announcement
    if record.status == 'published':
        all_users = db.scalars(select(User).where(User.status == 'active')).all()
        for u in all_users:
            create_notification_sync(
                db, user_id=u.id,
                title='新公告', content=f'平台发布了新公告：{record.title}',
                notification_type='announcement', related_id=record.id,
            )

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
        job_total=db.scalar(select(func.count()).select_from(Job).where(Job.status == 'active')) or 0,
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


# ---------------------------------------------------------------------------
# Feature: Recommendation Evaluation Center
# ---------------------------------------------------------------------------

@router.get('/recommend-evaluation', response_model=schemas.RecommendEvaluationResponse)
def recommend_evaluation(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin')),
) -> schemas.RecommendEvaluationResponse:
    cache_key = 'stats:recommend_evaluation'
    cached = cache_get_json(cache_key)
    if cached:
        return schemas.RecommendEvaluationResponse(**cached)

    K = 5

    # Load global data once
    all_jobs = db.scalars(select(Job).where(Job.status == 'active')).all()
    all_applications = db.scalars(select(Application)).all()
    all_views = db.scalars(select(ViewHistory)).all()
    all_favorites = db.scalars(select(Favorite)).all()

    rec_config = db.scalar(select(RecommendConfig).order_by(RecommendConfig.id.desc()))
    collab_w = rec_config.collaborative_weight if rec_config else 0.4
    content_w = rec_config.content_weight if rec_config else 0.6

    total_jobs = len(all_jobs)
    total_applications = len(all_applications)

    # Group applications by student
    student_apps: dict[int, set[int]] = {}
    for app in all_applications:
        student_apps.setdefault(app.student_id, set()).add(app.job_id)

    # Count interactions per student (applications + favorites + views)
    interaction_counts: Counter[int] = Counter()
    for app in all_applications:
        interaction_counts[app.student_id] += 1
    for fav in all_favorites:
        interaction_counts[fav.user_id] += 1
    for v in all_views:
        interaction_counts[v.user_id] += 1

    # Students with at least 1 application
    students_with_apps = {sid for sid, jobs in student_apps.items() if jobs}
    total_students = db.scalar(select(func.count()).select_from(StudentProfile)) or 0
    cold_start_users = sum(1 for sid in students_with_apps if interaction_counts.get(sid, 0) < 3)

    precision_sum = 0.0
    recall_sum = 0.0
    hit_count = 0
    total_matched_skills = 0
    total_recommendation_count = 0
    recommended_job_ids: set[int] = set()

    for student_id, applied_job_ids in student_apps.items():
        student = db.get(StudentProfile, student_id)
        if not student:
            continue

        skills_lower = {s.lower() for s in (student.skills or [])}

        # Compute per-student collaborative scores
        student_collab, _ = compute_collaborative_scores(
            all_applications, all_jobs, student_id,
            views=all_views, favorites=all_favorites,
        )

        # Score each job (reuse the same logic as ai.py job_recommend)
        scored: list[tuple[int, int, int]] = []  # (job_id, final_score, matched_count)
        for job in all_jobs:
            job_skills = job.skill_tags or []
            job_skills_lower = {s.lower() for s in job_skills}
            matched_count = len(skills_lower & job_skills_lower)

            skill_score = int((matched_count / max(len(job_skills), 1)) * 50)
            content_score = min(100, skill_score)  # simplified: skip city/industry for eval
            collaborative_score = student_collab.get(job.id, 0)
            final_score = int(collab_w * collaborative_score + content_w * content_score)

            scored.append((job.id, final_score, matched_count))

        scored.sort(key=lambda x: x[1], reverse=True)
        top_k_ids = {item[0] for item in scored[:K]}
        top_k_matched = sum(item[2] for item in scored[:K])

        recommended_job_ids.update(top_k_ids)

        # Precision@K = |relevant in top-K| / K
        relevant_in_top_k = len(top_k_ids & applied_job_ids)
        precision_sum += relevant_in_top_k / K

        # Recall@K = |relevant in top-K| / |all relevant|
        recall_sum += relevant_in_top_k / len(applied_job_ids)

        if relevant_in_top_k > 0:
            hit_count += 1

        total_matched_skills += top_k_matched
        total_recommendation_count += K

    evaluated = len(students_with_apps)
    precision_at_5 = round(precision_sum / max(evaluated, 1), 4)
    recall_at_5 = round(recall_sum / max(evaluated, 1), 4)
    hit_rate = round(hit_count / max(evaluated, 1), 4)
    coverage = round(len(recommended_job_ids) / max(total_jobs, 1), 4)
    avg_matched = round(total_matched_skills / max(total_recommendation_count, 1), 2)

    result = schemas.RecommendEvaluationResponse(
        total_students=total_students,
        evaluated_students=evaluated,
        cold_start_users=cold_start_users,
        total_jobs=total_jobs,
        total_applications=total_applications,
        precision_at_5=precision_at_5,
        recall_at_5=recall_at_5,
        hit_rate=hit_rate,
        coverage=coverage,
        avg_matched_skills=avg_matched,
        algorithm_version=f'hybrid(collab={collab_w},content={content_w})',
        evaluation_time=datetime.utcnow().isoformat(),
    )
    cache_set_json(cache_key, result.model_dump(), ttl_seconds=30)
    return result


# ---------------------------------------------------------------------------
# Feature: Enhanced Employment Analytics Dashboard
# ---------------------------------------------------------------------------

@router.get('/employment-analytics', response_model=schemas.EmploymentAnalyticsResponse)
def employment_analytics(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles('admin')),
) -> schemas.EmploymentAnalyticsResponse:
    cache_key = 'stats:employment_analytics'
    cached = cache_get_json(cache_key)
    if cached:
        return schemas.EmploymentAnalyticsResponse(**cached)

    # 1. Major-wise application heatmap: top 10 majors by application count
    major_rows = db.execute(
        select(StudentProfile.major, func.count(Application.id).label('cnt'))
        .join(Application, Application.student_id == StudentProfile.user_id)
        .group_by(StudentProfile.major)
        .order_by(func.count(Application.id).desc())
        .limit(10)
    ).all()
    major_heatmap = [
        schemas.MajorHeatmapItem(major=row[0], application_count=row[1])
        for row in major_rows
    ]

    # 2. Job type popularity: application count by job_type
    jt_rows = db.execute(
        select(Job.job_type, func.count(Application.id).label('cnt'))
        .join(Application, Application.job_id == Job.id)
        .group_by(Job.job_type)
        .order_by(func.count(Application.id).desc())
    ).all()
    job_type_popularity = [
        schemas.JobTypePopularityItem(job_type=row[0], application_count=row[1])
        for row in jt_rows
    ]

    # 3. Conversion funnel: count of applications at each status
    status_order = ['submitted', 'reviewing', 'to_contact', 'accepted', 'rejected', 'withdrawn']
    status_rows = db.execute(
        select(Application.status, func.count(Application.id).label('cnt'))
        .group_by(Application.status)
    ).all()
    status_map = {row[0]: row[1] for row in status_rows}
    conversion_funnel = [
        schemas.ConversionFunnelItem(status=s, count=status_map.get(s, 0))
        for s in status_order
    ]

    # 4. Skill gap analysis: most frequently missing skills across all applications
    # For each application, find job skill_tags that the student does NOT have
    apps_with_data = db.execute(
        select(StudentProfile.skills, Job.skill_tags)
        .join(Application, Application.student_id == StudentProfile.user_id)
        .join(Job, Job.id == Application.job_id)
    ).all()
    missing_counter: Counter[str] = Counter()
    for student_skills_raw, job_skills_raw in apps_with_data:
        student_skills_lower = {s.lower() for s in (student_skills_raw or [])}
        for skill in (job_skills_raw or []):
            if skill.lower() not in student_skills_lower:
                missing_counter[skill] += 1
    skill_gap = [
        schemas.SkillGapItem(skill=skill, missing_count=count)
        for skill, count in missing_counter.most_common(15)
    ]

    # 5. Company activity: companies ranked by response rate
    company_activity_rows = db.execute(
        select(
            CompanyProfile.company_name,
            func.count(Application.id).label('total'),
            func.sum(
                case(
                    (Application.status.in_(['reviewing', 'to_contact', 'accepted', 'rejected']), 1),
                    else_=0,
                )
            ).label('reviewed'),
        )
        .join(Job, Job.company_id == CompanyProfile.user_id)
        .join(Application, Application.job_id == Job.id)
        .group_by(CompanyProfile.company_name)
        .order_by(
            (func.sum(
                case(
                    (Application.status.in_(['reviewing', 'to_contact', 'accepted', 'rejected']), 1),
                    else_=0,
                )
            ) * 1.0 / func.count(Application.id)).desc()
        )
        .limit(10)
    ).all()
    company_activity = [
        schemas.CompanyActivityItem(
            company_name=row[0],
            total_received=row[1],
            total_reviewed=int(row[2] or 0),
            response_rate=round(int(row[2] or 0) / max(row[1], 1), 4),
        )
        for row in company_activity_rows
    ]

    # 6. Monthly trend: applications per month for last 6 months
    now = datetime.utcnow()
    six_months_ago = now - timedelta(days=180)
    monthly_rows = db.execute(
        select(
            extract('year', Application.create_time).label('y'),
            extract('month', Application.create_time).label('m'),
            func.count(Application.id).label('cnt'),
        )
        .where(Application.create_time >= six_months_ago)
        .group_by('y', 'm')
        .order_by('y', 'm')
    ).all()
    monthly_trend = [
        schemas.MonthlyTrendItem(
            month=f'{int(row[0])}-{int(row[1]):02d}',
            application_count=row[2],
        )
        for row in monthly_rows
    ]

    result = schemas.EmploymentAnalyticsResponse(
        major_heatmap=major_heatmap,
        job_type_popularity=job_type_popularity,
        conversion_funnel=conversion_funnel,
        skill_gap=skill_gap,
        company_activity=company_activity,
        monthly_trend=monthly_trend,
    )
    cache_set_json(cache_key, result.model_dump(), ttl_seconds=30)
    return result
