from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pathlib import Path
import os
import sys
import uvicorn

# Ensure relative SQLite paths in auth.py and particles.py resolve correctly
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
os.chdir(BASE_DIR)

# Importing py files with the funcitons
import auth 
import particles 


app = FastAPI(title="PIM API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Payload data structures
class Credentials(BaseModel):
    username: str
    password: str


class ResetPasswordRequest(BaseModel):
    username: str
    new_password: str


@app.get("/health")
def health_check():
    return JSONResponse(content={"status": "ok"})


# Auth endpoints
@app.post("/auth/login")    # TODO: Maybe add session id's to this so that the login can be tracked and stuff
def login_user(payload: Credentials):
    is_valid = auth.login(payload.username, payload.password)
    if not is_valid:
        return JSONResponse(status_code=401, content={"error": "Invalid username or password"})
    return JSONResponse(content={"message": "Login successful"})


@app.post("/auth/register", status_code=201)
def register_user(payload: Credentials):
    created = auth.add_new_user(payload.username, payload.password)
    if not created:
        return JSONResponse(status_code=409, content={"error": "Username already exists"})
    return JSONResponse(content={"message": "User created"})


@app.delete("/auth/delete") # TODO: Add some layer of security on this function
def delete_user(payload: Credentials):
    deleted = auth.delete_user(payload.username, payload.password)
    if not deleted:
        return JSONResponse(status_code=404, content={"error": "User not found or password incorrect"})
    return JSONResponse(content={"message": "User deleted"})


@app.post("/auth/reset-password")
def reset_password(payload: ResetPasswordRequest):
    updated = auth.reset_passwd(payload.username, payload.new_password)
    if not updated:
        return JSONResponse(status_code=404, content={"error": "User not found"})
    return JSONResponse(content={"message": "Password updated"})


@app.get("/auth/user/{username}")   # TODO: Add some layer of security on this function
def get_user(username: str):
    user = auth.get_user_details(username)
    if not user:
        return JSONResponse(status_code=404, content={"error": "User not found"})
    return JSONResponse(content=user)


# Particle endpoints
@app.get("/particles/{username}")
def list_articles(username: str):
    items = particles.view_articles(username)
    return JSONResponse(content={"items": items, "count": len(items)})


@app.get("/particles/{username}/search")
def search_articles(username: str, q: str = Query(..., min_length=1, description="Search query")):
    items = particles.search_article(username, q)
    return JSONResponse(content={"items": items, "count": len(items)})


@app.delete("/particles/{article_id}")
def delete_article(article_id: str):
    ok = particles.delete_article(article_id)
    if not ok:
        return JSONResponse(status_code=404, content={"error": "Article not found"})
    return JSONResponse(content={"message": "Article deleted"})


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
