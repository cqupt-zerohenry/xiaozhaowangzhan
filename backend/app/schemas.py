from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    role: str = Field(..., examples=['student', 'company', 'admin'])
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserStatusUpdate(BaseModel):
    status: str = Field(..., examples=['active', 'disabled'])


class UserOut(ORMModel, UserBase):
    id: int
    status: str
    create_time: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    user: UserOut
    token: str


class StudentRegister(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=6)
    student_no: str
    school: str
    major: str
    grade: str
    phone: str
    skills: list[str] = []
    awards: list[str] = []
    internships: list[str] = []
    projects: list[str] = []
    bio: str = ''


class CompanyRegister(BaseModel):
    company_name: str
    credit_code: str
    contact_name: str
    contact_phone: str
    email: EmailStr
    password: str = Field(..., min_length=6)
    description: str = ''
    industry: str = ''
    scale: str = ''
    address: str = ''
    website: str = ''
    welfare_tags: list[str] = []


class StudentProfile(ORMModel):
    user_id: int
    name: str
    student_no: str
    school: str
    major: str
    grade: str
    phone: str
    email: EmailStr
    skills: list[str] = []
    awards: list[str] = []
    internships: list[str] = []
    projects: list[str] = []
    bio: str = ''
    verified: bool = False


class StudentIntention(ORMModel):
    student_id: int
    expected_job: str = ''
    expected_city: str = ''
    expected_salary: str = ''
    expected_industry: str = ''
    arrival_time: str = ''
    accept_internship: bool = True


class Resume(ORMModel):
    id: int | None = None
    student_id: int
    resume_type: str = Field(..., examples=['online', 'file'])
    content_json: dict | None = None
    file_url: str = ''
    version_no: int = 1
    create_time: datetime | None = None


class CompanyProfile(ORMModel):
    user_id: int
    company_name: str
    credit_code: str
    license_url: str = ''
    contact_name: str
    contact_phone: str
    status: str = 'pending'
    description: str = ''
    industry: str = ''
    scale: str = ''
    address: str = ''
    website: str = ''
    promo_image_url: str = ''
    welfare_tags: list[str] = []


class CompanyStatusUpdate(BaseModel):
    status: str
    remark: str = ''


class JobBase(BaseModel):
    company_id: int
    job_name: str
    job_type: str
    city: str
    salary_min: int = Field(..., ge=0)
    salary_max: int = Field(..., ge=0)
    education: str
    description: str
    requirement: str
    skill_tags: list[str] = []
    status: str = 'active'
    deadline: str = ''

    def model_post_init(self, __context: object) -> None:
        if self.salary_max < self.salary_min:
            self.salary_min, self.salary_max = self.salary_max, self.salary_min


class JobOut(ORMModel, JobBase):
    id: int
    create_time: datetime


class Application(ORMModel):
    id: int | None = None
    student_id: int
    job_id: int
    resume_id: int
    status: str = 'submitted'
    create_time: datetime | None = None


class ApplicationStatusUpdate(BaseModel):
    status: str


class ApplicationDetailOut(BaseModel):
    application_id: int
    status: str
    apply_time: datetime
    job_id: int
    job_name: str
    student_id: int
    student_name: str
    school: str
    major: str
    grade: str
    skills: list[str] = []
    resume_content: dict | None = None
    resume_file_url: str = ''


class Message(ORMModel):
    id: int | None = None
    sender_id: int
    receiver_id: int
    content: str
    message_type: str = 'text'
    create_time: datetime | None = None
    is_read: bool = False


class AuditRecord(ORMModel):
    id: int | None = None
    audit_type: str
    target_id: int
    auditor_id: int
    result: str
    remark: str = ''
    create_time: datetime | None = None


class Announcement(ORMModel):
    id: int | None = None
    title: str
    content: str
    status: str = 'draft'
    pinned: bool = False
    create_time: datetime | None = None
    update_time: datetime | None = None


class JobRecommendResult(BaseModel):
    job_id: int
    job_name: str
    final_score: int
    content_score: int
    collaborative_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    reason: str


class JobRecommendResponse(BaseModel):
    matches: list[JobRecommendResult]


class JobMatchRequest(BaseModel):
    student_id: int | None = None
    skills: list[str] = []


class TalentRecommendResult(BaseModel):
    student_id: int
    name: str
    major: str
    grade: str
    skills: list[str]
    match_score: int
    reason: str


class TalentRecommendResponse(BaseModel):
    results: list[TalentRecommendResult]


class StatsResponse(BaseModel):
    student_total: int
    company_total: int
    job_total: int
    application_total: int


class InterviewRequest(BaseModel):
    job_title: str
    skills: list[str] = []


class InterviewResponse(BaseModel):
    questions: list[str]
    evaluation: str


class RagRequest(BaseModel):
    question: str
    kb_id: int | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class RagSourceItem(BaseModel):
    chunk_content: str
    document_title: str
    relevance_score: float


class RagResponse(BaseModel):
    answer: str
    learning_path: list[str]
    skill_tree: list[str]
    sources: list[RagSourceItem] = []


class MockInterviewRequest(BaseModel):
    job_title: str


class MockInterviewResponse(BaseModel):
    questions: list[str]
    feedback: str


class AIInterviewTemplateBase(BaseModel):
    name: str
    job_title: str
    question_types: list[str] = []
    difficulty: str = 'medium'
    question_count: int = Field(default=5, ge=1, le=20)
    scoring_rules: str = ''


class AIInterviewTemplateCreate(AIInterviewTemplateBase):
    company_id: int | None = None


class AIInterviewTemplateUpdate(BaseModel):
    name: str | None = None
    job_title: str | None = None
    question_types: list[str] | None = None
    difficulty: str | None = None
    question_count: int | None = Field(default=None, ge=1, le=20)
    scoring_rules: str | None = None


class AIInterviewTemplateOut(ORMModel, AIInterviewTemplateBase):
    id: int
    company_id: int
    create_time: datetime
    update_time: datetime


class ScreeningInterviewRequest(BaseModel):
    template_id: int
    candidate_name: str = ''
    candidate_summary: str = ''
    candidate_skills: list[str] = []
    candidate_experience: str = ''
    kb_id: int | None = None


class DimensionScore(BaseModel):
    dimension: str
    score: int
    comment: str


class ScreeningInterviewResponse(BaseModel):
    session_id: int
    template: AIInterviewTemplateOut
    questions: list[str]
    evaluation: str
    score: int
    recommendation: str
    focus_areas: list[str] = []
    dimension_scores: list[DimensionScore] = []


class StudentMockUploadRequest(BaseModel):
    job_title: str
    learning_content: str = Field(..., min_length=10)
    kb_id: int | None = None
    learning_focus: list[str] = []
    question_types: list[str] = []
    difficulty: str = 'medium'
    question_count: int = Field(default=5, ge=1, le=20)


class StudentMockUploadResponse(BaseModel):
    session_id: int
    questions: list[str]
    feedback: str
    strengths: list[str] = []
    improvements: list[str] = []
    next_actions: list[str] = []
    dimension_scores: list[DimensionScore] = []


class AIInterviewSessionOut(ORMModel):
    id: int
    template_id: int | None = None
    company_id: int | None = None
    student_id: int | None = None
    session_type: str
    learning_content: str = ''
    generated_questions: list[str] = []
    evaluation_json: dict | None = None
    create_time: datetime


class VerificationRequestCreate(BaseModel):
    student_id: int
    fields: list[str] = []


class VerificationRequestOut(ORMModel):
    id: int
    company_id: int
    student_id: int
    fields: list[str] = []
    status: str
    result: str
    create_time: datetime
    update_time: datetime


class VerificationRequestUpdate(BaseModel):
    status: str
    result: str = ''


class FavoriteOut(ORMModel):
    id: int
    user_id: int
    job_id: int
    create_time: datetime


class FavoriteCreate(BaseModel):
    job_id: int


class ViewHistoryOut(ORMModel):
    id: int
    user_id: int
    job_id: int
    create_time: datetime


class OperationLogOut(ORMModel):
    id: int
    user_id: int
    action: str
    target_type: str = ''
    target_id: int = 0
    detail: str = ''
    create_time: datetime


class RecommendConfigOut(ORMModel):
    id: int
    collaborative_weight: float
    content_weight: float
    update_time: datetime


class RecommendConfigUpdate(BaseModel):
    collaborative_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    content_weight: float = Field(default=0.6, ge=0.0, le=1.0)


class UnreadCountResponse(BaseModel):
    count: int


class EnhancedStatsResponse(BaseModel):
    student_total: int
    company_total: int
    job_total: int
    application_total: int
    hot_job_types: list[dict] = []
    active_companies: list[dict] = []
    recommendation_stats: dict = {}


class PasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=6)


class SimilarJobOut(BaseModel):
    job_id: int
    job_name: str
    similarity_score: int
    common_skills: list[str]


class FileUploadResponse(BaseModel):
    file_url: str
    filename: str


# ---- Knowledge Base ----

class KnowledgeBaseCreate(BaseModel):
    name: str
    description: str = ''


class KnowledgeBaseOut(ORMModel):
    id: int
    owner_id: int
    owner_role: str
    name: str
    description: str
    create_time: datetime
    update_time: datetime


class KnowledgeDocumentCreate(BaseModel):
    title: str
    content: str = ''


class KnowledgeDocumentOut(ORMModel):
    id: int
    kb_id: int
    title: str
    source_type: str
    chunk_count: int
    status: str
    file_url: str
    create_time: datetime


class ResumeOptimizeRequest(BaseModel):
    job_title: str


class ResumeOptimizeResponse(BaseModel):
    summary: str = ''
    strengths: list[str] = []
    suggestions: list[str] = []
    missing_skills: list[str] = []
    bio_rewrite: str = ''


class JobAssistantRequest(BaseModel):
    message: str
    history: list[dict] = []


class JobAssistantJobItem(BaseModel):
    job_id: int
    job_name: str
    company_name: str = ''
    city: str = ''
    salary: str = ''


class JobAssistantResponse(BaseModel):
    reply: str
    recommended_jobs: list[JobAssistantJobItem] = []


class RecommendEvaluationResponse(BaseModel):
    total_students: int
    evaluated_students: int
    cold_start_users: int
    total_jobs: int
    total_applications: int
    precision_at_5: float
    recall_at_5: float
    hit_rate: float
    coverage: float
    avg_matched_skills: float
    algorithm_version: str
    evaluation_time: str


class MajorHeatmapItem(BaseModel):
    major: str
    application_count: int


class JobTypePopularityItem(BaseModel):
    job_type: str
    application_count: int


class ConversionFunnelItem(BaseModel):
    status: str
    count: int


class SkillGapItem(BaseModel):
    skill: str
    missing_count: int


class CompanyActivityItem(BaseModel):
    company_name: str
    total_received: int
    total_reviewed: int
    response_rate: float


class MonthlyTrendItem(BaseModel):
    month: str
    application_count: int


class EmploymentAnalyticsResponse(BaseModel):
    major_heatmap: list[MajorHeatmapItem] = []
    job_type_popularity: list[JobTypePopularityItem] = []
    conversion_funnel: list[ConversionFunnelItem] = []
    skill_gap: list[SkillGapItem] = []
    company_activity: list[CompanyActivityItem] = []
    monthly_trend: list[MonthlyTrendItem] = []


# ---- Email Verification ----

class SendCodeRequest(BaseModel):
    email: EmailStr
    purpose: str = 'register'


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str
    purpose: str = 'register'


class PasswordResetByEmailRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str = Field(..., min_length=6)


# ---- Resume Parsing ----

class ResumeParseResponse(BaseModel):
    name: str = ''
    phone: str = ''
    email: str = ''
    school: str = ''
    major: str = ''
    skills: list[str] = []
    experience: list[str] = []
    raw_text: str = ''


# ---- Notifications ----

class NotificationOut(ORMModel):
    id: int
    user_id: int
    title: str
    content: str
    notification_type: str
    related_id: int | None = None
    is_read: bool
    create_time: datetime


# ---- Interview Flow ----

class InterviewFlowStartRequest(BaseModel):
    template_id: int | None = None
    job_title: str = ''
    question_count: int = Field(default=5, ge=1, le=20)


class InterviewFlowQuestionOut(BaseModel):
    index: int
    question: str
    time_limit: int = 120


class InterviewFlowStartResponse(BaseModel):
    session_id: int
    questions: list[InterviewFlowQuestionOut]
    total_time: int


class InterviewFlowAnswerRequest(BaseModel):
    session_id: int
    question_index: int
    answer: str


class InterviewFlowAnswerResponse(BaseModel):
    feedback: str
    score: int


class InterviewFlowResultResponse(BaseModel):
    session_id: int
    total_score: int
    dimension_scores: list[DimensionScore] = []
    overall_feedback: str
    question_feedbacks: list[dict] = []


# ---- Company Analytics ----

class CompanyAnalyticsResponse(BaseModel):
    job_stats: list[dict] = []
    talent_source: list[dict] = []
    funnel: list[ConversionFunnelItem] = []
    trend: list[MonthlyTrendItem] = []


# ---- Student Analytics ----

class StudentAnalyticsResponse(BaseModel):
    skill_competitiveness: list[dict] = []
    salary_benchmark: dict = {}
    market_trends: list[dict] = []
    application_stats: dict = {}


# ---- View History Detail ----

class ViewHistoryDetailOut(BaseModel):
    id: int
    job_id: int
    job_name: str = ''
    company_name: str = ''
    create_time: datetime
