package main

import (
    "log"
    "net/http"
    "net/url"
    "os"
    "strconv"
    "strings"

    httpapi "github.com/jessig1/life-goals-core/internal/http"
)

func main() {
    addr := normalizeAddr(os.Getenv("CORE_ADDR"))
    log.Printf("Listening on %s", addr)

    // Public mux: healthz is served without auth
    publicMux := http.NewServeMux()
    publicMux.HandleFunc("/healthz", healthHandler)

    // Private API mux (behind auth)
    apiMux := http.NewServeMux()
    // Use path-only patterns for compatibility with Go < 1.22.
    apiMux.HandleFunc("/internal/upsert/task", onlyMethod("POST", httpapi.UpsertTaskHandler))
    apiMux.HandleFunc("/internal/upsert/page", onlyMethod("POST", httpapi.UpsertPageHandler))
    apiMux.HandleFunc("/internal/query/tasks", onlyMethod("GET", httpapi.QueryTasksHandler))

    // Mount the private API under /
    publicMux.Handle("/internal/", authMiddleware(apiMux))

	log.Printf("CORE_SHARED_SECRET set=%v len=%d", os.Getenv("CORE_SHARED_SECRET") != "", len(os.Getenv("CORE_SHARED_SECRET")))
    // Wrap with CORS; auth is applied only to /internal/* via publicMux.
    if err := http.ListenAndServe(addr, corsMiddleware(publicMux)); err != nil {
        log.Fatal(err)
    }
}

// keep your authMiddleware here...
// authMiddleware checks the shared secret on every request.
func authMiddleware(next http.Handler) http.Handler {
    secret := os.Getenv("CORE_SHARED_SECRET")
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Allow unauthenticated OPTIONS so browsers can preflight.
        if r.Method == http.MethodOptions {
            next.ServeHTTP(w, r)
            return
        }
        // Enforce auth only for /internal/* paths
        if !strings.HasPrefix(r.URL.Path, "/internal/") {
            next.ServeHTTP(w, r)
            return
        }
        if secret == "" || r.Header.Get("X-Core-Secret") != secret {
            http.Error(w, "Forbidden", http.StatusForbidden)
            return
        }
        next.ServeHTTP(w, r)
    })
}

// onlyMethod ensures the request uses the expected HTTP method.
func onlyMethod(method string, next http.HandlerFunc) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        if r.Method != method {
            http.Error(w, http.StatusText(http.StatusMethodNotAllowed), http.StatusMethodNotAllowed)
            return
        }
        next(w, r)
    }
}

// corsMiddleware handles CORS, allowing preflight without authentication.
// Configure allowed origins with CORE_CORS_ORIGIN (comma-separated). Defaults to "*".
func corsMiddleware(next http.Handler) http.Handler {
    // Read and parse allowed origins once at startup.
    raw := os.Getenv("CORE_CORS_ORIGIN")
    allowed := parseOrigins(raw)
    wildcard := contains(allowed, "*") || len(allowed) == 0

    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        origin := r.Header.Get("Origin")
        // Always vary on Origin for proper caching.
        w.Header().Add("Vary", "Origin")

        // Decide which origin value to return, if any.
        if wildcard && origin == "" {
            // No Origin header; skip setting ACAO for non-CORS requests.
        } else if wildcard {
            w.Header().Set("Access-Control-Allow-Origin", "*")
        } else if origin != "" && contains(allowed, origin) {
            w.Header().Set("Access-Control-Allow-Origin", origin)
        }

        // Common CORS headers
        w.Header().Set("Access-Control-Allow-Methods", "GET,POST,PUT,PATCH,DELETE,OPTIONS")
        w.Header().Set("Access-Control-Allow-Headers", "Content-Type, X-Core-Secret")
        w.Header().Set("Access-Control-Max-Age", "600")

        if r.Method == http.MethodOptions {
            // Preflight request: No body needed.
            w.WriteHeader(http.StatusNoContent)
            return
        }

        next.ServeHTTP(w, r)
    })
}

func parseOrigins(s string) []string {
    if strings.TrimSpace(s) == "" {
        return nil
    }
    parts := strings.Split(s, ",")
    out := make([]string, 0, len(parts))
    for _, p := range parts {
        p = strings.TrimSpace(p)
        if p != "" {
            out = append(out, p)
        }
    }
    return out
}

func contains(list []string, v string) bool {
    for _, x := range list {
        if x == v {
            return true
        }
    }
    return false
}

// healthHandler responds OK for readiness/liveness checks.
func healthHandler(w http.ResponseWriter, r *http.Request) {
    switch r.Method {
    case http.MethodGet, http.MethodHead:
        w.Header().Set("Content-Type", "text/plain; charset=utf-8")
        w.WriteHeader(http.StatusOK)
        if r.Method == http.MethodGet {
            _, _ = w.Write([]byte("ok"))
        }
    default:
        http.Error(w, http.StatusText(http.StatusMethodNotAllowed), http.StatusMethodNotAllowed)
    }
}

// normalizeAddr makes CORE_ADDR flexible and Windows-friendly.
// Accepts forms like 8080, :8080, localhost:8080, tcp/8080, http://host:8080.
func normalizeAddr(s string) string {
    s = strings.TrimSpace(s)
    if s == "" {
        return ":8080"
    }
    // Only digits => treat as port
    if _, err := strconv.Atoi(s); err == nil {
        return ":" + s
    }
    // proto/port (e.g., tcp/8080) => use just the port
    if i := strings.IndexByte(s, '/'); i != -1 && i+1 < len(s) {
        maybePort := s[i+1:]
        if _, err := strconv.Atoi(maybePort); err == nil {
            return ":" + maybePort
        }
    }
    // URL with scheme => extract host:port
    if strings.Contains(s, "://") {
        if u, err := url.Parse(s); err == nil {
            host := u.Host
            if host == "" {
                host = "localhost"
            }
            if !strings.Contains(host, ":") {
                // Default ports by scheme
                switch strings.ToLower(u.Scheme) {
                case "https":
                    host += ":443"
                default:
                    host += ":80"
                }
            }
            return host
        }
    }
    // *:8080 => :8080
    if strings.HasPrefix(s, "*:") {
        return s[1:]
    }
    // host only => default port
    if !strings.Contains(s, ":") {
        return s + ":8080"
    }
    return s
}
