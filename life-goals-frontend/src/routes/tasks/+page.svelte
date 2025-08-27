<script lang="ts">
  import { onMount } from 'svelte';
  const API = 'http://localhost:8000';

  let authenticated = false;
  let csrf = '';
  let tasks: any[] = [];
  let loading = false;
  let errorMsg = '';

  async function refreshSession() {
    const r = await fetch(`${API}/session`, { credentials: 'include' });
    const j = await r.json();
    csrf = j.csrf;
    authenticated = !!j.authenticated;
  }

  async function loadTasks() {
    loading = true; errorMsg = ''; tasks = [];
    try {
      const res = await fetch(`${API}/tasks`, { credentials: 'include' });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}\n${await res.text()}`);
      tasks = await res.json();
    } catch (e: any) {
      errorMsg = e.message || String(e);
    } finally {
      loading = false;
    }
  }

  onMount(async () => {
    await refreshSession();
    if (authenticated) await loadTasks();
  });
</script>

<!-- your markup/table here (unchanged), call {loadTasks()} on a Refresh button -->
