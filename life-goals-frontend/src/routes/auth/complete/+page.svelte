<script lang="ts">
  import { onMount } from 'svelte';
  const API = 'http://localhost:8000';

  let status = 'Finishing sign-in...';

  onMount(async () => {
    // fetch CSRF + auth flag; cookie is now set by the backend
    const r = await fetch(`${API}/session`, { credentials: 'include' });
    const j = await r.json();
    status = j.authenticated ? 'Connected to Todoist ✅' : 'Not connected ❌';
  });
</script>

<p class="p-4">{status}</p>