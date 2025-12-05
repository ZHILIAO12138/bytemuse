from datetime import datetime
from typing import Dict

from sqlalchemy import Column, String

from app.database.base import Base, DBBase
from app.utils import dict_trans_obj


class History(Base, DBBase):
    __tablename__ = 'history'
    hash: str = Column(String(255), primary_key=True, nullable=False)
    save_path: str = Column(String(255))
    code: str = Column(String(20))
    create_time: str = Column(String, default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def __init__(self, data: Dict):
        dict_trans_obj(data, self)
