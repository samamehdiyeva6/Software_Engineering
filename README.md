# EscrowFlow (Flet)

High‑fidelity UI implementation of the provided PDF screens using Python Flet.

The project now also includes a structured FastAPI backend for authentication and project CRUD.

## Run

1. Create and activate a virtual environment (optional, recommended).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
python app.py
```

4. Start the API:

```bash
uvicorn main:app --reload
```

5. Open API docs:

```text
http://127.0.0.1:8000/docs
```

## API Structure

- `main.py` builds the FastAPI app and registers routes.
- `api/routers/auth.py` contains login and register endpoints.
- `api/routers/projects.py` contains project CRUD endpoints.
- `api/schemas.py` contains request/response validation models.
- `api/services.py` contains business logic built on top of `database.py`.

## API Endpoints

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/projects?owner_user_id={id}`
- `GET /api/v1/projects/{project_id}?owner_user_id={id}`
- `POST /api/v1/projects`
- `PUT /api/v1/projects/{project_id}?owner_user_id={id}`
- `DELETE /api/v1/projects/{project_id}?owner_user_id={id}`

## Routes

- `/` Login
- `/register` Create account
- `/dashboard` Customer dashboard
- `/projects` Project management
- `/project-detail` Project detail
- `/project-create` Create project
- `/contract` Contract lifecycle
- `/escrow` Escrow & financials
- `/proposal` Worker proposal
- `/milestones` Milestones & deliverables
- `/admin` Admin overview
- `/escrow-control` Admin escrow control
- `/dispute` Dispute resolution
- `/user-management` User management

Use the sidebar navigation where available, or change the route in the URL bar.
