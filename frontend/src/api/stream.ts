import { config } from '../config';

export function buildStreamUrl(query: string, convId?: number): string {
  const params = new URLSearchParams({ query });
  if (convId) params.set('conv_id', String(convId));
  return `${config.API_URL}/chat/stream?${params.toString()}`;
}
