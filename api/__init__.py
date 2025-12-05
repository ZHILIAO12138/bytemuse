import hashlib

from fastapi import FastAPI

from app.database.models import User
from app.database.session import session_scope
from app.schduler import scheduler_thread
from app.core.config import *
from app.api.endpoints import subscribe, config, picproxy, actors, admin, message
from app.database.utils.setup import setup_database, update_database
from app.utils.log import logger

app = FastAPI(title="ByteMuse", version="1.0.0", description="")

app.include_router(subscribe.router, prefix='/api/v1', tags=["subscribe"])
app.include_router(config.router, prefix='/api/v1', tags=["core"])
app.include_router(picproxy.router, prefix='/api/v1', tags=["picproxy"])
app.include_router(actors.router, prefix='/api/v1', tags=["actors"])
app.include_router(admin.router, prefix='/api/v1', tags=["admin"])
app.include_router(message.router, prefix='/api/v1', tags=["message"])


@app.on_event("startup")
async def startup_event():
    # 构建数据库
    setup_database()
    update_database()
    #     创建目录
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
    if not os.path.exists(torrent_folder):
        os.makedirs(torrent_folder)
    if not os.path.exists(env_path):
        logger.error(f"配置文件不存在：{env_path}")
    with session_scope() as session:
        user = session.query(User).first()
        if not user:
            username = "admin"
            password = generate_secure_random_string(16)
            user = User({"username": username,
                         "password": hashlib.md5(password.encode()).hexdigest()
                         })
            session.add(user)
            session.commit()
            logger.info(f"初始账号: {username}")
            logger.info(f"初始密码: {password}")
        session.close()
    scheduler_thread.start()
    logger.warning("原始80端口已弃用,新端口为3750")
    logger.info("WEB服务已启动,请访问：http://127.0.0.1:3750")
