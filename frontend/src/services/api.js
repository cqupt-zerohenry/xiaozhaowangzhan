const API_BASE = import.meta.env.VITE_API_BASE || '/api';

function getToken() {
  try {
    const stored = JSON.parse(localStorage.getItem('auth') || 'null');
    return stored?.token || '';
  } catch (err) {
    return '';
  }
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'Request failed');
  }

  if (response.status === 204) {
    return null;
  }
  return response.json();
}

export function login(payload) {
  return request('/users/login', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function fetchUsers() {
  return request('/users');
}

export function registerStudent(payload) {
  return request('/auth/register/student', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function registerCompany(payload) {
  return request('/auth/register/company', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function fetchJobs(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, value);
    }
  });
  const queryString = query.toString();
  return request(`/jobs${queryString ? `?${queryString}` : ''}`);
}

export function createJob(payload) {
  return request('/jobs', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function updateJob(id, payload) {
  return request(`/jobs/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  });
}

export function deleteJob(id) {
  return request(`/jobs/${id}`, { method: 'DELETE' });
}

export function fetchCompanies() {
  return request('/companies');
}

export function fetchCompany(id) {
  return request(`/companies/${id}`);
}

export function updateCompany(id, payload) {
  return request(`/companies/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  });
}

export function submitCompanyCertification(id) {
  return request(`/companies/${id}/certification`, { method: 'POST' });
}

export function updateCompanyStatus(id, payload) {
  return request(`/companies/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify(payload)
  });
}

export function fetchCompanyRecommendations(id) {
  return request(`/companies/${id}/recommendations`);
}

export function createVerificationRequest(companyId, payload) {
  return request(`/companies/${companyId}/verify-student`, {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function fetchCompanyVerificationRequests(companyId) {
  return request(`/companies/${companyId}/verify-requests`);
}

export function fetchStudentProfile(id) {
  return request(`/students/${id}`);
}

export function fetchStudents() {
  return request('/students');
}

export function updateStudentProfile(id, payload) {
  return request(`/students/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  });
}

export function fetchStudentIntention(id) {
  return request(`/students/${id}/intention`);
}

export function updateStudentIntention(id, payload) {
  return request(`/students/${id}/intention`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  });
}

export function fetchResumes(id) {
  return request(`/students/${id}/resumes`);
}

export function createResume(id, payload) {
  return request(`/students/${id}/resumes`, {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function fetchMessages(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, value);
    }
  });
  const queryString = query.toString();
  return request(`/messages${queryString ? `?${queryString}` : ''}`);
}

export function sendMessage(payload) {
  return request('/messages', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function createApplication(payload) {
  return request('/applications', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function fetchApplications(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, value);
    }
  });
  const queryString = query.toString();
  return request(`/applications${queryString ? `?${queryString}` : ''}`);
}

export function fetchCompanyApplications(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, value);
    }
  });
  const queryString = query.toString();
  return request(`/applications/company-view${queryString ? `?${queryString}` : ''}`);
}

export function updateApplicationStatus(id, payload) {
  return request(`/applications/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify(payload)
  });
}

export function jobRecommend(payload) {
  return request('/ai/job-recommend', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function jobMatch(payload) {
  return request('/ai/job-match', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function rag(payload) {
  return request('/ai/rag', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function interview(payload) {
  return request('/ai/interview', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function mockInterview(payload) {
  return request('/ai/mock-interview', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function fetchInterviewTemplates(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, value);
    }
  });
  const queryString = query.toString();
  return request(`/ai/interview-templates${queryString ? `?${queryString}` : ''}`);
}

export function createInterviewTemplate(payload) {
  return request('/ai/interview-templates', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function updateInterviewTemplate(id, payload) {
  return request(`/ai/interview-templates/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  });
}

export function deleteInterviewTemplate(id) {
  return request(`/ai/interview-templates/${id}`, { method: 'DELETE' });
}

export function screeningInterview(payload) {
  return request('/ai/screening-interview', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function studentMockUpload(payload) {
  return request('/ai/student-mock-upload', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function fetchInterviewSessions(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, value);
    }
  });
  const queryString = query.toString();
  return request(`/ai/interview-sessions${queryString ? `?${queryString}` : ''}`);
}

export function fetchAudits() {
  return request('/admin/audits');
}

export function createAudit(payload) {
  return request('/admin/audits', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function fetchAnnouncements() {
  return request('/admin/announcements');
}

export function createAnnouncement(payload) {
  return request('/admin/announcements', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function updateAnnouncement(id, payload) {
  return request(`/admin/announcements/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  });
}

export function deleteAnnouncement(id) {
  return request(`/admin/announcements/${id}`, { method: 'DELETE' });
}

export function fetchStats() {
  return request('/admin/stats');
}

export function updateUserStatus(userId, payload) {
  return request(`/admin/users/${userId}/status`, {
    method: 'PATCH',
    body: JSON.stringify(payload)
  });
}

export function fetchVerificationRequests() {
  return request('/admin/verification-requests');
}

export function updateVerificationRequest(id, payload) {
  return request(`/admin/verification-requests/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload)
  });
}

// Favorites
export function fetchFavorites() {
  return request('/favorites');
}

export function addFavorite(jobId) {
  return request('/favorites', {
    method: 'POST',
    body: JSON.stringify({ job_id: jobId })
  });
}

export function removeFavorite(jobId) {
  return request(`/favorites/${jobId}`, { method: 'DELETE' });
}

// File upload
export function uploadFile(file) {
  const token = getToken();
  const formData = new FormData();
  formData.append('file', file);
  return fetch(`${API_BASE}/files/upload`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData
  }).then(res => {
    if (!res.ok) throw new Error('Upload failed');
    return res.json();
  });
}

// Messages
export function fetchUnreadCount() {
  return request('/messages/unread-count');
}

export function markMessageRead(messageId) {
  return request(`/messages/${messageId}/read`, { method: 'PATCH' });
}

// Jobs
export function fetchJob(id) {
  return request(`/jobs/${id}`);
}

export function fetchSimilarJobs(id) {
  return request(`/jobs/${id}/similar`);
}

// Admin enhanced
export function fetchEnhancedStats() {
  return request('/admin/enhanced-stats');
}

export function resetUserPassword(userId, payload) {
  return request(`/admin/users/${userId}/reset-password`, {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function fetchOperationLogs() {
  return request('/admin/operation-logs');
}

export function fetchRecommendConfig() {
  return request('/admin/recommend-config');
}

export function updateRecommendConfig(payload) {
  return request('/admin/recommend-config', {
    method: 'PUT',
    body: JSON.stringify(payload)
  });
}

// Online users
export function fetchOnlineUsers() {
  return request('/online-users');
}

// Knowledge Base
export function fetchKnowledgeBases() {
  return request('/ai/knowledge-bases');
}

export function createKnowledgeBase(payload) {
  return request('/ai/knowledge-bases', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function updateKnowledgeBase(kbId, payload) {
  return request(`/ai/knowledge-bases/${kbId}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  });
}

export function deleteKnowledgeBase(kbId) {
  return request(`/ai/knowledge-bases/${kbId}`, { method: 'DELETE' });
}

export function fetchKBDocuments(kbId) {
  return request(`/ai/knowledge-bases/${kbId}/documents`);
}

export function addKBDocumentPaste(kbId, payload) {
  return request(`/ai/knowledge-bases/${kbId}/documents`, {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function uploadKBDocument(kbId, file) {
  const token = getToken();
  const formData = new FormData();
  formData.append('file', file);
  return fetch(`${API_BASE}/ai/knowledge-bases/${kbId}/documents/upload`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData
  }).then(res => {
    if (!res.ok) throw new Error('Upload failed');
    return res.json();
  });
}

export function resumeOptimize(payload) {
  return request('/ai/resume-optimize', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function deleteKBDocument(kbId, docId) {
  return request(`/ai/knowledge-bases/${kbId}/documents/${docId}`, { method: 'DELETE' });
}

export function fetchRecommendEvaluation() {
  return request('/admin/recommend-evaluation');
}

export function fetchEmploymentAnalytics() {
  return request('/admin/employment-analytics');
}

// AI Job Assistant (floating ball chat)
export function jobAssistant(payload) {
  return request('/ai/job-assistant', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}
