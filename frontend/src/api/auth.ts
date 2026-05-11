import client from './client';
import type { AuthResponse } from '../types';

export const authApi = {
  login: (name: string, password: string) =>
    client.post<AuthResponse>('/auth/login', null, { params: { name, password } }).then(r => r.data),

  register: (name: string, password: string) =>
    client.post<AuthResponse>('/auth/register', null, { params: { name, password } }).then(r => r.data),
};
