from datetime import datetime
from typing import Dict

from sqlalchemy import Column, String

from app.database.base import Base, DBBase
from app.utils import dict_trans_obj


class Actor(Base, DBBase):
    __tablename__ = 'actor'
    name: str = Column(String(20), primary_key=True, nullable=False)
    photo: str = Column(String(255))
    limit_date: str = Column(String(12))
    create_time: str = Column(String, default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    update_time: str = Column(String, onupdate=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def __init__(self, data: Dict):
        dict_trans_obj(data, self)

