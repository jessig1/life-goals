<script lang="ts">
  import { onMount } from 'svelte';
  const API = '/api';

  let csrf = '';
  let authenticated = false;
  let tasks:any[] = [];
  let msg = '';

  async function refreshSession() {
    const r = await fetch(`${API}/session`, { credentials: 'include' });
    const j = await r.json();
    csrf = j.csrf;
    authenticated = !!j.authenticated;
  }

  async function loadTasks() {
    const r = await fetch(`${API}/tasks`, { credentials: 'include' });
    if (!r.ok) {
      msg = await r.text();
      return;
    }
    tasks = await r.json();
  }

  async function logout() {
    const r = await fetch(`${API}/logout`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'X-CSRF-Token': csrf }
    });
    if (r.ok) window.location.href = '/';
  }

  onMount(async () => {
    await refreshSession();
    if (!authenticated) {
      window.location.href = '/'; // route guard
      return;
    }
    await loadTasks();
  });
</script>

<div class="max-w-6xl mx-auto p-6 space-y-4">
  <div class="flex items-center justify-between">
    <h1 class="text-2xl font-bold">My Tasks</h1>
    <button class="px-3 py-2 rounded bg-gray-200" on:click={logout}>Logout</button>
  </div>

  {#if msg}<pre class="bg-red-50 p-3 rounded">{msg}</pre>{/if}

  {#if tasks.length === 0}
    <div class="text-gray-600">No tasks found.</div>
  {:else}
    <ul class="list-disc ml-6">
      {#each tasks as t}<li>{t.content}</li>{/each}
    </ul>
  {/if}
</div>
