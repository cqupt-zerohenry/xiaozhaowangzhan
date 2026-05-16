"""Tests for enhanced company talent recommendations."""
from __future__ import annotations

from app.models import CompanyProfile, Job, StudentIntention, StudentProfile, User
from app.security import hash_password


def _setup_company_with_jobs(db, client):
    company_user = User(
        role='company',
        name='Talent Corp',
        email='talentcorp@test.com',
        password_hash=hash_password('123456'),
        status='active',
    )
    db.add(company_user)
    db.flush()
    db.add(
        CompanyProfile(
            user_id=company_user.id,
            company_name='Talent Corp',
            credit_code='TC1001',
            contact_name='HR',
            contact_phone='123456',
            status='approved',
            industry='互联网',
        )
    )
    db.flush()

    backend_job = Job(
        company_id=company_user.id,
        job_name='后端开发工程师',
        job_type='后端开发',
        city='重庆',
        salary_min=12000,
        salary_max=20000,
        education='本科',
        description='build api',
        requirement='python fastapi',
        skill_tags=['Python', 'FastAPI', 'SQL'],
    )
    frontend_job = Job(
        company_id=company_user.id,
        job_name='前端开发工程师',
        job_type='前端开发',
        city='上海',
        salary_min=10000,
        salary_max=18000,
        education='本科',
        description='build ui',
        requirement='vue javascript',
        skill_tags=['Vue', 'JavaScript'],
    )
    db.add_all([backend_job, frontend_job])
    db.flush()

    company_token = client.post(
        '/api/users/login',
        json={'email': 'talentcorp@test.com', 'password': '123456'},
    ).json()['token']
    return company_user.id, company_token, backend_job.id, frontend_job.id


def _create_student(db, email, name, skills, expected_city, expected_job):
    user = User(
        role='student',
        name=name,
        email=email,
        password_hash=hash_password('123456'),
        status='active',
    )
    db.add(user)
    db.flush()
    db.add(
        StudentProfile(
            user_id=user.id,
            name=name,
            student_no=f'S-{user.id}',
            school='重庆邮电大学',
            major='软件工程',
            grade='2024级',
            phone='13800000000',
            email=email,
            skills=skills,
        )
    )
    db.add(
        StudentIntention(
            student_id=user.id,
            expected_city=expected_city,
            expected_industry='互联网',
            expected_job=expected_job,
            accept_internship=True,
        )
    )
    db.commit()
    return user.id


def test_company_recommendations_support_job_filter(db, client):
    company_id, company_token, backend_job_id, _ = _setup_company_with_jobs(db, client)
    best_student_id = _create_student(
        db,
        email='backend@test.com',
        name='后端同学',
        skills=['Python', 'FastAPI', 'Redis'],
        expected_city='重庆',
        expected_job='后端',
    )
    _create_student(
        db,
        email='frontend@test.com',
        name='前端同学',
        skills=['Vue', 'JavaScript'],
        expected_city='上海',
        expected_job='前端',
    )

    resp = client.get(
        f'/api/companies/{company_id}/recommendations?job_id={backend_job_id}',
        headers={'Authorization': f'Bearer {company_token}'},
    )

    assert resp.status_code == 200
    rows = resp.json()['results']
    assert rows[0]['student_id'] == best_student_id
    assert rows[0]['target_job_id'] == backend_job_id
    assert 'Python' in rows[0]['matched_skills']
    assert isinstance(rows[0]['missing_skills'], list)
    assert '技能' in rows[0]['reason']


def test_company_recommendations_choose_best_job_per_student(db, client):
    company_id, company_token, backend_job_id, frontend_job_id = _setup_company_with_jobs(db, client)
    _create_student(
        db,
        email='backend2@test.com',
        name='后端候选人',
        skills=['Python', 'FastAPI'],
        expected_city='重庆',
        expected_job='后端',
    )
    frontend_student_id = _create_student(
        db,
        email='frontend2@test.com',
        name='前端候选人',
        skills=['Vue', 'JavaScript'],
        expected_city='上海',
        expected_job='前端',
    )

    resp = client.get(
        f'/api/companies/{company_id}/recommendations',
        headers={'Authorization': f'Bearer {company_token}'},
    )

    assert resp.status_code == 200
    rows = resp.json()['results']
    student_rows = {item['student_id']: item for item in rows}
    assert student_rows[frontend_student_id]['target_job_id'] == frontend_job_id
    assert student_rows[frontend_student_id]['target_job_id'] != backend_job_id
