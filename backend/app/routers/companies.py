from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.db import get_db
from app.dependencies import get_current_user, require_roles
from app.models import (
    CompanyProfile,
    Job,
    StudentProfile,
    User,
    VerificationRequest,
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
