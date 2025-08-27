

<script lang="ts">
  import { onMount } from 'svelte';
  export const ssr = false;
  const API = 'http://localhost:8000';
  await fetch('http://localhost:8000/tasks', { credentials: 'include' })

  let authenticated = false;
  let csrf = '';
  let rawMode = false;

  // Optional filters
  let filter = '';
  let project_id = '';
  let section_id = '';
  let label = '';

  let loading = false;
  let errorMsg = '';
  let tasks: any[] = [];

  async function checkSession() {
    const r = await fetch(`${API}/session`, { credentials: 'include' });
    const j = await r.json();
    authenticated = !!j.authenticated;
    csrf = j.csrf;
  }

  async function loadTasks() {
    errorMsg = '';
    loading = true;
    tasks = [];
    try {
      const url = new URL(`${API}/tasks`);
      if (filter) url.searchParams.set('filter', filter);
      if (project_id) url.searchParams.set('project_id', project_id);
      if (section_id) url.searchParams.set('section_id', section_id);
      if (label) url.searchParams.set('label', label);

      const res = await fetch(url.toString(), {
        method: 'GET',
        credentials: 'include'
      });
      const text = await res.text();
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}\n${text}`);
      tasks = JSON.parse(text);
    } catch (e: any) {
      errorMsg = e.message || String(e);
    } finally {
      loading = false;
    }
  }

  function priorityBadge(p: number) {
    const map = {1: 'P1', 2: 'P2', 3: 'P3', 4: 'P4'};
    return map[p as 1|2|3|4] ?? String(p);
  }

  onMount(async () => {
    await checkSession();
    if (authenticated) {
      await loadTasks();
    }
  });
</script>

<div class="max-w-6xl mx-auto p-6 space-y-6">
  <div class="flex items-center justify-between">
    <h1 class="text-2xl font-bold">My Todoist Tasks</h1>
    <div class="flex items-center gap-3">
      {#if authenticated}
        <span class="text-green-700">Connected ✅</span>
      {:else}
        <a class="px-4 py-2 rounded bg-black text-white" href="http://localhost:8000/login">Connect Todoist</a>
      {/if}
    </div>
  </div>

  <!-- Filters -->
  <div class="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
    <div>
      <label class="block text-sm text-gray-600 mb-1">Filter (Todoist syntax)</label>
      <input class="w-full border rounded p-2" bind:value={filter} placeholder='e.g. "today | overdue"' />
    </div>
    <div>
      <label class="block text-sm text-gray-600 mb-1">Project ID</label>
      <input class="w-full border rounded p-2" bind:value={project_id} placeholder='optional' />
    </div>
    <div>
      <label class="block text-sm text-gray-600 mb-1">Section ID</label>
      <input class="w-full border rounded p-2" bind:value={section_id} placeholder='optional' />
    </div>
    <div>
      <label class="block text-sm text-gray-600 mb-1">Label</label>
      <input class="w-full border rounded p-2" bind:value={label} placeholder='optional' />
    </div>
    <div class="md:col-span-4 flex items-center gap-3">
      <button class="px-4 py-2 rounded bg-black text-white disabled:opacity-50" on:click={loadTasks} disabled={!authenticated}>
        {loading ? 'Loading…' : 'Refresh'}
      </button>
      <label class="flex items-center gap-2">
        <input type="checkbox" bind:checked={rawMode} />
        <span class="text-sm">Show raw JSON</span>
      </label>
    </div>
  </div>

  {#if errorMsg}
    <pre class="bg-red-50 border border-red-200 text-red-800 p-3 rounded whitespace-pre-wrap">{errorMsg}</pre>
  {/if}

  {#if tasks.length === 0 && !loading && authenticated}
    <div class="text-gray-600">No tasks found.</div>
  {/if}

  {#if rawMode && tasks.length}
    <pre class="bg-gray-50 p-3 rounded overflow-auto max-h-[60vh]">{JSON.stringify(tasks, null, 2)}</pre>
  {:else if tasks.length}
    <div class="overflow-auto border rounded">
      <table class="min-w-full text-sm">
        <thead class="bg-gray-50">
          <tr class="[&>th]:px-3 [&>th]:py-2 text-left">
            <th>Content</th>
            <th>ID</th>
            <th>Priority</th>
            <th>Project</th>
            <th>Section</th>
            <th>Labels</th>
            <th>Due</th>
            <th>Assignee</th>
            <th>URL</th>
          </tr>
        </thead>
        <tbody>
          {#each tasks as t}
            <tr class="[&>td]:px-3 [&>td]:py-2 border-t">
              <td class="font-medium">{t.content}</td>
              <td class="text-gray-600">{t.id}</td>
              <td>
                <span class="inline-block px-2 py-0.5 rounded bg-gray-100 border">{priorityBadge(t.priority)}</span>
              </td>
              <td>{t.project_id}</td>
              <td>{t.section_id || ''}</td>
              <td>{(t.labels || []).join(', ')}</td>
              <td>
                {#if t.due}
                  <div>{t.due.string}</div>
                  <div class="text-gray-500">{t.due.date || t.due.datetime}</div>
                {/if}
              </td>
              <td>{t.assignee_id || ''}</td>
              <td>
                {#if t.url}
                  <a class="text-blue-600 underline" href={t.url} target="_blank" rel="noreferrer">open</a>
                {/if}
              </td>
            </tr>
            <!-- Optional: expandable row with full JSON per task -->
            <tr class="border-b">
              <td colspan="9">
                <details class="text-xs">
                  <summary class="cursor-pointer text-gray-600">details</summary>
                  <pre class="bg-gray-50 p-3 rounded overflow-auto">{JSON.stringify(t, null, 2)}</pre>
                </details>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>