import client from './client';
import type { Conversation, Message, ExportResult } from '../types';

export const chatApi = {
  listConversations: () =>
    client.get<Conversation[]>('/conversations').then(r => r.data),

  getMessages: (convId: number) =>
    client.get<Message[]>(`/conversations/${convId}/messages`).then(r => r.data),

  createConversation: () =>
    client.post<{ id: number }>('/conversations', null, { params: { title: '新对话' } }).then(r => r.data),

  deleteConversation: (convId: number) =>
    client.delete(`/conversations/${convId}`),

  exportConversation: (convId: number) =>
    client.get<ExportResult>(`/conversations/${convId}/export`).then(r => r.data),
};
