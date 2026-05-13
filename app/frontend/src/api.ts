import type { ProcessResponse, LedgerEntry, LedgerForm, SampleApplication } from './types';

const BASE = '/api';

export async function fetchSamples(): Promise<SampleApplication[]> {
  const res = await fetch(`${BASE}/sample`);
  const data = await res.json();
  return data.samples ?? [];
}

export async function processApplication(text: string): Promise<ProcessResponse> {
  const res = await fetch(`${BASE}/process`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ application_text: text }),
  });
  return res.json();
}

export async function confirmResult(
  resultId: string,
  modifications?: Record<string, unknown>,
): Promise<ProcessResponse> {
  const res = await fetch(`${BASE}/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ result_id: resultId, modifications }),
  });
  return res.json();
}

export async function exportResult(resultId: string, format: 'json' | 'csv'): Promise<string> {
  const res = await fetch(`${BASE}/export/${resultId}?format=${format}`);
  const data = await res.json();
  return format === 'csv' ? data.csv : JSON.stringify(data, null, 2);
}

export async function fetchStatus(): Promise<{ llama_server_ready: boolean; model: string }> {
  const res = await fetch(`${BASE}/status`);
  return res.json();
}

// ─── Ledger CRUD ────────────────────────────────────

export async function fetchLedger(): Promise<LedgerEntry[]> {
  const res = await fetch(`${BASE}/ledger`);
  const data = await res.json();
  return data.entries ?? [];
}

export async function createLedger(form: LedgerForm): Promise<LedgerEntry> {
  const res = await fetch(`${BASE}/ledger`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(form),
  });
  return res.json();
}

export async function updateLedger(resultId: string, form: LedgerForm): Promise<LedgerEntry> {
  const res = await fetch(`${BASE}/ledger/${resultId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(form),
  });
  return res.json();
}

export async function deleteLedger(resultId: string): Promise<void> {
  await fetch(`${BASE}/ledger/${resultId}`, { method: 'DELETE' });
}