<script lang="ts">
  import { onMount } from 'svelte';

  const API = '/api'; // if you’re using Vite proxy; else 'http://localhost:8000'
  let status = 'Finalizing sign-in…';

  onMount(async () => {
  const r = await fetch(`${API}/session`, { credentials: 'include' });
  const j = await r.json();
  status = j.authenticated ? 'Connected ✅ Redirecting…' : 'Not connected ❌';
  if (j.authenticated) {
    setTimeout(() => window.location.href = '/tasks', 2000);
  }
});

  function goToApp() {
    // take them back to your app's home or /tasks
    window.location.href = '/tasks';
  }
</script>

<div class="min-h-screen flex flex-col items-center justify-center gap-6">
  <h1 class="text-2xl font-bold">{status}</h1>
  <button
    on:click={goToApp}
    class="px-6 py-3 rounded-xl bg-black text-white shadow hover:bg-gray-800"
  >
    Go to My Tasks
  </button>
</div>
