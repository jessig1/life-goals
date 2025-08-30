<script lang="ts">
  import { onMount } from 'svelte';
  const API = '/api';
  let status = 'Finalizing sign-in…';

  onMount(async () => {
    const r = await fetch(`${API}/session`, { credentials: 'include' });
    const j = await r.json();
    if (j.authenticated) {
      status = 'Connected ✅ Redirecting…';
      setTimeout(() => (window.location.href = '/tasks'), 800);
    } else {
      status = 'Not connected ❌';
    }
  });
</script>

<p class="p-6 text-center">{status}</p>
