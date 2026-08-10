"""The hybrid Q&A endpoint: natural-language questions over a user's own
transactions plus the knowledge corpus, via app/rag/answer.py.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import CurrentUser, DbSession
from app.rag.answer import answer as compute_answer

router = APIRouter(tags=["ask"])


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    text: str
    route: str
    used_llm: bool
    sources: list[str]


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest, user: CurrentUser, db: DbSession):
    result = compute_answer(db, user.id, request.question)
    return AskResponse(text=result.text, route=result.route, used_llm=result.used_llm, sources=result.sources)
