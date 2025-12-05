from datetime import datetime
from typing import Dict

from sqlalchemy import Column, String, Integer

from app.database.base import Base, DBBase
from app.utils import dict_trans_obj


class Health(Base, DBBase):
    __tablename__ = 'health'
    id: int = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    module: str = Column(String(255))
    status: str = Column(String(255))  # healthy unhealthy none
    info: str = Column(String(255))
    time_cost: int = Column(Integer)
    create_time: str = Column(String, default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def __init__(self, data: Dict):
        dict_trans_obj(data, self)
