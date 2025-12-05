from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, QueuePool
from sqlalchemy.orm import sessionmaker, scoped_session

from app.core.config import DATABASE_PATH

# 数据库连接 URL
DATABASE_URL = DATABASE_PATH

# 创建数据库引擎
engine = create_engine(DATABASE_URL,
                       pool_pre_ping=True,
                       echo=False,
                       poolclass=QueuePool,
                       pool_size=1024,
                       pool_recycle=3600,
                       pool_timeout=180,
                       max_overflow=10,
                       connect_args={"timeout": 60})

# 创建会话工厂
SessionFactory = sessionmaker(bind=engine, autocommit=False, autoflush=True)
Session = scoped_session(SessionFactory)


def get_session() -> Generator:
    session = None
    try:
        session = Session()
        yield session
    finally:
        if session:
            session.close()


@contextmanager
def session_scope() -> Generator:
    """提供一个事务范围的上下文管理器"""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
