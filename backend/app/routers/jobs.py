from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from app import schemas
from app.cache import cache_delete_prefix, cache_get_json, cache_set_json
from app.db import get_db
from app.dependencies import get_current_user
from app.models import CompanyProfile, Favorite, Job, User, ViewHistory
from app.job_indexer import index_job_to_kb, remove_job_from_kb
from app.security import decode_access_token

_oauth2 = OAuth2PasswordBearer(tokenUrl='/api/users/login', auto_error=False)


def get_optional_user(token: str | None = Depends(_oauth2), db: Session = Depends(get_db)) -> User | None:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get('sub', 0))
        user = db.get(User, user_id)
        return user if user and user.status == 'active' else None
    except Exception:
        return None

router = APIRouter(prefix='/jobs', tags=['jobs'])


def serialize_job(job: Job) -> dict:
    return schemas.JobOut.model_validate(job).model_dump(mode='json')


@router.post('', response_model=schemas.JobOut)
def create_job(
    payload: schemas.JobBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.JobOut:
    if current_user.role not in {'company', 'admin'}:
        raise HTTPException(status_code=403, detail='Permission denied')
    if current_user.role == 'company' and current_user.id != payload.company_id:
        raise HTTPException(status_code=403, detail='Permission denied')

    company = db.get(CompanyProfile, payload.company_id)
    if not company:
        raise HTTPException(status_code=404, detail='Company not found')
    if company.status != 'approved':
        raise HTTPException(status_code=403, detail='Company not approved')

    record = Job(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    cache_delete_prefix('jobs:list:')
    try:
        index_job_to_kb(record, db)
    except Exception:
        pass  # 索引失败不影响岗位创建
    return schemas.JobOut.model_validate(record)


@router.put('/{job_id}', response_model=schemas.JobOut)
def update_job(
    job_id: int,
    payload: schemas.JobBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.JobOut:
    record = db.get(Job, job_id)
    if not record:
        raise HTTPException(status_code=404, detail='Job not found')

    if current_user.role == 'company' and current_user.id != record.company_id:
        raise HTTPException(status_code=403, detail='Permission denied')
    if current_user.role not in {'company', 'admin'}:
        raise HTTPException(status_code=403, detail='Permission denied')

    if current_user.role == 'company':
        company = db.get(CompanyProfile, current_user.id)
        if not company or company.status != 'approved':
            raise HTTPException(status_code=403, detail='Company not approved')

    for key, value in payload.model_dump().items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    cache_delete_prefix('jobs:list:')
    try:
        index_job_to_kb(record, db)
    except Exception:
        pass
    return schemas.JobOut.model_validate(record)


@router.delete('/{job_id}')
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    record = db.get(Job, job_id)
    if not record:
        raise HTTPException(status_code=404, detail='Job not found')

    if current_user.role == 'company' and current_user.id != record.company_id:
        raise HTTPException(status_code=403, detail='Permission denied')
    if current_user.role not in {'company', 'admin'}:
        raise HTTPException(status_code=403, detail='Permission denied')

    remove_job_from_kb(record.id, db)
    db.delete(record)
    db.commit()
    cache_delete_prefix('jobs:list:')
    return {'status': 'deleted'}


@router.get('', response_model=list[schemas.JobOut])
def list_jobs(
    keyword: str | None = Query(default=None),
    company: str | None = Query(default=None),
    city: str | None = Query(default=None),
    education: str | None = Query(default=None),
    industry: str | None = Query(default=None),
    salary_min: int | None = Query(default=None),
    sort: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[schemas.JobOut]:
    cache_key = 'jobs:list:' + json.dumps(
        {
            'keyword': keyword,
            'company': company,
            'city': city,
            'education': education,
            'industry': industry,
            'salary_min': salary_min,
            'sort': sort,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    cached = cache_get_json(cache_key)
    if cached is not None:
        return [schemas.JobOut.model_validate(item) for item in cached]

    query = select(Job)
    filters = [Job.status == 'active']

    if keyword:
        like = f'%{keyword.lower()}%'
        filters.append(or_(Job.job_name.ilike(like), Job.description.ilike(like), Job.requirement.ilike(like)))

    if city:
        filters.append(Job.city == city)

    if education:
        filters.append(Job.education == education)

    if salary_min is not None:
        filters.append(Job.salary_max >= salary_min)

    if company:
        company_ids = db.scalars(
            select(CompanyProfile.user_id).where(CompanyProfile.company_name.ilike(f'%{company}%'))
        ).all()
        if not company_ids:
            return []
        filters.append(Job.company_id.in_(company_ids))

    if industry:
        company_ids = db.scalars(
            select(CompanyProfile.user_id).where(CompanyProfile.industry == industry)
        ).all()
        if not company_ids:
            return []
        filters.append(Job.company_id.in_(company_ids))

    query = query.where(*filters)

    if sort == 'latest':
        query = query.order_by(desc(Job.create_time))

    rows = db.scalars(query).all()
    serialized = [serialize_job(row) for row in rows]
    cache_set_json(cache_key, serialized, ttl_seconds=90)
    return [schemas.JobOut.model_validate(item) for item in serialized]


@router.get('/{job_id}', response_model=schemas.JobOut)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
) -> schemas.JobOut:
    record = db.get(Job, job_id)
    if not record:
        raise HTTPException(status_code=404, detail='Job not found')

    # Record view history (deduplicate per user+job)
    if current_user:
        existing = db.scalar(
            select(ViewHistory).where(
                ViewHistory.user_id == current_user.id,
                ViewHistory.job_id == job_id,
            )
        )
        if not existing:
            db.add(ViewHistory(user_id=current_user.id, job_id=job_id))
            db.commit()

    return schemas.JobOut.model_validate(record)


@router.get('/{job_id}/similar', response_model=list[schemas.SimilarJobOut])
def similar_jobs(
    job_id: int,
    db: Session = Depends(get_db),
) -> list[schemas.SimilarJobOut]:
    target = db.get(Job, job_id)
    if not target:
        raise HTTPException(status_code=404, detail='Job not found')

    target_skills = set(target.skill_tags or [])
    if not target_skills:
        return []

    others = db.scalars(
        select(Job).where(Job.id != job_id, Job.status == 'active')
    ).all()

    results = []
    for job in others:
        job_skills = set(job.skill_tags or [])
        common = target_skills.intersection(job_skills)
        if not common:
            continue
        score = int((len(common) / max(len(target_skills.union(job_skills)), 1)) * 100)
        results.append(schemas.SimilarJobOut(
            job_id=job.id,
            job_name=job.job_name,
            similarity_score=score,
            common_skills=list(common),
        ))

    results.sort(key=lambda x: x.similarity_score, reverse=True)
    return results[:5]
