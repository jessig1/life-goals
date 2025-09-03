import type { RequestHandler } from './$types';

type Due = {
  date?: string;
  datetime?: string;
};
type Task = {
  id: string;
  content: string;
  created_at?: string;
  due?: Due;
};

function taskTimestamp(t: Task): number {
  // Prefer created_at, then due datetime/date, else 0
  const iso = t.created_at ?? t.due?.datetime ?? t.due?.date;
  if (!iso) return 0;
  const n = Date.parse(iso);
  return Number.isNaN(n) ? 0 : n;
}

export const GET: RequestHandler = async ({ fetch, url }) => {
  const offset = Math.max(0, Number(url.searchParams.get('offset') ?? '0') || 0);
  const limit = Math.max(1, Math.min(100, Number(url.searchParams.get('limit') ?? '5') || 5));

  const r = await fetch('/api/tasks', { credentials: 'include' });
  if (!r.ok) {
    return new Response(await r.text(), { status: r.status });
  }
  const items = (await r.json()) as Task[];
  const sorted = items.slice().sort((a, b) => taskTimestamp(b) - taskTimestamp(a));
  const page = sorted.slice(offset, offset + limit);
  return new Response(JSON.stringify(page), {
    status: 200,
    headers: { 'Content-Type': 'application/json' }
  });
};
