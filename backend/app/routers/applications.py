from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.db import get_db
from app.dependencies import get_current_user
from app.models import Application, Job, Message, Notification, Resume, StudentProfile, User
from app.notification_service import create_notification_sync

router = APIRouter(prefix='/applications', tags=['applications'])

# ---------------------------------------------------------------------------
# Status transition rules
# ---------------------------------------------------------------------------

# Company/admin can set any status within the recruitment flow.
_COMPANY_ALLOWED_STATUSES: set[str] = {
    'submitted',
    'viewed',
    'reviewing',
    'to_contact',
    'interview_scheduled',
    'interviewing',
    'accepted',
    'rejected',
}

# Students can only withdraw, and only from these statuses
_STUDENT_WITHDRAW_FROM: set[str] = {'submitted', 'viewed', 'reviewing'}


def _validate_transition(
    current_status: str,
    new_status: str,
    role: str,
) -> str | None:
    """Return an error message if the transition is invalid, or None if OK."""
    if role == 'student':
        if new_status != 'withdrawn':
            return 'Students can only withdraw applications'
        if current_status not in _STUDENT_WITHDRAW_FROM:
            return f'Cannot withdraw from status \'{current_status}\''
        return None

    if role in ('company', 'admin'):
        if new_status not in _COMPANY_ALLOWED_STATUSES:
            return f'Unsupported status \'{new_status}\''
        return None

    return 'Unknown role'


@router.post('', response_model=schemas.Application)
def create_application(
    payload: schemas.Application,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.Application:
    if current_user.role not in {'student', 'admin'}:
        raise HTTPException(status_code=403, detail='Permission denied')
    if current_user.role == 'student' and current_user.id != payload.student_id:
        raise HTTPException(status_code=403, detail='Permission denied')

    if not db.get(StudentProfile, payload.student_id):
        raise HTTPException(status_code=404, detail='Student not found')
    if not db.get(Job, payload.job_id):
        raise HTTPException(status_code=404, detail='Job not found')
    resume = db.get(Resume, payload.resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail='Resume not found')
    if resume.student_id != payload.student_id:
        raise HTTPException(status_code=403, detail='Resume does not belong to the student')

    existed = db.scalar(
        select(Application).where(
            Application.student_id == payload.student_id,
            Application.job_id == payload.job_id,
        )
    )
    if existed:
        raise HTTPException(status_code=400, detail='Already applied')

    record = Application(**payload.model_dump(exclude={'id', 'create_time'}))
    db.add(record)
    db.commit()
    db.refresh(record)
    return schemas.Application.model_validate(record)


@router.get('', response_model=list[schemas.Application])
def list_applications(
    student_id: int | None = Query(default=None),
    job_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[schemas.Application]:
    query = select(Application)

    if current_user.role == 'student':
        query = query.where(Application.student_id == current_user.id)
    elif current_user.role == 'company':
        company_job_ids = db.scalars(select(Job.id).where(Job.company_id == current_user.id)).all()
        if not company_job_ids:
            return []
        query = query.where(Application.job_id.in_(company_job_ids))

    if student_id is not None:
        if current_user.role == 'student' and student_id != current_user.id:
            raise HTTPException(status_code=403, detail='Permission denied')
        query = query.where(Application.student_id == student_id)

    if job_id is not None:
        if current_user.role == 'company':
            owner_job = db.get(Job, job_id)
            if not owner_job or owner_job.company_id != current_user.id:
                raise HTTPException(status_code=403, detail='Permission denied')
        query = query.where(Application.job_id == job_id)

    rows = db.scalars(query.order_by(Application.id.desc())).all()
    return [schemas.Application.model_validate(item) for item in rows]


@router.patch('/{application_id}/status', response_model=schemas.Application)
def update_status(
    application_id: int,
    payload: schemas.ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.Application:
    record = db.get(Application, application_id)
    if not record:
        raise HTTPException(status_code=404, detail='Application not found')

    # --- Ownership check ---
    if current_user.role == 'student':
        if current_user.id != record.student_id:
            raise HTTPException(status_code=403, detail='Permission denied')
    elif current_user.role == 'company':
        job = db.get(Job, record.job_id)
        if not job or job.company_id != current_user.id:
            raise HTTPException(status_code=403, detail='Permission denied')

    # --- Validate status transition ---
    error = _validate_transition(record.status, payload.status, current_user.role)
    if error:
        raise HTTPException(status_code=400, detail=error)

    record.status = payload.status

    # Auto-send notification message to student
    _NOTIFY_STATUSES = {'submitted', 'viewed', 'reviewing', 'to_contact', 'interview_scheduled', 'interviewing', 'accepted', 'rejected'}
    if current_user.role in {'company', 'admin'} and payload.status in _NOTIFY_STATUSES:
        status_labels = {
            'submitted': '已投递',
            'viewed': '已查看',
            'reviewing': '筛选中',
            'to_contact': '待沟通',
            'interview_scheduled': '面试已安排',
            'interviewing': '面试中',
            'accepted': '已通过',
            'rejected': '已淘汰',
        }
        job = db.get(Job, record.job_id)
        job_name = job.job_name if job else f'岗位{record.job_id}'
        msg = Message(
            sender_id=current_user.id,
            receiver_id=record.student_id,
            content=f'[系统通知] 您投递的「{job_name}」状态已更新为：{status_labels.get(payload.status, payload.status)}',
            message_type='system',
        )
        db.add(msg)
        create_notification_sync(
            db,
            user_id=record.student_id,
            title='投递状态更新',
            content=f'您投递的「{job_name}」状态已更新为：{status_labels.get(payload.status, payload.status)}',
            notification_type='application',
            related_id=application_id,
        )

    db.commit()
    db.refresh(record)
    return schemas.Application.model_validate(record)


@router.get('/company-view', response_model=list[schemas.ApplicationDetailOut])
def company_view_applications(
    job_id: int | None = Query(default=None),
    school: str | None = Query(default=None),
    major: str | None = Query(default=None),
    skill: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[schemas.ApplicationDetailOut]:
    if current_user.role not in {'company', 'admin'}:
        raise HTTPException(status_code=403, detail='Permission denied')

    query = select(Application).order_by(Application.id.desc())

    if status:
        query = query.where(Application.status == status)
    if job_id is not None:
        query = query.where(Application.job_id == job_id)

    rows = db.scalars(query).all()
    result: list[schemas.ApplicationDetailOut] = []

    for app in rows:
        job = db.get(Job, app.job_id)
        if not job:
            continue
        if current_user.role == 'company' and job.company_id != current_user.id:
            continue

        student = db.get(StudentProfile, app.student_id)
        resume = db.get(Resume, app.resume_id)
        if not student:
            continue

        if school and school.lower() not in (student.school or '').lower():
            continue
        if major and major.lower() not in (student.major or '').lower():
            continue
        if skill and skill not in (student.skills or []):
            continue

        result.append(
            schemas.ApplicationDetailOut(
                application_id=app.id,
                status=app.status,
                apply_time=app.create_time,
                update_time=app.update_time,
                job_id=job.id,
                job_name=job.job_name,
                student_id=student.user_id,
                student_name=student.name,
                school=student.school,
                major=student.major,
                grade=student.grade,
                skills=student.skills or [],
                resume_content=resume.content_json if resume else None,
                resume_file_url=resume.file_url if resume else '',
            )
        )

    return result


@router.get('/company-view/{application_id}', response_model=schemas.ApplicationDetailOut)
def company_view_application_detail(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.ApplicationDetailOut:
    if current_user.role not in {'company', 'admin'}:
        raise HTTPException(status_code=403, detail='Permission denied')

    app = db.get(Application, application_id)
    if not app:
        raise HTTPException(status_code=404, detail='Application not found')

    job = db.get(Job, app.job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')

    if current_user.role == 'company' and job.company_id != current_user.id:
        raise HTTPException(status_code=403, detail='Permission denied')

    student = db.get(StudentProfile, app.student_id)
    if not student:
        raise HTTPException(status_code=404, detail='Student not found')

    resume = db.get(Resume, app.resume_id)

    return schemas.ApplicationDetailOut(
        application_id=app.id,
        status=app.status,
        apply_time=app.create_time,
        update_time=app.update_time,
        job_id=job.id,
        job_name=job.job_name,
        student_id=student.user_id,
        student_name=student.name,
        school=student.school,
        major=student.major,
        grade=student.grade,
        skills=student.skills or [],
        resume_content=resume.content_json if resume else None,
        resume_file_url=resume.file_url if resume else '',
    )
