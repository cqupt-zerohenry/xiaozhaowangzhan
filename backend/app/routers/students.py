from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.db import get_db
from app.dependencies import get_current_user, require_self_or_roles
from app.models import Resume, StudentIntention, StudentProfile, User

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

    record = Resume(**payload.model_dump(exclude={'id', 'create_time'}))
    db.add(record)
    db.commit()
    db.refresh(record)
    return schemas.Resume.model_validate(record)
