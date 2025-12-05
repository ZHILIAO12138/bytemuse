import hashlib

from sqlalchemy.orm import Session
from app.api.endpoints import create_jwt_token
from app.schemas.reponse import ResponseEntity
from app.database.models import User, Cache
from app.core.config import generate_secure_random_string
from app.utils.log import logger


def login(username: str, password: str, token_key: str, session: Session) -> ResponseEntity:
    if token_key:
        cache_token = session.query(Cache).filter('forget_password' == Cache.namespace).filter(
            "token" == Cache.key).first()
        if cache_token and cache_token.content == token_key:
            user = session.query(User).filter(User.username == username).first()
            if user:
                md5_password = hashlib.md5(password.encode()).hexdigest()
                user.username = username
                user.password = md5_password
                token = create_jwt_token(username)
                user.token = token
                session.commit()
                session.close()
                return ResponseEntity(success=True, message="修改密码成功", data={'token': token})
            else:
                user = User({"username": username,
                             "password": hashlib.md5(password.encode()).hexdigest()
                             })
                token = create_jwt_token(username)
                user.token = token
                session.add(user)
                session.commit()
                return ResponseEntity(success=True, message="创建用户成功", data={'token': token})
        return ResponseEntity(success=False, message="token不正确", data="")
    else:
        user = session.query(User).filter(User.username == username).first()
        if user:
            md5_password = hashlib.md5(password.encode()).hexdigest()
            if md5_password == user.password:
                token = create_jwt_token(username)
                if token != user.token:
                    user.token = token
                    session.commit()
                    session.close()
                return ResponseEntity(success=True, message="登录成功", data={'token': token})
        return ResponseEntity(success=False, message="账号密码不正确", data="")


def update_user(username: str, password: str, session: Session) -> ResponseEntity:
    if username and password:
        user = session.query(User).first()
        user.username = username
        user.password = hashlib.md5(password.encode()).hexdigest()
        token = create_jwt_token(username)
        user.token = token
        session.commit()
        session.close()
        return ResponseEntity(success=True, message="修改成功", data={'token': token})
    return ResponseEntity(success=True, message="账号密码不能为空", data="")


def init_token(session: Session) -> ResponseEntity:
    random_str = generate_secure_random_string(32)
    cache_token = session.query(Cache).filter('forget_password' == Cache.namespace).filter(
        "token" == Cache.key).first()
    if cache_token:
        cache_token.content = random_str
        session.commit()
    else:
        cache_token = Cache({"namespace": 'forget_password', "key": "token", "content": random_str})
        session.add(cache_token)
        session.commit()
    logger.error(f"重置账号密码token: {random_str}")
    return ResponseEntity(success=True, message="token已生成,请查看后台日志", data="")
