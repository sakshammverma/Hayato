# HAYATO

## About
An autonomous, multi agent code remediation engine built with LangGraph. Parallel analyzes GitHub pull requests for vulnerabilities, implements multi provider API fallbacks, and generates verified patches

## Architecture

```mermaid
graph TD
    A[Developer opens PR] --> B[GitHub Webhook]
    B --> C[FastAPI Server]
    C --> D{Verify HMAC Signature}
    D -->|Invalid| E[401 Rejected]
    D -->|Valid| F[Return 200 instantly]
    F --> G[Redis Job Queue]
    G --> H[Background Worker]
    H --> I[LangGraph Pipeline]
    I --> J[fetch_files_node]
    J --> K[coordinator_routing]
    K --> L[review_file_node x N parallel]
    L --> M{Cache Hit?}
    M -->|Yes| N[Return cached review]
    M -->|No| O[Call Groq LLM]
    O --> P[Sandbox: flake8 + bandit]
    P --> Q[Cache result in Redis]
    Q --> R[reducer_node]
    N --> R
    R --> S[Post inline PR comment]
    R --> T[Save to SQLite DB]
    T --> U[Dashboard: render.com/]
```
