from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Announcement,
    Application,
    CompanyProfile,
    Job,
    Message,
    Resume,
    StudentIntention,
    StudentProfile,
    User,
)
from app.security import hash_password


# ===================================================================
#  默认账号（三个角色各一个，密码统一 123456，方便演示）
#
#   角色      邮箱                      密码
#   学生      student@test.com          123456
#   企业      company@test.com          123456
#   管理员    admin@test.com            123456
# ===================================================================

DEFAULT_PASSWORD = '123456'


def create_student(
    db: Session,
    *,
    name: str,
    email: str,
    password: str,
    student_no: str,
    school: str,
    major: str,
    grade: str,
    phone: str,
    skills: list[str],
    awards: list[str] | None = None,
    internships: list[str] | None = None,
    projects: list[str] | None = None,
    bio: str = '',
    expected_job: str,
    expected_city: str,
    expected_salary: str,
    expected_industry: str,
) -> tuple[User, Resume]:
    user = User(
        role='student',
        name=name,
        email=email,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.flush()

    db.add(
        StudentProfile(
            user_id=user.id,
            name=name,
            student_no=student_no,
            school=school,
            major=major,
            grade=grade,
            phone=phone,
            email=email,
            skills=skills,
            awards=awards or [],
            internships=internships or [],
            projects=projects or [],
            bio=bio or f'{name}，{major}专业，目标岗位 {expected_job}。',
            verified=True,
        )
    )

    db.add(
        StudentIntention(
            student_id=user.id,
            expected_job=expected_job,
            expected_city=expected_city,
            expected_salary=expected_salary,
            expected_industry=expected_industry,
            arrival_time='2026-07',
            accept_internship=True,
        )
    )

    resume = Resume(
        student_id=user.id,
        resume_type='online',
        content_json={'skills': skills, 'major': major, 'school': school},
        version_no=1,
    )
    db.add(resume)
    db.flush()

    return user, resume


def seed_data(db: Session) -> None:
    user_count = db.scalar(select(func.count()).select_from(User))
    if user_count and user_count > 0:
        return

    # ---------- 管理员 ----------
    admin = User(
        role='admin',
        name='系统管理员',
        email='admin@test.com',
        password_hash=hash_password(DEFAULT_PASSWORD),
    )

    # ---------- 企业用户 ----------
    company1 = User(
        role='company',
        name='星云科技HR',
        email='company@test.com',
        password_hash=hash_password(DEFAULT_PASSWORD),
    )
    company2 = User(
        role='company',
        name='极光实验室HR',
        email='company2@test.com',
        password_hash=hash_password(DEFAULT_PASSWORD),
    )
    db.add_all([admin, company1, company2])
    db.flush()

    db.add_all(
        [
            CompanyProfile(
                user_id=company1.id,
                company_name='星云科技有限公司',
                credit_code='91310000MA1G0000X1',
                contact_name='王招聘',
                contact_phone='13800001111',
                status='approved',
                description='专注云原生与 AI 基础设施的技术企业，团队200+人。',
                industry='互联网/云计算',
                scale='200-500人',
                address='上海市浦东新区',
                website='https://nebula-tech.example.com',
                welfare_tags=['五险一金', '弹性工作', '学习基金', '免费三餐'],
            ),
            CompanyProfile(
                user_id=company2.id,
                company_name='极光智能实验室',
                credit_code='91330000MA1G0000X2',
                contact_name='李招聘',
                contact_phone='13700003333',
                status='approved',
                description='AI 平台研发团队，面向校园招聘实习岗。',
                industry='人工智能',
                scale='50-200人',
                address='杭州市西湖区',
                website='https://aurora-labs.example.com',
                welfare_tags=['培训体系', '弹性工时', '实习转正'],
            ),
        ]
    )

    # ---------- 学生用户 ----------
    student1, resume1 = create_student(
        db,
        name='李华',
        email='student@test.com',
        password=DEFAULT_PASSWORD,
        student_no='20250001',
        school='东港大学',
        major='计算机科学与技术',
        grade='2025',
        phone='13900002222',
        skills=['Python', 'Linux', 'Docker', 'Kubernetes', 'MySQL'],
        awards=['省级程序设计竞赛二等奖'],
        internships=['某云计算公司SRE实习3个月'],
        projects=['校园微服务监控平台', '容器化部署自动化工具'],
        bio='李华，计算机科学与技术专业，熟悉云原生技术栈，目标SRE/运维开发方向。',
        expected_job='SRE/运维开发',
        expected_city='上海',
        expected_salary='8000-12000',
        expected_industry='互联网/云计算',
    )
    student2, resume2 = create_student(
        db,
        name='张三',
        email='student2@test.com',
        password=DEFAULT_PASSWORD,
        student_no='20250002',
        school='北桥大学',
        major='软件工程',
        grade='2025',
        phone='13600004444',
        skills=['Java', 'Spring Boot', 'MySQL', 'Redis', 'Docker'],
        awards=['校级优秀毕业设计'],
        internships=['某互联网公司后端开发实习4个月'],
        projects=['电商秒杀系统', '分布式任务调度框架'],
        bio='张三，软件工程专业，擅长Java后端开发，有分布式系统实践经验。',
        expected_job='后端开发工程师',
        expected_city='杭州',
        expected_salary='10000-15000',
        expected_industry='人工智能',
    )
    student3, resume3 = create_student(
        db,
        name='王五',
        email='student3@test.com',
        password=DEFAULT_PASSWORD,
        student_no='20250003',
        school='东港大学',
        major='人工智能',
        grade='2025',
        phone='13500005555',
        skills=['Python', 'PyTorch', 'SQL', 'TensorFlow', 'Docker'],
        awards=['数学建模竞赛一等奖', 'Kaggle银牌'],
        internships=['某AI公司算法实习3个月'],
        projects=['图像分类模型优化', '自然语言处理情感分析系统'],
        bio='王五，人工智能专业，专注深度学习与NLP方向，目标AI工程师。',
        expected_job='AI算法工程师',
        expected_city='杭州',
        expected_salary='12000-18000',
        expected_industry='人工智能',
    )

    # ---------- 岗位 ----------
    job1 = Job(
        company_id=company1.id,
        job_name='SRE 运维开发实习生',
        job_type='SRE/运维',
        city='上海',
        salary_min=8000,
        salary_max=12000,
        education='本科',
        description='负责云平台可靠性保障与自动化运维工具开发，参与容器化部署与监控告警体系建设。',
        requirement='1. 熟悉Linux操作系统\n2. 了解Docker/Kubernetes\n3. 掌握Python或Go\n4. 有监控/日志系统使用经验优先',
        skill_tags=['Linux', 'Docker', 'Kubernetes', 'Python'],
        status='active',
        deadline='2026-06-30',
    )
    job2 = Job(
        company_id=company2.id,
        job_name='Java 后端开发实习生',
        job_type='后端开发',
        city='杭州',
        salary_min=9000,
        salary_max=13000,
        education='本科',
        description='参与AI平台后端服务开发，负责接口设计、数据库优化与微服务治理。',
        requirement='1. 熟练掌握Java/Spring Boot\n2. 熟悉MySQL/Redis\n3. 了解微服务架构\n4. 有实际项目经验优先',
        skill_tags=['Java', 'Spring Boot', 'MySQL', 'Redis', 'Docker'],
        status='active',
        deadline='2026-06-30',
    )
    job3 = Job(
        company_id=company2.id,
        job_name='AI 算法实习生',
        job_type='AI/算法',
        city='杭州',
        salary_min=10000,
        salary_max=16000,
        education='本科',
        description='参与模型训练流水线搭建与AI服务部署，研究前沿算法并落地到业务场景。',
        requirement='1. 熟练掌握Python\n2. 熟悉PyTorch/TensorFlow\n3. 有机器学习项目经验\n4. 了解数据处理流程',
        skill_tags=['Python', 'PyTorch', 'TensorFlow', 'SQL'],
        status='active',
        deadline='2026-06-30',
    )
    job4 = Job(
        company_id=company1.id,
        job_name='前端开发实习生',
        job_type='前端开发',
        city='上海',
        salary_min=8000,
        salary_max=11000,
        education='本科',
        description='参与内部管理系统与数据可视化平台的前端开发，使用Vue3技术栈。',
        requirement='1. 熟悉HTML/CSS/JavaScript\n2. 掌握Vue或React\n3. 了解HTTP协议\n4. 有组件化开发经验优先',
        skill_tags=['Vue', 'JavaScript', 'HTML', 'CSS'],
        status='active',
        deadline='2026-06-30',
    )
    db.add_all([job1, job2, job3, job4])
    db.flush()

    # ---------- 投递记录 ----------
    db.add_all(
        [
            Application(student_id=student1.id, job_id=job1.id, resume_id=resume1.id, status='submitted'),
            Application(student_id=student1.id, job_id=job2.id, resume_id=resume1.id, status='reviewing'),
            Application(student_id=student2.id, job_id=job1.id, resume_id=resume2.id, status='submitted'),
            Application(student_id=student2.id, job_id=job2.id, resume_id=resume2.id, status='to_contact'),
            Application(student_id=student3.id, job_id=job2.id, resume_id=resume3.id, status='submitted'),
            Application(student_id=student3.id, job_id=job3.id, resume_id=resume3.id, status='accepted'),
        ]
    )

    # ---------- 消息 ----------
    db.add(
        Message(
            sender_id=company1.id,
            receiver_id=student1.id,
            content='李华同学你好，看到你投递了SRE实习岗位，方便这周三下午进行线上面试吗？',
            message_type='text',
        )
    )
    db.add(
        Message(
            sender_id=student1.id,
            receiver_id=company1.id,
            content='您好，可以的，请问是腾讯会议还是飞书？',
            message_type='text',
        )
    )
    db.add(
        Message(
            sender_id=company2.id,
            receiver_id=student3.id,
            content='王五同学，恭喜你通过了AI算法实习的面试，请尽快确认入职时间。',
            message_type='system',
        )
    )

    # ---------- 公告 ----------
    db.add(
        Announcement(
            title='2026年春季校园招聘周启动通知',
            content='各位同学：\n\n2026年春季校园招聘周将于下周一正式开始，届时将有20+家企业入驻平台发布实习及校招岗位。请提前完善个人档案和简历，祝大家求职顺利！\n\n—— 就业指导中心',
            status='published',
            pinned=True,
        )
    )
    db.add(
        Announcement(
            title='平台功能更新：AI模拟面试上线',
            content='AI模拟面试功能已正式上线，学生可在AI助手页面上传学习内容，系统将自动生成定制面试题并给出反馈建议。欢迎体验！',
            status='published',
            pinned=False,
        )
    )

    db.commit()
