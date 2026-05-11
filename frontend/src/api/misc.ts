import client from './client';
import type { MemoryItem, CacheEntry, Stats } from '../types';

export const miscApi = {
  getMemory: () =>
    client.get<MemoryItem[]>('/memory').then(r => r.data),

  getCache: () =>
    client.get<CacheEntry[]>('/cache').then(r => r.data),

  deleteCacheEntry: (id: number) =>
    client.delete(`/cache/${id}`),

  clearCache: () =>
    client.delete('/cache'),

  getStats: () =>
    client.get<Stats>('/stats').then(r => r.data),
};
