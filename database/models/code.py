from datetime import datetime
from typing import Dict

from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, Text, Boolean
from sqlalchemy.orm import Session

from app.database.base import Base, DBBase
from app.utils import dict_trans_obj


class Code(Base, DBBase):
    __tablename__ = 'code'

    code: str = Column(String(20), nullable=False, primary_key=True)
    title: str = Column(String(255))
    poster: str = Column(String(255))
    banner: str = Column(String(255))
    preview_url: str = Column(String(255))
    duration: int = Column(Integer)
    release_date: str = Column(String(12))
    genres: str = Column(String(255))
    casts: str = Column(String(255))
    producer: str = Column(String(255))
    publisher: str = Column(String(255))
    series: str = Column(String(255))
    still_photo: str = Column(Text)
    status: str = Column(String(20), nullable=False, default='UN_SUBSCRIBE')  # UN_SUBSCRIBE SUBSCRIBE COMPLETE
    mode: str = Column(String(20), nullable=False, default='STRICT')  # STRICT PRELOAD
    filter: str = Column(Text)
    star: bool = Column(Boolean)
    create_time: str = Column(String, default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    update_time: str = Column(String, onupdate=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def __init__(self, data: Dict):
        dict_trans_obj(data, self)


def save_code(session: Session, code: Code):
    if not session.get(Code,code.code):
        session.add(code)


def get_by_code(session: Session, code: str) -> Code:
    return session.get(Code,code)
