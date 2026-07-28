# CarCast
A responsive demo storefront for die-cast cars and collectible toys. It has JWT login, persistent carts, a deliberately **demo-only** payment flow, and printable invoice generation.

## Run locally
1. Install Docker Desktop.
2. Edit `.env`; replace both secrets with unique long values.
3. From this directory run: `docker compose up --build`
4. Open http://localhost:5173. API health: http://localhost:4000/api/health

Use any email and a password of 8+ characters to create a demo account. Never use a real payment card: checkout stores no payment credentials.

## Security notes
- Passwords use bcrypt hashes; auth uses short-lived signed JWTs.
- Helmet, CORS allow-list, payload limits, validation and rate limiting are enabled.
- Database queries are parameterized and application DB role is non-superuser.
- For production, use HTTPS, a managed secret store, a real payment provider’s hosted checkout, CSRF protections if moving to cookies, monitoring, and migrations/backups.

## Local AI product assistant (RAG)
The chat button uses a narrow RAG service: product records are embedded with Chroma and Ollama, then `qwen3.5:4b` answers **only** CarCast product and price questions. Other questions receive “I don't have information about that.”

Before starting Compose, install/run Ollama on the Docker host and pull the models:
```bash
ollama pull qwen3.5:4b
ollama pull nomic-embed-text
```
Then run `docker compose up --build`. Compose reaches host Ollama through `host.docker.internal:11434`; configure `OLLAMA_BASE_URL` and the optional `OLLAMA_API_KEY` in `.env` if required by your Ollama proxy.
