# AI-Powered Employee Platform

A portfolio MVP for employee and workplace self-service. The platform brings employee records, departments, project assignments, leave requests, and a database-aware AI assistant together behind a FastAPI API and a small browser UI.

## Overview

The application gives employees and administrators one place to work with employee information, see project assignments, submit and review leave requests, and ask natural-language questions about platform data. AI answers that need company data are grounded through a small set of server-side tools that query PostgreSQL; the model does not receive direct database access.

## Key Features

- JWT-based registration, login, and authenticated API access
- Employee records and department directory endpoints
- Projects and employee-project assignments
- Employee leave request submission and history
- Ollama-powered AI assistant using Qwen 2.5 7B by default
- LLM function/tool calling through a Python executor
- PostgreSQL-backed AI tools and persisted AI conversations
- Multi-turn conversation context, including tool-call/result messages
- Prompt-injection-aware system instructions with backend authorization boundaries
- FastAPI REST API with Pydantic request/response validation
- Server-rendered Jinja2 pages with plain HTML, CSS, and JavaScript
- Automated pytest coverage for core authentication, authorization, AI tools, and UI routes
- Docker Compose support for the FastAPI app and PostgreSQL

## AI Architecture

```text
User
  → FastAPI (/ai/chat)
  → Ollama / Qwen 2.5 7B
  → tool selection
  → Python tool executor
  → PostgreSQL via SQLAlchemy
  → tool result
  → Ollama / Qwen 2.5 7B
  → saved assistant response
```

The API authenticates the request and loads the user’s conversation history. Ollama receives the system prompt, few-shot examples, history, and the registered tool definitions. When the model selects a tool, the executor checks that the tool exists, validates its arguments with Pydantic, checks the user’s role, and calls the registered Python function. Results and conversation messages are persisted before the result is sent back to Ollama for a natural-language response.

Available tools:

- `get_my_projects` — returns projects assigned to the authenticated user’s linked employee profile.
- `get_my_leave_requests` — returns that employee’s leave requests, optionally filtered by leave type.
- `search_employees` — searches employee names and email addresses and returns a limited result set.

The model selects from an application-defined allowlist; it cannot submit SQL. Personal project and leave tools scope their database queries to the authenticated user’s employee link. The current service executes the first tool call returned for a turn.

## Tech Stack

- **Language:** Python
- **API:** FastAPI, Pydantic
- **Persistence:** SQLAlchemy, PostgreSQL, Alembic
- **Authentication:** JWT, `pwdlib` password hashing
- **AI:** Ollama, Qwen2.5 7B, HTTPX
- **Web UI:** Jinja2, HTML, CSS, JavaScript
- **Testing:** pytest
- **Packaging:** Docker, Docker Compose
- **Version control:** Git, GitHub

## Project Structure

```text
.
├── alembic/                  # Existing database revision history
│   └── versions/
├── app/
│   ├── ai_executor.py        # Tool validation, authorization, and execution
│   ├── ai_service.py         # Chat orchestration and persistence
│   ├── ai_tools.py           # Tool implementations and definitions
│   ├── database.py           # SQLAlchemy engine and request sessions
│   ├── llm_provider.py       # Ollama HTTP provider
│   ├── main.py               # FastAPI API and UI routes
│   ├── models.py             # SQLAlchemy models
│   ├── prompts.py            # System instructions and examples
│   ├── schemas.py            # Pydantic schemas
│   ├── security.py           # Password/JWT helpers and role dependency
│   └── test_ollama_tools.py  # Optional manual Ollama smoke check
├── static/
│   ├── css/style.css
│   └── js/                   # Browser-side API and page logic
├── templates/                # Jinja2 page templates
├── tests/                    # Automated pytest suite
├── .dockerignore
├── .env.example
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Local Setup

The commands below use PowerShell. They assume a PostgreSQL server is available locally and the database already has the base application tables. See the migration limitation below before using a fresh database.

1. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install the Python requirements:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Create `.env` only if one does not already exist, then preserve existing secrets and configure it for a locally running PostgreSQL server:

   ```powershell
   if (-not (Test-Path .env)) { Copy-Item .env.example .env }
   ```

   For a native local run, set `DATABASE_URL` to a SQLAlchemy PostgreSQL URL using the `postgresql+psycopg` driver, host `localhost`, port `5432`, and your database name. Also set a long random `JWT_SECRET_KEY`. The Ollama defaults are `http://127.0.0.1:11434` and `qwen2.5:7b`.

4. Start PostgreSQL and select a database with the expected base schema. The checked-in revisions extend a pre-existing schema; they do not create all base tables.

5. Inspect the database revision and review the migration warning before applying anything:

   ```powershell
   alembic current
   alembic upgrade head
   ```

   Do not run `upgrade head` against a blank database or an existing database until its schema, current revision, backup, and the data effects of the revisions have been reviewed.

6. Install/load the model and ensure Ollama is running on the host:

   ```powershell
   ollama pull qwen2.5:7b
   ollama serve
   ```

   If Ollama is already running as a Windows service/application, the `ollama serve` command may not be needed.

7. Start FastAPI from the repository root:

   ```powershell
   uvicorn app.main:app --reload
   ```

8. Open <http://127.0.0.1:8000/login>. Interactive API documentation is at <http://127.0.0.1:8000/docs>.

## Docker Setup

Docker Compose runs **FastAPI and PostgreSQL**. PostgreSQL data is stored in the persistent `postgres_data` volume. The app connects to the database using the Compose service hostname `db`.

Ollama remains installed and running on the host; **Ollama is not containerized**. For Windows Docker Desktop, the app uses `host.docker.internal` to reach the host Ollama server. The URL and model are configurable with `OLLAMA_BASE_URL` and `OLLAMA_MODEL`.

Create `.env` from `.env.example` only when there is no existing `.env`; otherwise add the Compose values without replacing existing secrets. Set `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `JWT_SECRET_KEY`, then run:

```powershell
docker compose up --build
```

Open <http://localhost:8000/login>. Stop the services without removing persistent data with:

```powershell
docker compose down
```

The repository does not currently contain an initial schema migration. A blank PostgreSQL volume cannot be initialized solely with `alembic upgrade head`, and Compose does not create the application schema. In addition, revision `40f2f7beb152` truncates `ai_tool_calls` while converting columns. Review the target database and take a backup before applying existing migrations; they are intentionally not run automatically on container startup.

## Testing

Run the automated suite from the repository root:

```powershell
pytest -q
```

The current suite contains **17 passing tests**.

## Example AI Queries

- “What projects am I working on?”
- “Show me my leave requests.”
- “Search for employees named Rahul.”
- “What is its description?”

The last question demonstrates multi-turn context: it can refer to a project discussed earlier in the same conversation.

## Security

- Passwords are stored as hashes using `pwdlib`; plaintext passwords are not persisted.
- The existing JWT bearer flow authenticates protected API endpoints.
- Role checks are applied through the existing role dependency and AI tool registry.
- Tool arguments are validated against Pydantic models before execution.
- Conversation ownership is checked before stored history is used.
- The prompt instructs the model to treat user instructions as untrusted and not bypass application rules. Authorization and tool allowlisting are enforced in backend code; prompt instructions alone are not a security boundary.
- Local secrets belong in `.env`. That file is excluded from Git and Docker build context; `.env.example` contains placeholders.

## Known Limitations / Future Improvements

- Ollama runs locally on the development laptop and currently uses CPU inference, which can make AI responses slow.
- Docker does not containerize Ollama; the host service must be running and reachable from the app container.
- The Alembic history needs a reviewed initial baseline for completely fresh databases. One existing revision also truncates tool-call records.
- Employee create/update/delete APIs require authentication but are not restricted to admins. Current department and project routes are read-only.
- The UI is intentionally simple and intended as an MVP/portfolio demonstration.
- The AI service executes only the first tool call returned for a turn.
