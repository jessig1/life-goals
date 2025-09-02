package main

import (
	"log"
	"net/http"
	"os"

	httpapi "github.com/jessig1/life-goals-core/internal/http"
)

func main() {
	addr := os.Getenv("CORE_ADDR")
	if addr == "" { addr = ":8080" }

	mux := http.NewServeMux()
	mux.HandleFunc("POST /internal/upsert/task", httpapi.UpsertTaskHandler)
	mux.HandleFunc("POST /internal/upsert/page", httpapi.UpsertPageHandler)
	mux.HandleFunc("GET /internal/query/tasks", httpapi.QueryTasksHandler)

	log.Printf("core API listening on %s", addr)
	if err := http.ListenAndServe(addr, authMiddleware(mux)); err != nil {
		log.Fatal(err)
	}
}

// keep your authMiddleware here...
// authMiddleware checks the shared secret on every request.
func authMiddleware(next http.Handler) http.Handler {
	secret := os.Getenv("CORE_SHARED_SECRET")
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if secret == "" || r.Header.Get("X-Core-Secret") != secret {
			http.Error(w, "Forbidden", http.StatusForbidden)
			return
		}
		next.ServeHTTP(w, r)
	})
}
