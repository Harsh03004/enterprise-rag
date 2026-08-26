import { apiFetch } from "./client";

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface User {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export async function register(
  data: RegisterRequest,
): Promise<User> {
  const response = await apiFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });

  return response.json();
}

export async function login(
  data: LoginRequest,
): Promise<LoginResponse> {
  const response = await apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });

  return response.json();
}