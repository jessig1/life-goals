<script lang="ts">
  import { onMount } from 'svelte';
  const API = '/api';

  let csrf = '';
  let authenticated = false;

  // Form state
  let content = '';
  let description = '';
  let priority: number = 1; // 1..4
  let dueString = '';
  let labels = '';
  let creating = false;
  let error = '';

  async function refreshSession() {
    const r = await fetch(`${API}/session`, { credentials: 'include' });
    const j = await r.json();
    csrf = j.csrf;
    authenticated = !!j.authenticated;
  }

  async function createTask() {
    error = '';
    if (!content.trim()) {
      error = 'Content is required';
      return;
    }
    creating = true;
    try {
      const body: Record<string, any> = { content: content.trim() };
      if (description.trim()) body.description = description.trim();
      const p = Number(priority);
      if (p >= 1 && p <= 4) body.priority = p;
      if (dueString.trim()) body.due_string = dueString.trim();
      const lbls = labels.split(',').map((s) => s.trim()).filter(Boolean);
      if (lbls.length) body.labels = lbls;

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
      // Go back to tasks list
      window.location.href = '/tasks';
    } catch (e: any) {
      error = e?.message ?? String(e);
    } finally {
      creating = false;
    }
  }

  onMount(async () => {
    await refreshSession();
    if (!authenticated) {
      window.location.href = '/';
    }
  });
</script>

<div class="max-w-3xl mx-auto p-6 space-y-4">
  <div class="flex items-center justify-between">
    <h1 class="text-2xl font-bold">New Task</h1>
    <a href="/tasks" class="px-3 py-2 rounded bg-gray-200">Back</a>
  </div>

  <div class="rounded border border-gray-200 p-4 bg-white shadow-sm">
    <form on:submit|preventDefault={createTask} class="grid gap-3 md:grid-cols-2">
      <div class="md:col-span-2">
        <label class="block text-sm font-medium text-gray-700">Content *</label>
        <input class="mt-1 w-full rounded border px-3 py-2" bind:value={content} placeholder="Task title" />
      </div>
      <div class="md:col-span-2">
        <label class="block text-sm font-medium text-gray-700">Description</label>
        <textarea class="mt-1 w-full rounded border px-3 py-2" rows="2" bind:value={description} placeholder="Details"></textarea>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">Priority</label>
        <select class="mt-1 w-full rounded border px-3 py-2" bind:value={priority}>
          <option value="1">P4 (Normal)</option>
          <option value="2">P3 (Medium)</option>
          <option value="3">P2 (High)</option>
          <option value="4">P1 (Urgent)</option>
        </select>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">Due (natural language)</label>
        <input class="mt-1 w-full rounded border px-3 py-2" bind:value={dueString} placeholder="e.g., tomorrow 5pm or 2025-09-10" />
      </div>
      <div class="md:col-span-2">
        <label class="block text-sm font-medium text-gray-700">Labels (comma-separated)</label>
        <input class="mt-1 w-full rounded border px-3 py-2" bind:value={labels} placeholder="work,urgent" />
      </div>
      {#if error}
        <div class="md:col-span-2 text-sm text-red-600">{error}</div>
      {/if}
      <div class="md:col-span-2">
        <button type="submit" class="px-4 py-2 rounded bg-blue-600 text-white disabled:opacity-50" disabled={creating}>
          {creating ? 'Creating…' : 'Create Task'}
        </button>
      </div>
    </form>
  </div>
</div>

