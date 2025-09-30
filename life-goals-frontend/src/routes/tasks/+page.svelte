<script lang="ts">
  import { onMount } from 'svelte';
  const API = '/api';

  type Due = {
    date?: string;
    datetime?: string;
    timezone?: string;
    is_recurring?: boolean;
    string?: string;
  };
  type Task = {
    id: string;
    content: string;
    description?: string;
    priority?: number; // 1..4 (4 is highest in Todoist)
    project_id?: string;
    labels?: string[];
    due?: Due;
    url?: string;
    is_completed?: boolean;
    section_id?: string;
  };

  type Project = { id: string; name: string };
  type Section = { id: string; name: string; project_id: string };

  let csrf = '';
  let authenticated = false;
  let tasks: Task[] = [];
  let msg = '';
  let projects: Project[] = [];
  let sections: Section[] = [];
  const PAGE_SIZE = 5;
  let offset = 0;
  let hasMore = true;
  let loadingMore = false;

  // Filters / sorting
  let filterProject = '';
  let filterSection = '';
  let filterText = '';
  let filterPriority = '' as '' | '4' | '3' | '2' | '1';
  let sortBy: 'due' | 'priority' | 'none' = 'none';
  let sortDir: 'asc' | 'desc' = 'asc';
  let initialized = false;

  // Simple localStorage cache helpers
  type CacheEntry<T> = { ts: number; data: T };
  function getCache<T>(key: string, maxAgeMs: number): T | null {
    try {
      const raw = localStorage.getItem(key);
      if (!raw) return null;
      const entry = JSON.parse(raw) as CacheEntry<T>;
      if (!entry || typeof entry.ts !== 'number') return null;
      if (Date.now() - entry.ts > maxAgeMs) return null;
      return entry.data;
    } catch { return null; }
  }
  function setCache<T>(key: string, data: T) {
    try { localStorage.setItem(key, JSON.stringify({ ts: Date.now(), data })); } catch {}
  }

  function applyFiltersFromURL() {
    const sp = new URLSearchParams(window.location.search);
    filterProject = sp.get('project') ?? '';
    filterSection = sp.get('section') ?? '';
    filterPriority = (sp.get('priority') as any) ?? '';
    filterText = sp.get('q') ?? '';
    sortBy = ((sp.get('sort') as any) ?? 'none');
    sortDir = ((sp.get('dir') as any) ?? 'asc');
  }

  function updateURLFromFilters() {
    const sp = new URLSearchParams();
    if (filterProject) sp.set('project', filterProject);
    if (filterSection) sp.set('section', filterSection);
    if (filterPriority) sp.set('priority', filterPriority);
    if (filterText) sp.set('q', filterText);
    if (sortBy !== 'none') sp.set('sort', sortBy);
    if (sortDir !== 'asc') sp.set('dir', sortDir);
    const qs = sp.toString();
    const newUrl = `${window.location.pathname}${qs ? `?${qs}` : ''}${window.location.hash}`;
    window.history.replaceState({}, '', newUrl);
  }

  // New task form state
  let newContent = '';
  let newDescription = '';
  let newPriority: number = 1; // 1..4
  let newDueString = '';
  let newLabels = '';
  let creating = false;
  let createError = '';

  async function refreshSession() {
    const r = await fetch(`${API}/session`, { credentials: 'include' });
    const j = await r.json();
    csrf = j.csrf;
    authenticated = !!j.authenticated;
  }

  async function loadTasks() {
    const r = await fetch(`/tasks/data?offset=0&limit=${PAGE_SIZE}`, { credentials: 'include' });
    if (!r.ok) {
      msg = await r.text();
      return;
    }
    const data = (await r.json()) as Task[];
    tasks = data;
    offset = data.length;
    hasMore = data.length === PAGE_SIZE;
  }

  async function loadMore() {
    if (!hasMore || loadingMore) return;
    loadingMore = true;
    try {
      const r = await fetch(`/tasks/data?offset=${offset}&limit=${PAGE_SIZE}`, { credentials: 'include' });
      if (!r.ok) {
        msg = await r.text();
        return;
      }
      const data = (await r.json()) as Task[];
      tasks = tasks.concat(data);
      offset += data.length;
      hasMore = data.length === PAGE_SIZE;
    } finally {
      loadingMore = false;
    }
  }

  async function loadProjects() {
    const cacheKey = 'projects:v1';
    const cached = getCache<Project[]>(cacheKey, 10 * 60 * 1000);
    if (cached) projects = cached;
    const r = await fetch(`${API}/projects`, { credentials: 'include' });
    if (r.ok) {
      const data = await r.json();
      projects = data;
      setCache(cacheKey, data);
    }
  }

  async function loadSections(projectId?: string) {
    const url = new URL(`${API}/sections`, window.location.origin);
    if (projectId) url.searchParams.set('project_id', projectId);
    const cacheKey = `sections:v1:${projectId ?? 'all'}`;
    const cached = getCache<Section[]>(cacheKey, 10 * 60 * 1000);
    if (cached) sections = cached;
    const r = await fetch(url, { credentials: 'include' });
    if (r.ok) {
      const data = await r.json();
      sections = data;
      setCache(cacheKey, data);
    }
  }

  async function logout() {
    const r = await fetch(`${API}/logout`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'X-CSRF-Token': csrf }
    });
    if (r.ok) window.location.href = '/';
  }

  async function createTask() {
    createError = '';
    if (!newContent.trim()) {
      createError = 'Content is required';
      return;
    }
    creating = true;
    try {
      const body: Record<string, any> = { content: newContent.trim() };
      if (filterProject) body.project_id = filterProject;
      if (filterSection) body.section_id = filterSection;
      if (newDescription.trim()) body.description = newDescription.trim();
      const p = Number(newPriority);
      if (p >= 1 && p <= 4) body.priority = p;
      if (newDueString.trim()) body.due_string = newDueString.trim();
      const labels = newLabels.split(',').map((s) => s.trim()).filter(Boolean);
      if (labels.length) body.labels = labels;

      const r = await fetch(`${API}/create_task`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrf
        },
        body: JSON.stringify(body)
      });
      if (!r.ok) {
        const text = await r.text();
        throw new Error(text || 'Failed to create task');
      }
      // Optional: use the returned task; then reload to reflect filters/order
      await loadTasks();
      // Reset form
      newContent = '';
      newDescription = '';
      newPriority = 1;
      newDueString = '';
      newLabels = '';
    } catch (e: any) {
      createError = e?.message ?? String(e);
    } finally {
      creating = false;
    }
  }

  function formatDue(due?: Due): string | null {
    if (!due) return null;
    if (due.string) return due.string;
    const iso = due.datetime ?? due.date;
    if (!iso) return null;
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString();
  }

  function priorityLabel(p?: number): string | null {
    if (!p) return null;
    switch (p) {
      case 4: return 'P1 (Urgent)';
      case 3: return 'P2 (High)';
      case 2: return 'P3 (Medium)';
      case 1: return 'P4 (Normal)';
      default: return `P${p}`;
    }
  }

  function priorityClasses(p?: number): string {
    switch (p) {
      case 4: return 'bg-red-100 text-red-800';
      case 3: return 'bg-amber-100 text-amber-800';
      case 2: return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  }

  function isOverdue(due?: Due): boolean {
    const iso = due?.datetime ?? due?.date;
    if (!iso) return false;
    const d = new Date(iso);
    return !Number.isNaN(d.getTime()) && d.getTime() < Date.now();
  }

  function projectName(id?: string): string | null {
    if (!id) return null;
    const p = projects.find((x) => x.id === id);
    return p ? p.name : id;
  }

  function sectionName(id?: string): string | null {
    if (!id) return null;
    const s = sections.find((x) => x.id === id);
    return s ? s.name : id;
  }

  onMount(async () => {
    await refreshSession();
    if (!authenticated) {
      window.location.href = '/'; // route guard
      return;
    }
    await loadTasks();
  });

  $: if (filterProject) {
    // When project filter changes, refresh sections for that project
    loadSections(filterProject);
    // Reset section filter if it doesn't belong
    if (filterSection && !sections.find((s) => s.id === filterSection && s.project_id === filterProject)) {
      filterSection = '';
    }
  }

  // Keep URL in sync with filters
  $: if (initialized) {
    updateURLFromFilters();
  }

  function filteredAndSorted(tasksIn: Task[]): Task[] {
    let arr = tasksIn.filter((t) => {
      if (filterProject && t.project_id !== filterProject) return false;
      if (filterSection && t.section_id !== filterSection) return false;
      if (filterPriority && String(t.priority ?? '') !== filterPriority) return false;
      if (filterText) {
        const q = filterText.toLowerCase();
        const hay = `${t.content} ${t.description ?? ''} ${(t.labels ?? []).join(' ')}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
    if (sortBy === 'due') {
      const score = (t: Task) => {
        const iso = t.due?.datetime ?? t.due?.date;
        if (!iso) return Infinity;
        const d = new Date(iso).getTime();
        return Number.isNaN(d) ? Infinity : d;
      };
      arr.sort((a, b) => (score(a) - score(b)) * (sortDir === 'asc' ? 1 : -1));
    } else if (sortBy === 'priority') {
      const score = (t: Task) => t.priority ? (5 - t.priority) : 0; // higher first
      arr.sort((a, b) => (score(a) - score(b)) * (sortDir === 'asc' ? 1 : -1));
    }
    return arr;
  }
</script>

<div class="max-w-6xl mx-auto p-6 space-y-4">

  <div class="flex items-center justify-between">
    <h1 class="text-2xl font-bold">My Tasks</h1>
    <div class="flex items-center gap-2">
      <a href="/tasks/new" class="px-3 py-2 rounded bg-blue-600 text-white">Create Task</a>
      <button class="px-3 py-2 rounded bg-gray-200" on:click={logout}>Logout</button>
      <button class="px-3 py-2 rounded bg-green-600 text-white" on:click={() => window.location.href = '/api/notion/connect'}>Connect Notion</button>
      <button class="px-3 py-2 rounded bg-red-600 text-white" on:click={() => window.location.href = '/api/login'}>Connect Todoist</button>
    </div>
  </div>

  

  {#if msg}<pre class="bg-red-50 p-3 rounded">{msg}</pre>{/if}

  {#if tasks.length === 0}
    <div class="text-gray-600">No tasks found.</div>
  {:else}
    <div class="grid gap-3 md:gap-4">
      {#each tasks as t}
        <div class="rounded border border-gray-200 p-4 bg-white shadow-sm">
          <div class="flex items-start justify-between gap-3">
            <div class="space-y-1">
              <div class="font-medium text-gray-900">{t.content}</div>
              {#if t.description}
                <div class="text-sm text-gray-600 whitespace-pre-wrap">{t.description}</div>
              {/if}
            </div>
            {#if t.priority}
              <span class={`text-xs px-2 py-1 rounded ${priorityClasses(t.priority)}`}>
                {priorityLabel(t.priority)}
              </span>
            {/if}
          </div>

          <div class="mt-3 flex flex-wrap items-center gap-2 text-sm text-gray-700">
            {#if t.project_id}
              <span class="px-2 py-1 rounded bg-gray-100 text-gray-700">Project: {projectName(t.project_id)}</span>
            {/if}
            {#if t.section_id}
              <span class="px-2 py-1 rounded bg-gray-100 text-gray-700">Section: {sectionName(t.section_id)}</span>
            {/if}
            {#if t.due}
              <span class={`px-2 py-1 rounded ${isOverdue(t.due) ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
                Due: {formatDue(t.due)}
              </span>
            {/if}
            {#if t.labels && t.labels.length}
              {#each t.labels as label}
                <span class="px-2 py-1 rounded bg-blue-50 text-blue-700">#{label}</span>
              {/each}
            {/if}
            {#if t.url}
              <a class="px-2 py-1 rounded bg-purple-50 text-purple-700 hover:underline" href={t.url} target="_blank" rel="noreferrer">Open</a>
            {/if}
          </div>
        </div>
      {/each}
    </div>
    {#if hasMore}
      <div class="mt-4">
        <button class="px-4 py-2 rounded bg-gray-100 hover:bg-gray-200 disabled:opacity-50" on:click={loadMore} disabled={loadingMore}>
          {loadingMore ? 'Loading…' : 'Show more'}
        </button>
      </div>
    {/if}
  {/if}
</div>
