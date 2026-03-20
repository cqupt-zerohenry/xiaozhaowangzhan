from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.db import get_db
from app.email_service import send_verification_email, verify_code
from app.models import CompanyProfile, StudentIntention, StudentProfile, User
from app.security import hash_password

router = APIRouter(prefix='/auth', tags=['auth'])


def ensure_unique_email(db: Session, email: str) -> None:
    exists = db.scalar(select(User).where(User.email == email))
    if exists:
        raise HTTPException(status_code=400, detail='Email already exists')


@router.post('/send-code', summary='Send email verification code')
def send_code(payload: schemas.SendCodeRequest) -> dict:
    code = send_verification_email(payload.email, payload.purpose)
    if code is None:
        raise HTTPException(status_code=500, detail='Failed to send verification code (Redis unavailable)')
    return {'status': 'sent', 'message': '验证码已发送'}


@router.post('/verify-code', summary='Verify email code')
def verify_email_code(payload: schemas.VerifyCodeRequest) -> dict:
    if verify_code(payload.email, payload.code, payload.purpose):
        return {'verified': True}
    raise HTTPException(status_code=400, detail='验证码错误或已过期')


@router.post('/register/student', response_model=schemas.UserOut, summary='Register student')
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


@router.post('/register/company', response_model=schemas.UserOut, summary='Register company')
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


@router.post('/send-reset-code', summary='Send password reset code')
def send_reset_code(payload: schemas.SendCodeRequest, db: Session = Depends(get_db)) -> dict:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user:
        raise HTTPException(status_code=404, detail='该邮箱未注册')
    code = send_verification_email(payload.email, 'reset')
    if code is None:
        raise HTTPException(status_code=500, detail='Failed to send reset code')
    return {'status': 'sent', 'message': '重置验证码已发送'}


@router.post('/reset-password', summary='Reset password by email verification')
def reset_password_by_email(payload: schemas.PasswordResetByEmailRequest, db: Session = Depends(get_db)) -> dict:
    if not verify_code(payload.email, payload.code, 'reset'):
        raise HTTPException(status_code=400, detail='验证码错误或已过期')
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {'status': 'ok', 'message': '密码已重置'}
