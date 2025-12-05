from datetime import datetime
from typing import Dict

from sqlalchemy import Column, String, Integer, Text

from app.database.base import Base, DBBase
from app.utils import dict_trans_obj


class Cache(Base, DBBase):
    __tablename__ = 'cache'

    id: int = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    namespace: str = Column(String(50))
    key: str = Column(String(50))
    content: str = Column(Text)
    create_time: str = Column(String, default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def __init__(self, data: Dict):
        dict_trans_obj(data, self)