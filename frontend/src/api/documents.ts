import client from './client';
import type { Document } from '../types';

export const documentApi = {
  listDocuments: () =>
    client.get<Document[]>('/documents').then(r => r.data),

  uploadDocument: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return client.post<Document>('/documents/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    }).then(r => r.data);
  },

  deleteDocument: (docId: number) =>
    client.delete(`/documents/${docId}`),
};
