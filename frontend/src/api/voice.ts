import api from './client';
import type { VoiceResponse } from '../types';

export async function processText(
  text: string, language: string, sessionId: string,
  farmerId?: number, country?: string,
): Promise<VoiceResponse> {
  const res = await api.post('/voice/text', {
    text, language, session_id: sessionId,
    farmer_id: farmerId, country: country || 'IN',
  });
  return res.data;
}

export async function processPhoto(
  photo: File, text: string, language: string, sessionId: string,
  farmerId?: number, country?: string,
): Promise<VoiceResponse> {
  const form = new FormData();
  form.append('photo', photo);
  form.append('text', text);
  form.append('language', language);
  form.append('session_id', sessionId);
  if (farmerId) form.append('farmer_id', String(farmerId));
  form.append('country', country || 'IN');
  const res = await api.post('/voice/photo', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}
