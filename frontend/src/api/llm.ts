import client from './client';
import type { LLMProvider } from '../types';

export const llmApi = {
  list: () =>
    client.get<LLMProvider[]>('/llm/providers').then(r => r.data),

  getActive: () =>
    client.get<LLMProvider>('/llm/providers/active').then(r => r.data),

  add: (name: string, api_base: string, api_key: string, model: string) =>
    client.post<{ id: number }>('/llm/providers', null, {
      params: { name, api_base, api_key, model },
    }).then(r => r.data),

  update: (id: number, name: string, api_base: string, api_key: string, model: string) =>
    client.put(`/llm/providers/${id}`, null, {
      params: { name, api_base, api_key, model },
    }),

  activate: (id: number) =>
    client.post(`/llm/providers/${id}/activate`),

  delete: (id: number) =>
    client.delete(`/llm/providers/${id}`),
};
