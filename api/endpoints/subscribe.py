from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from app.api.endpoints import get_current_user
from app.api.services import isubscribe
from app.api.services.isubscribe import CodeQuery, Torrent
from app.schemas import CodeSubscribe
from app.schemas.reponse import ResponseEntity
from app.database.session import get_session

router = APIRouter()


@router.get("/dashboard")
def dashboard(session: Session = Depends(get_session),
                    current_user: str = Depends(get_current_user)) -> ResponseEntity:
    return isubscribe.dashboard(session)


@router.get("/ranks")
def rank(type: str, session: Session = Depends(get_session),
                  current_user: str = Depends(get_current_user)) -> ResponseEntity:
    return isubscribe.rank(type, session)




@router.post("/codes/list")
def list_code(code_query: CodeQuery, session: Session = Depends(get_session),
              current_user: str = Depends(get_current_user)) -> ResponseEntity:
    return isubscribe.code_list(code_query, session)


@router.post("/codes/recommend")
def list_code(session: Session = Depends(get_session),
              current_user: str = Depends(get_current_user)) -> ResponseEntity:
    return isubscribe.recommend(session)


@router.post("/codes/release_today")
def release_today(session: Session = Depends(get_session),
                  current_user: str = Depends(get_current_user)) -> ResponseEntity:
    return isubscribe.release_today(session)


@router.post("/codes/sub")
async def sub(subscribe: CodeSubscribe, session: Session = Depends(get_session),
        current_user: str = Depends(get_current_user)) -> ResponseEntity:
    return isubscribe.sub(subscribe, session)



@router.delete("/codes/cancel")
async def cancel(code_no: str, session: Session = Depends(get_session),
           current_user: str = Depends(get_current_user)) -> ResponseEntity:
    return isubscribe.cancel(code_no, session)


@router.get("/complex/search")
def torrents(query: str, session: Session = Depends(get_session)) -> ResponseEntity:
    return isubscribe.torrents(query, session)


@router.post("/torrents/download/manual")
async def manual_download(torrent: Torrent, session: Session = Depends(get_session),
                          current_user: str = Depends(get_current_user)) -> ResponseEntity:
    return isubscribe.manual_download(torrent, session)


@router.get("/codes/download/all")
async def download_subscribe(current_user: str = Depends(get_current_user)) -> ResponseEntity:
    return isubscribe.download_subscribe()


@router.get("/rank/subscribe")
async def rank_subscribe(codes: str, session: Session = Depends(get_session),
                         current_user: str = Depends(get_current_user)) -> ResponseEntity:
    return isubscribe.rank_subscribe(codes, session)


@router.get("/codes/star")
async def star_code(code_no: str, session: Session = Depends(get_session),
           current_user: str = Depends(get_current_user)) -> ResponseEntity:
    return isubscribe.star_code(code_no, session)