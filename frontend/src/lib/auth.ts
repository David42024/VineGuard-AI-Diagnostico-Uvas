import api, { LoginResponse, User } from "./api";

export async function login(
  username: string,
  password: string
): Promise<LoginResponse> {
  const response = await api.post<LoginResponse>("/auth/login", {
    username,
    password,
  });
  return response.data;
}

export async function logout(): Promise<void> {
  try {
    await api.post("/auth/logout");
  } catch {
    // Ignore logout errors
  }
}

export async function getSession(): Promise<User> {
  const response = await api.get<User>("/auth/me");
  return response.data;
}
