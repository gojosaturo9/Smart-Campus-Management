from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.session import get_current_user
from app.core.chatbot import chatbot_reply

router = APIRouter(prefix="/chatbot")


class ChatbotRequest(BaseModel):
    message: str


@router.post("/message")
def chatbot_message(payload: ChatbotRequest, user: dict = Depends(get_current_user)):
    return {"ok": True, **chatbot_reply(user=user, message=payload.message)}
