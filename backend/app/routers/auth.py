from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.db import get_db
from app.models import CompanyProfile, StudentIntention, StudentProfile, User
from app.security import hash_password

router = APIRouter(prefix='/auth', tags=['auth'])


def ensure_unique_email(db: Session, email: str) -> None:
    exists = db.scalar(select(User).where(User.email == email))
    if exists:
        raise HTTPException(status_code=400, detail='Email already exists')


@router.post('/register/student', response_model=schemas.UserOut)
def register_student(payload: schemas.StudentRegister, db: Session = Depends(get_db)) -> schemas.UserOut:
    ensure_unique_email(db, payload.email)

    user = User(
        role='student',
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        status='active',
    )
    db.add(user)
    db.flush()

    db.add(
        StudentProfile(
            user_id=user.id,
            name=payload.name,
            student_no=payload.student_no,
            school=payload.school,
            major=payload.major,
            grade=payload.grade,
            phone=payload.phone,
            email=payload.email,
            skills=payload.skills,
            awards=payload.awards,
            internships=payload.internships,
            projects=payload.projects,
            bio=payload.bio,
            verified=False,
        )
    )
    db.add(StudentIntention(student_id=user.id))

    db.commit()
    db.refresh(user)
    return schemas.UserOut.model_validate(user)


@router.post('/register/company', response_model=schemas.UserOut)
def register_company(payload: schemas.CompanyRegister, db: Session = Depends(get_db)) -> schemas.UserOut:
    ensure_unique_email(db, payload.email)

    user = User(
        role='company',
        name=payload.contact_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        status='active',
    )
    db.add(user)
    db.flush()

    db.add(
        CompanyProfile(
            user_id=user.id,
            company_name=payload.company_name,
            credit_code=payload.credit_code,
            contact_name=payload.contact_name,
            contact_phone=payload.contact_phone,
            status='pending',
            description=payload.description,
            industry=payload.industry,
            scale=payload.scale,
            address=payload.address,
            website=payload.website,
            welfare_tags=payload.welfare_tags,
        )
    )

    db.commit()
    db.refresh(user)
    return schemas.UserOut.model_validate(user)
