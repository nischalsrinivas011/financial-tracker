import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import accounts, ask, statements, transactions
from app.api.deps import CurrentUser

app = FastAPI(title="Financial Tracker API")
app.include_router(statements.router)
app.include_router(ask.router)
app.include_router(accounts.router)
app.include_router(transactions.router)

# Bearer-token cross-origin calls only (Clerk's frontend SDK attaches the
# session token as an Authorization header, not a cookie) - allow_credentials
# stays False since no cookie is sent cross-origin, keeping this simpler.
# CORS_ALLOWED_ORIGINS, like CLERK_AUTHORIZED_PARTIES, defaults to the
# Next.js dev server and needs updating to the real deployed frontend URL
# once Vercel deploy happens (Phase 6, later step).
_cors_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/me")
def me(user: CurrentUser):
    return {"user_id": str(user.id), "clerk_user_id": user.clerk_user_id}
