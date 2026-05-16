"""Tests for admin college insights aggregation."""
from __future__ import annotations

from app.models import Application, CompanyProfile, Job, Resume, StudentProfile, User
from app.security import hash_password


def test_admin_college_insights(db, client):
    admin = User(
        role='admin',
        name='Admin',
        email='collegeadmin@test.com',
        password_hash=hash_password('123456'),
        status='active',
    )
    db.add(admin)

    company_user = User(
        role='company',
        name='Insight Corp',
        email='insightcorp@test.com',
        password_hash=hash_password('123456'),
        status='active',
    )
    db.add(company_user)
    db.flush()
    db.add(
        CompanyProfile(
            user_id=company_user.id,
            company_name='Insight Corp',
            credit_code='IC1001',
            contact_name='张老师',
            contact_phone='13500001111',
            status='approved',
            scale='100-500人',
        )
    )
    db.flush()

    job = Job(
        company_id=company_user.id,
        job_name='后端开发工程师',
        job_type='后端开发',
        city='重庆',
        salary_min=12000,
        salary_max=18000,
        education='本科',
        description='build services',
        requirement='python',
        skill_tags=['Python', 'FastAPI'],
    )
    db.add(job)
    db.flush()

    student_user = User(
        role='student',
        name='张三',
        email='college-student@test.com',
        password_hash=hash_password('123456'),
        status='active',
    )
    db.add(student_user)
    db.flush()
    db.add(
        StudentProfile(
            user_id=student_user.id,
            name='张三',
            student_no='S001',
            school='计算机学院',
            major='软件工程',
            grade='2024级',
            phone='13800000000',
            email='college-student@test.com',
            skills=['Python'],
        )
    )
    db.flush()

    resume = Resume(student_id=student_user.id, resume_type='online', content_json={'skills': ['Python']})
    db.add(resume)
    db.flush()
    db.add(
        Application(
            student_id=student_user.id,
            job_id=job.id,
            resume_id=resume.id,
            status='reviewing',
        )
    )
    db.commit()

    admin_token = client.post(
        '/api/users/login',
        json={'email': 'collegeadmin@test.com', 'password': '123456'},
    ).json()['token']

    resp = client.get(
        '/api/admin/college-insights',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert len(payload) == 1
    college = payload[0]
    assert college['name'] == '计算机学院'
    assert college['grades'] == ['2024级']
    assert college['companies'][0]['name'] == 'Insight Corp'
    assert college['jobs'][0]['applicationCount'] == 1
    assert college['applications'][0]['studentName'] == '张三'
