from sqlalchemy import text

from app.database.base import Base
from app.database.session import engine, session_scope
from app.database.utils import check_and_create_column
from app.utils.log import logger


def setup_database():
    Base.metadata.create_all(engine)


def update_database():
    with session_scope() as session:
        new_actor_script(session)
        update_code_script(session)
        check_and_create_column(session, "code", "star", "init")
        pass


def new_actor_script(session):
    sql = "PRAGMA table_info({})".format('actor')
    # 查询表的 schema
    columns = session.execute(text(sql)).fetchall()

    # 检查列是否存在
    column_exists = any(column[1] == 'code' for column in columns)
    is_not_null = any(column[1] == 'limit_date' and  column[3] for column in columns)
    if column_exists or is_not_null:
        logger.info("演员表字段不一致，进行更新")
        session.execute(text("""
         create table actor_dg_tmp
        (
            name        varchar(32) primary key not null ,
            photo       VARCHAR(255),
            limit_date  VARCHAR(12),
            create_time VARCHAR(32),
            update_time VARCHAR(32)
        )
        """))
        session.execute(text("""
                insert into actor_dg_tmp(name,photo, limit_date, create_time, update_time)
        select name,photo, limit_date, create_time, update_time
        from actor
                """))
        session.execute(text("""
                        drop table actor
                        """))
        session.execute(text("""
                        alter table actor_dg_tmp
            rename to actor
                        """))
        session.commit()
        session.flush()


def update_code_script(session):
    sql = "PRAGMA table_info({})".format('code')
    # 查询表的 schema
    columns = session.execute(text(sql)).fetchall()
    # 检查列是否存在
    column_exists = any(column[1] == 'preview_url' for column in columns)

    if not column_exists:
        logger.info("code表字段不一致，进行更新")
        session.execute(text("""
         create table code_dg_tmp
        (
            code         VARCHAR(20) PRIMARY KEY NOT NULL,
            title        VARCHAR(255),
            poster       VARCHAR(255),
            banner       VARCHAR(255),
            preview_url  VARCHAR(255),
            duration     INTEGER,
            release_date VARCHAR(12),
            genres       VARCHAR(255),
            casts        VARCHAR(255),
            producer     VARCHAR(255),
            publisher    VARCHAR(255),
            series       VARCHAR(255),
            still_photo  TEXT,
            status       VARCHAR(20) NOT NULL DEFAULT 'UN_SUBSCRIBE',
            mode         VARCHAR(20) NOT NULL DEFAULT 'STRICT',
            filter       TEXT,
            create_time  VARCHAR(32),
            update_time  VARCHAR(32)
        )
        """))
        session.execute(text("""
                insert into code_dg_tmp(code, title, poster, banner, duration, 
                    release_date, genres, casts, producer, publisher, series, still_photo, 
                    status, mode, filter, create_time, update_time)
                select code, title, poster, banner, duration, 
                    release_date, genres, casts, producer, publisher, series, still_photo, 
                    status, mode, filter, create_time, update_time
                from code
        """))
        session.execute(text("""
                        drop table code
                        """))
        session.execute(text("""
                        alter table code_dg_tmp
            rename to code
                        """))
        session.commit()
        session.flush()
