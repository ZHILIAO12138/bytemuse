from fastapi import APIRouter, Depends
from fastapi import Request
from sqlalchemy.orm import Session
from app.api.services import imessage
from app.database.session import get_session

router = APIRouter()


@router.get("/message")
async def get_message(msg_signature: str, timestamp: str, nonce: str, echostr: str):
    return imessage.get_message(msg_signature, timestamp, nonce, echostr)


@router.post("/message")
async def post_message(msg_signature: str, timestamp: str, nonce: str, request: Request,
                       session: Session = Depends(get_session)):
    xml_data = await request.body()
    return imessage.post_message(msg_signature, timestamp, nonce, xml_data, session)


