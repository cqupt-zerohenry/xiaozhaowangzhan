import { computed, ref } from "vue";
import { login as loginRequest } from "../services/api";

const stored = JSON.parse(localStorage.getItem("auth") || "null");

const user = ref(stored?.user ?? null);
const token = ref(stored?.token ?? "");

const role = computed(() => user.value?.role || "guest");
const isAuthed = computed(() => Boolean(user.value));

function persist() {
  if (!user.value) {
    localStorage.removeItem("auth");
    return;
  }
  localStorage.setItem("auth", JSON.stringify({ user: user.value, token: token.value }));
}

async function login(payload) {
  const result = await loginRequest(payload);
  user.value = result.user;
  token.value = result.token;
  persist();
  return result;
}

function logout() {
  user.value = null;
  token.value = "";
  persist();
}

export function useAuth() {
  return {
    user,
    token,
    role,
    isAuthed,
    login,
    logout
  };
}
