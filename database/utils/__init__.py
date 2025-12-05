from sqlalchemy import text
from sqlalchemy.orm import Session


def check_and_create_column(session: Session, table_name, column_name, column_definition):
    # 连接到 SQLite 数据库
    sql = "PRAGMA table_info({})".format(table_name)
    # 查询表的 schema
    columns = session.execute(text(sql)).fetchall()

    # 检查列是否存在
    column_exists = any(column[1] == column_name for column in columns)
    if not column_exists:
        session.execute(text("ALTER TABLE {} ADD COLUMN {} {}".format(table_name, column_name, column_definition)))
    session.commit()
    session.flush()


def check_and_delete_column(session: Session, table_name, column_name):
    sql = "PRAGMA table_info({})".format(table_name)
    # 查询表的 schema
    columns = session.execute(text(sql)).fetchall()

    # 检查列是否存在
    column_exists = any(column[1] == column_name for column in columns)
    if column_exists:
        session.execute(text("ALTER TABLE {} DROP  COLUMN {}".format(table_name, column_name)))
    session.commit()
    session.flush()


def drop_primary_key(session: Session, table_name):
    session.execute(text("ALTER TABLE {} DROP PRIMARY KEY".format(table_name)))
    session.commit()
    session.flush()



def check_and_set_primary(session: Session, table_name, column_name):
    sql = "PRAGMA table_info({})".format(table_name)
    # 查询表的 schema
    columns = session.execute(text(sql)).fetchall()

    # 检查列是否存在
    column_exists = any(column[1] == column_name for column in columns)
    if column_exists:
        session.execute(text("ALTER TABLE {} ADD PRIMARY KEY ({})".format(table_name, column_name)))
    session.commit()
    session.flush()