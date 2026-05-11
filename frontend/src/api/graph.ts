import client from './client';
import type { KnowledgeGraph } from '../types';

export const graphApi = {
  getGraph: () =>
    client.get<KnowledgeGraph>('/graph').then(r => r.data),

  clearGraph: () =>
    client.delete('/graph'),
};
