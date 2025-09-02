package httpapi

import (
	"encoding/json"
	"net/http"
)

type Task struct {
	ID        string   `json:"id"`
	Content   string   `json:"content"`
	Priority  int      `json:"priority"`
	ProjectID string   `json:"project_id"`
	Labels    []string `json:"labels"`
	Due       any      `json:"due"`
}

func UpsertTaskHandler(w http.ResponseWriter, r *http.Request) {
	var t Task
	if err := json.NewDecoder(r.Body).Decode(&t); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest); return
	}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]any{"ok": true})
}

func UpsertPageHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]any{"ok": true})
}

func QueryTasksHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]any{"items": []Task{}})
}
