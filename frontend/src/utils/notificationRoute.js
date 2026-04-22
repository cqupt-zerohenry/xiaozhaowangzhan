function normalizeText(value) {
  return String(value || "").toLowerCase();
}

function containsAny(text, patterns) {
  return patterns.some((item) => text.includes(item));
}

export function resolveNotificationTarget(notification, role = "student") {
  const type = String(notification?.notification_type || "").toLowerCase();
  const text = `${normalizeText(notification?.title)} ${normalizeText(notification?.content)}`;

  if (type === "announcement" || containsAny(text, ["公告", "announcement"])) {
    return { path: "/notifications", query: { type: "announcement" }, label: "查看公告" };
  }

  if (type === "application" || containsAny(text, ["投递", "申请", "岗位状态"])) {
    if (role === "student") {
      if (containsAny(text, ["面试", "邀约"])) {
        return { path: "/my-applications", query: { status: "interviewing" }, label: "查看投递进度" };
      }
      if (containsAny(text, ["通过", "offer", "录用"])) {
        return { path: "/my-applications", query: { status: "accepted" }, label: "查看结果" };
      }
      if (containsAny(text, ["淘汰", "拒绝"])) {
        return { path: "/my-applications", query: { status: "rejected" }, label: "查看结果" };
      }
      return { path: "/my-applications", label: "查看投递进度" };
    }
    if (role === "company") {
      return { path: "/company-center", query: { tab: "candidates" }, label: "查看候选人" };
    }
    return { path: "/admin-center", query: { tab: "overview" }, label: "查看详情" };
  }

  if (type === "interview" || containsAny(text, ["面试", "interview"])) {
    if (role === "company") {
      return { path: "/ai", query: { tab: "company-screening" }, label: "查看 AI 初筛" };
    }
    return { path: "/interview-flow", label: "进入面试" };
  }

  if (containsAny(text, ["核验"])) {
    if (role === "student") {
      return { path: "/profile", query: { tab: "insight" }, label: "查看核验结果" };
    }
    if (role === "company") {
      return { path: "/company-center", query: { tab: "certification" }, label: "查看核验请求" };
    }
    return { path: "/admin-center", query: { tab: "verifications" }, label: "审批核验" };
  }

  if (containsAny(text, ["审核", "资质"]) && role === "admin") {
    return { path: "/companies", label: "进入审核" };
  }

  if (containsAny(text, ["消息", "沟通", "chat"])) {
    return { path: "/messages", label: "查看消息" };
  }

  return { path: "/notifications", label: "查看通知" };
}

export function compareNotifications(a, b) {
  if (Boolean(a?.is_read) !== Boolean(b?.is_read)) {
    return a?.is_read ? 1 : -1;
  }
  const priority = {
    application: 0,
    interview: 1,
    system: 2,
    announcement: 3
  };
  const pa = priority[String(a?.notification_type || "").toLowerCase()] ?? 9;
  const pb = priority[String(b?.notification_type || "").toLowerCase()] ?? 9;
  if (pa !== pb) return pa - pb;
  return Number(b?.id || 0) - Number(a?.id || 0);
}

