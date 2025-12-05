from typing import Dict

from sqlalchemy import Column, String

from app.database.base import Base, DBBase
from app.utils import dict_trans_obj


class User(Base, DBBase):
    __tablename__ = 'user'

    username: str = Column(String(32), nullable=False, primary_key=True)
    password: str = Column(String(255), nullable=False)
    token: str = Column(String(255))

    def __init__(self, data: Dict):
        dict_trans_obj(data, self)
