## PIM_Comp350

A simple Personal Information Manager (PIM) API built with FastAPI and SQLite for COMP350. The project currently provides basic user authentication and CRUD-like operations for user "particles" (articles/notes). A minimal frontend scaffold is included.

Contributors: Ishaan Kurian, Rohan Kalia

---

### Tech stack

- **Backend**: FastAPI, Uvicorn, Pydantic, Starlette
- **Database**: SQLite (file: `backend/db/pim.db`)
- **Frontend**: Static skeleton under `frontend/` (HTML/CSS/JS placeholders)
- **License**: MIT (see `LICENSE`)

---

### Project structure

```
PIM_Comp350/
  backend/
    auth.py              # Authentication helpers backed by SQLite
    main.py              # FastAPI app and HTTP endpoints
    particles.py         # Particle (article) operations
    db/pim.db            # SQLite database
    requirements.txt     # Python dependencies
  frontend/
    public/index.html    # Placeholder (empty)
    src/css/styles.css   # Placeholder (empty)
    src/js/main.js       # Placeholder (empty)
  docs/                  # Design docs
  LICENSE                # MIT License
  README.md              # This file
```

---

### Prerequisites

- Python 3.10+ (3.11 recommended)
- `pip`
- Optional: `sqlite3` CLI to inspect the database

---

### Setup and run (backend)

1. Create and activate a virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies

```bash
pip install -r backend/requirements.txt
```

3. Run the API server

```bash
cd backend
uvicorn main:app --reload
```

4. Open API docs

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Health check: `http://127.0.0.1:8000/health`

Note: CORS is enabled for all origins in development.

---

### Database

- Location: `backend/db/pim.db`
- The code assumes two tables: `auth` and `particles`.

Schemas:

```sql
-- auth table
CREATE TABLE IF NOT EXISTS auth (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL  -- Plaintext currently; hashing is a TODO
);

-- particles table
CREATE TABLE IF NOT EXISTS particles (
  article_id TEXT PRIMARY KEY,
  username TEXT NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  FOREIGN KEY (username) REFERENCES auth(username)
);
```

You can inspect the DB using:

```bash
sqlite3 backend/db/pim.db ".tables"
```

---

### API overview

Base URL: `http://127.0.0.1:8000`

#### Auth

- POST `/auth/login`

  - Body: `{ "username": "string", "password": "string" }`
  - 200: `{ "message": "Login successful" }`
  - 401: `{ "error": "Invalid username or password" }`

- POST `/auth/register` (201 on success)

  - Body: `{ "username": "string", "password": "string" }`
  - 201: `{ "message": "User created" }`
  - 409: `{ "error": "Username already exists" }`

- DELETE `/auth/delete`

  - Body: `{ "username": "string", "password": "string" }`
  - 200: `{ "message": "User deleted" }`
  - 404: `{ "error": "User not found or password incorrect" }`

- POST `/auth/reset-password`

  - Body: `{ "username": "string", "new_password": "string" }`
  - 200: `{ "message": "Password updated" }`
  - 404: `{ "error": "User not found" }`

- GET `/auth/user/{username}`
  - 200: `{ "id": number, "username": "string", "password": "string" }`
  - 404: `{ "error": "User not found" }`

Security warnings (current state):

- Passwords are not hashed.
- No sessions/tokens; endpoints like user lookup and deletion lack auth guards.

#### Particles

- GET `/particles/{username}`

  - 200: `{ "items": [ { "particle_id"|"article_id": string, "title": string, "content": string } ], "count": number }`
  - Note: There is a known key-name inconsistency between endpoints (`particle_id` vs `article_id`). See Known issues below.

- GET `/particles/{username}/search?q=...`

  - 200: `{ "items": [ { "particle_id": string, "title": string, "content": string } ], "count": number }`

- DELETE `/particles/{particle_id}`
  - 200: `{ "message": "Particle deleted" }`
  - 404: `{ "error": "Particle not found" }`

---

### Quick examples

```bash
# Register
curl -s -X POST http://127.0.0.1:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"secret"}'

# Login
curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"secret"}'

# List particles for a user
curl -s "http://127.0.0.1:8000/particles/alice"

# Search particles
curl -s "http://127.0.0.1:8000/particles/alice/search?q=note"

# Delete a particle
curl -s -X DELETE "http://127.0.0.1:8000/particles/ARTICLE_ID"
```

---

### License

MIT © 2025 Rohan Kalia. See `LICENSE` for details.
