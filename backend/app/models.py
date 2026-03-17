from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db import Base


def now_utc() -> datetime:
    return datetime.utcnow()


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default='active')
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class StudentProfile(Base):
    __tablename__ = 'student_profiles'

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    student_no: Mapped[str] = mapped_column(String(100))
    school: Mapped[str] = mapped_column(String(255))
    major: Mapped[str] = mapped_column(String(255))
    grade: Mapped[str] = mapped_column(String(50))
    phone: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(255))
    skills: Mapped[list] = mapped_column(JSON, default=list)
    awards: Mapped[list] = mapped_column(JSON, default=list)
    internships: Mapped[list] = mapped_column(JSON, default=list)
    projects: Mapped[list] = mapped_column(JSON, default=list)
    bio: Mapped[str] = mapped_column(Text, default='')
    verified: Mapped[bool] = mapped_column(Boolean, default=False)


class StudentIntention(Base):
    __tablename__ = 'student_intentions'

    student_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    expected_job: Mapped[str] = mapped_column(String(100), default='')
    expected_city: Mapped[str] = mapped_column(String(100), default='')
    expected_salary: Mapped[str] = mapped_column(String(100), default='')
    expected_industry: Mapped[str] = mapped_column(String(100), default='')
    arrival_time: Mapped[str] = mapped_column(String(100), default='')
    accept_internship: Mapped[bool] = mapped_column(Boolean, default=True)


class Resume(Base):
    __tablename__ = 'resumes'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    resume_type: Mapped[str] = mapped_column(String(20), default='online')
    content_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    file_url: Mapped[str] = mapped_column(String(500), default='')
    version_no: Mapped[int] = mapped_column(Integer, default=1)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class CompanyProfile(Base):
    __tablename__ = 'company_profiles'

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    company_name: Mapped[str] = mapped_column(String(255))
    credit_code: Mapped[str] = mapped_column(String(100))
    license_url: Mapped[str] = mapped_column(String(500), default='')
    contact_name: Mapped[str] = mapped_column(String(100))
    contact_phone: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default='pending', index=True)
    description: Mapped[str] = mapped_column(Text, default='')
    industry: Mapped[str] = mapped_column(String(100), default='')
    scale: Mapped[str] = mapped_column(String(100), default='')
    address: Mapped[str] = mapped_column(String(255), default='')
    website: Mapped[str] = mapped_column(String(255), default='')
    promo_image_url: Mapped[str] = mapped_column(String(500), default='')
    welfare_tags: Mapped[list] = mapped_column(JSON, default=list)


class Job(Base):
    __tablename__ = 'jobs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    job_name: Mapped[str] = mapped_column(String(255), index=True)
    job_type: Mapped[str] = mapped_column(String(100))
    city: Mapped[str] = mapped_column(String(100), index=True)
    salary_min: Mapped[int] = mapped_column(Integer)
    salary_max: Mapped[int] = mapped_column(Integer)
    education: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(LONGTEXT)
    requirement: Mapped[str] = mapped_column(LONGTEXT)
    skill_tags: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default='active', index=True)
    deadline: Mapped[str] = mapped_column(String(50), default='')
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now_utc, index=True)


class Application(Base):
    __tablename__ = 'applications'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey('jobs.id'), index=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey('resumes.id'))
    status: Mapped[str] = mapped_column(String(30), default='submitted', index=True)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    update_time: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc)


class Message(Base):
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    receiver_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    content: Mapped[str] = mapped_column(LONGTEXT)
    message_type: Mapped[str] = mapped_column(String(30), default='text')
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now_utc, index=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)


class AuditRecord(Base):
    __tablename__ = 'audit_records'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    audit_type: Mapped[str] = mapped_column(String(50), index=True)
    target_id: Mapped[int] = mapped_column(Integer)
    auditor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    result: Mapped[str] = mapped_column(String(50))
    remark: Mapped[str] = mapped_column(Text, default='')
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now_utc, index=True)


class Announcement(Base):
    __tablename__ = 'announcements'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    content: Mapped[str] = mapped_column(LONGTEXT)
    status: Mapped[str] = mapped_column(String(20), default='draft', index=True)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    update_time: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc)


class VerificationRequest(Base):
    __tablename__ = 'verification_requests'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    fields: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default='pending', index=True)
    result: Mapped[str] = mapped_column(Text, default='')
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    update_time: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc)


class AIInterviewTemplate(Base):
    __tablename__ = 'ai_interview_templates'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    name: Mapped[str] = mapped_column(String(100))
    job_title: Mapped[str] = mapped_column(String(100))
    question_types: Mapped[list] = mapped_column(JSON, default=list)
    difficulty: Mapped[str] = mapped_column(String(20), default='medium')
    question_count: Mapped[int] = mapped_column(Integer, default=5)
    scoring_rules: Mapped[str] = mapped_column(Text, default='')
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    update_time: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc)


class AIInterviewSession(Base):
    __tablename__ = 'ai_interview_sessions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey('ai_interview_templates.id'), nullable=True, index=True
    )
    company_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True, index=True)
    student_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True, index=True)
    session_type: Mapped[str] = mapped_column(String(20), index=True)  # screening/mock
    learning_content: Mapped[str] = mapped_column(LONGTEXT, default='')
    generated_questions: Mapped[list] = mapped_column(JSON, default=list)
    evaluation_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now_utc, index=True)


class Favorite(Base):
    __tablename__ = 'favorites'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey('jobs.id'), index=True)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class ViewHistory(Base):
    __tablename__ = 'view_history'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey('jobs.id'), index=True)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now_utc, index=True)


class OperationLog(Base):
    __tablename__ = 'operation_logs'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    action: Mapped[str] = mapped_column(String(50), index=True)
    target_type: Mapped[str] = mapped_column(String(50), default='')
    target_id: Mapped[int] = mapped_column(Integer, default=0)
    detail: Mapped[str] = mapped_column(Text, default='')
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now_utc, index=True)


class RecommendConfig(Base):
    __tablename__ = 'recommend_config'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    collaborative_weight: Mapped[float] = mapped_column(default=0.4)
    content_weight: Mapped[float] = mapped_column(default=0.6)
    update_time: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc)
