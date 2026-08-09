from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI

from app.api.deps import CurrentUser

app = FastAPI(title="Financial Tracker API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/me")
def me(user: CurrentUser):
    return {"user_id": str(user.id), "clerk_user_id": user.clerk_user_id}
