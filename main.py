from fastapi import FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base

app = FastAPI()
URI = "sqlite:///escrowflow.db"
engine = create_engine(URI)
Base = declarative_base()

@app.get("/")
def home():
    return {"message": "EscrowFlow API"}

@app.get("/users")
def get_users():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, email, role FROM users"))
        users = [dict(row) for row in result.mappings()]
    return {"users": users}

@app.get("/projects")
def get_projects():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, title, description, status FROM projects"))
        projects = [dict(row) for row in result.mappings()]
    return {"projects": projects}
