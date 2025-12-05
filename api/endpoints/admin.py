from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.endpoints import get_current_user
from app.api.services import iadmin
from app.schemas.reponse import ResponseEntity
from app.database.session import get_session

router = APIRouter()


@router.get("/login")
async def login(username: str, password: str, token_key: str, session: Session = Depends(get_session)) -> ResponseEntity:
    return iadmin.login(username, password, token_key, session)


@router.get('/user/token')
async def init_token(session: Session = Depends(get_session)) -> ResponseEntity:
    return iadmin.init_token(session)


@router.get('/user/update')
async def update_user(username: str, password: str, session: Session = Depends(get_session),
                current_user: str = Depends(get_current_user)) -> ResponseEntity:
    return iadmin.update_user(username, password, session)
