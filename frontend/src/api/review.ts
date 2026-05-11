import client from './client';
import type { ReviewCard } from '../types';

export const reviewApi = {
  getDueCards: () =>
    client.get<ReviewCard[]>('/review/cards').then(r => r.data),

  reviewCard: (cardId: number, quality: number) =>
    client.post(`/review/cards/${cardId}/review`, null, { params: { quality } }),

  deleteCard: (cardId: number) =>
    client.delete(`/review/cards/${cardId}`),
};
