export const APPLICATION_STATUS_MAP = {
  submitted: '已投递',
  viewed: '已查看',
  reviewing: '筛选中',
  to_contact: '待沟通',
  interview_scheduled: '已安排面试',
  interviewing: '面试中',
  accepted: '已通过',
  rejected: '已淘汰',
  withdrawn: '已撤回'
};

export const APPLICATION_STATUS_OPTIONS = Object.entries(APPLICATION_STATUS_MAP).map(([value, label]) => ({ value, label }));

export const APPLICATION_STATUS_TRANSITIONS = {
  submitted: ['viewed', 'reviewing', 'to_contact', 'rejected', 'withdrawn'],
  viewed: ['reviewing', 'to_contact', 'rejected', 'withdrawn'],
  reviewing: ['to_contact', 'interview_scheduled', 'rejected', 'withdrawn'],
  to_contact: ['interview_scheduled', 'interviewing', 'rejected', 'withdrawn'],
  interview_scheduled: ['interviewing', 'rejected', 'withdrawn'],
  interviewing: ['accepted', 'rejected', 'withdrawn'],
  accepted: [],
  rejected: [],
  withdrawn: []
};

export function applicationStatusLabel(status) {
  return APPLICATION_STATUS_MAP[status] || status || '未知';
}

export function canApplicationStatusTransition(currentStatus, nextStatus) {
  if (!currentStatus || !nextStatus) return false;
  const allowed = APPLICATION_STATUS_TRANSITIONS[currentStatus] || [];
  return allowed.includes(nextStatus);
}

export const COMPANY_STATUS_MAP = {
  approved: '已通过',
  pending: '待审核',
  rejected: '已驳回',
  disabled: '已禁用'
};

export function companyStatusLabel(status) {
  return COMPANY_STATUS_MAP[status] || status || '未知';
}

export const VERIFY_STATUS_MAP = {
  pending: '待处理',
  approved: '已通过',
  rejected: '已驳回'
};

export function verifyStatusLabel(status) {
  return VERIFY_STATUS_MAP[status] || status || '未知';
}
