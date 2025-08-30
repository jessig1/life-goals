<script lang="ts">
  const API_BASE = 'http://localhost:8000';
  let csrf = '';
  let content = '';
  let due_string = 'today at 10:05';
  let priority = 3;
  let msg = '';
  
 

   // Get CSRF token and (optionally) auth status
  async function init() {
    const res = await fetch(`${API_BASE}/api/session`, { credentials: 'include' });
    const data = await res.json();
    csrf = data.csrf;
  }
  init();

  async function createTask() {
    const res = await fetch('http://localhost:8000/api/create_task', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrf},
      credentials: 'include',
      body: JSON.stringify({ content, due_string, priority })
    });
    msg = `${res.status} ${res.statusText}\n` + (await res.text());
    if (res.ok) { content = ''; }
  }
</script>

<div class="max-w-xl mx-auto p-6 space-y-4">
  <a class="px-4 py-2 rounded bg-gray-200" href="/tasks">View Tasks</a>
  <h1 class="text-2xl font-bold">Create Todoist Task</h1>
  <input class="w-full border rounded p-2" placeholder="Task content" bind:value={content} />
  <input class="w-full border rounded p-2" placeholder="due_string (e.g., today 16:00)" bind:value={due_string} />
  <select class="border rounded p-2" bind:value={priority}>
    <option value="1">Priority 1 (low)</option>
    <option value="2">Priority 2</option>
    <option value="3">Priority 3</option>
    <option value="4">Priority 4 (urgent)</option>
  </select>
  <button class="px-4 py-2 rounded bg-black text-white" on:click={createTask}>Create</button>
  <pre class="bg-gray-50 p-3 rounded whitespace-pre-wrap">{msg}</pre>
  <a href={`${API_BASE}/api/login`}>Connect Todoist</a>
</div>
