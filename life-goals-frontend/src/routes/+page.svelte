<script lang="ts">
  import { onMount } from 'svelte';
  const API = '/api';

  let status = 'Checking session…';

  onMount(async () => {
    try {
      const r = await fetch(`${API}/session`, { credentials: 'include' });
      const j = await r.json();
      if (j.authenticated) {
        window.location.href = '/tasks';
        return;
      }
      status = 'Not connected';
    } catch {
      status = 'Could not reach server';
    }
  });
</script>

<div class="min-h-screen grid place-items-center p-8">
  <div class="text-center space-y-4">
    <h1 class="text-2xl font-bold">Life Goals</h1>
    <p class="text-gray-600">{status}</p>
    <a class="px-4 py-2 rounded bg-black text-white inline-block" href="/api/login">
      Connect Todoist
    </a>
  </div>
</div>
