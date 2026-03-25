import { api } from "./http";

export type User = {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
};

export async function getCurrentUser() {
  const { data } = await api.get<User>("/auth/me");
  return data;
}

export async function login(payload: { email: string; password: string }) {
  const { data } = await api.post<User>("/auth/login", payload);
  return data;
}
